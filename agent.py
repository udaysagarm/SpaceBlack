
import os
import shutil
import subprocess
import datetime
import json
import time
from typing import TypedDict, Annotated, List, Union
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_community.tools import BraveSearch, DuckDuckGoSearchRun
from brain.llm_factory import get_llm
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Constants
BRAIN_DIR = "brain"
CONFIG_FILE = "config.json"
ENV_FILE = ".env"
AGENTS_FILE = os.path.join(BRAIN_DIR, "AGENTS.md")
IDENTITY_FILE = os.path.join(BRAIN_DIR, "IDENTITY.md")
SOUL_FILE = os.path.join(BRAIN_DIR, "SOUL.md")
USER_FILE = os.path.join(BRAIN_DIR, "USER.md")

# ... (existing imports)
from brain.memory_manager import (
    ensure_brain_initialized, 
    read_file_safe,
    build_system_prompt,
    BRAIN_DIR,
    SOUL_FILE,
    HEARTBEAT_FILE,
    HEARTBEAT_STATE_FILE,
    SCHEDULE_FILE,
    IDENTITY_FILE,
    load_config
)

# ... (existing constants)
HEARTBEAT_STATE_FILE = os.path.join(BRAIN_DIR, "memory", "heartbeat-state.json")

# ... (existing functions: load_config, read_file_safe, build_system_prompt)

def run_autonomous_heartbeat(force: bool = False) -> Union[str, None]:
    """
    Checks if a heartbeat is needed. If so, runs background tasks.
    Also checks schedule for due tasks.
    """
    # 1. Check Schedule (Every run)
    schedule_notifications = []
    try:
        schedule_content = read_file_safe(SCHEDULE_FILE, "[]")
        schedule = json.loads(schedule_content)
        
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        matches = []
        remaining = []
        
        for item in schedule:
            if item["time"] <= current_time_str:
                matches.append(item)
            else:
                remaining.append(item)
                
        if matches:
            # We have due tasks!
            # Propagate specific notifications
            for task in matches:
                schedule_notifications.append(f"⏰ **Scheduled Task Due**: {task['task']} (Time: {task['time']})")
            
            # Save updated schedule (removing executed tasks)
            with open(SCHEDULE_FILE, "w") as f:
                json.dump(remaining, f, indent=4)
    except Exception as e:
        schedule_notifications.append(f"Scheduler Error: {e}")

    # 2. Check Autonomous Interval (Every 3 hours)
    last_run = 0
    if os.path.exists(HEARTBEAT_STATE_FILE):
        try:
            with open(HEARTBEAT_STATE_FILE, "r") as f:
                data = json.load(f)
                last_run = data.get("last_run", 0) or 0
        except: pass
    
    now = time.time()
    heartbeat_msg = None
    
    # 3 hours = 10800 seconds
    if force or (now - last_run >= 10800):
        # Run standard heartbeat check
        try:
            heartbeat_instructions = read_file_safe(HEARTBEAT_FILE, "Report status.")
            identity = read_file_safe(IDENTITY_FILE)
            
            prompt = f"""
            [SYSTEM WAKEUP - AUTONOMOUS HEARTBEAT]
            You are {identity}.
            You have just woken up for a scheduled background check.
            
            [INSTRUCTIONS]
            {heartbeat_instructions}
            
            [TASK]
            Perform the check. 
            - If everything is normal and no action is needed, reply with 'Status: OK'.
            - If there is something the user needs to know (e.g. system alert, suggestion), write a short message.
            """
            
            config = load_config()
            llm = get_llm(config["provider"], config["model"], temperature=0.3)
            res = llm.invoke(prompt)
            # Handle list return from invoke (rare but possible)
            if isinstance(res, list):
                res = res[0]
            
            content = res.content
            if isinstance(content, list): content = " ".join([str(p) for p in content])
            response = content.strip()
            
            with open(HEARTBEAT_STATE_FILE, "w") as f:
                json.dump({"last_run": now, "status": "ok"}, f)
                
            if "Status: OK" not in response:
                heartbeat_msg = response
        except Exception as e:
            heartbeat_msg = f"Heartbeat Error: {str(e)}"

    # Combine results
    results = []
    if schedule_notifications:
        results.extend(schedule_notifications)
    if heartbeat_msg:
        results.append(heartbeat_msg)
        
    if results:
        return "\n\n".join(results)
    return None

# --- Tools ---
# Tools are imported from tools/ module
from langgraph.graph.message import add_messages
from tools.system import reflect_and_evolve, update_memory, update_user_profile, execute_terminal_command
from tools.scheduler import schedule_task
from tools.search import web_search




# --- Graph ---

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def run_agent(state: AgentState):
    system_prompt = build_system_prompt()
    chat_history = list(state["messages"])
    
    # Sanitization: Ensure AIMessages with tool calls have content (fix for google-genai SDK)
    for msg in chat_history:
        if isinstance(msg, AIMessage) and msg.tool_calls and not msg.content:
            msg.content = " "
            
    # Robust Fix: Merge system prompt into the first HumanMessage
    # This avoids "contents required" errors and order issues with Gemini 2.0
    if chat_history and isinstance(chat_history[0], HumanMessage):
        chat_history[0] = HumanMessage(content=system_prompt + "\n\n" + str(chat_history[0].content))
    else:
        # Fallback if first message isn't Human
        chat_history = [HumanMessage(content=system_prompt)] + chat_history
    
    messages = chat_history
    
    config = load_config()
    llm = get_llm(config["provider"], config["model"], temperature=0)

    tools = [reflect_and_evolve, update_memory, update_user_profile, execute_terminal_command, schedule_task, web_search]
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", run_agent)
    tools = [reflect_and_evolve, update_memory, update_user_profile, execute_terminal_command, schedule_task, web_search]
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    
    def should_continue(state: AgentState):
        if state["messages"][-1].tool_calls: return "tools"
        return END
        
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    return workflow.compile()

app = build_graph()
