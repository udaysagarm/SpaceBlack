
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

def parse_recurrence(recurrence: str) -> datetime.timedelta:
    """
    Parses a recurrence string into a timedelta.
    Supports: "30s", "10m", "2h", "5d", "1w".
    Aliases: "daily" (1d), "weekly" (1w), "hourly" (1h).
    """
    recurrence = recurrence.lower().strip()
    
    # Aliases
    if recurrence == "daily": return datetime.timedelta(days=1)
    if recurrence == "weekly": return datetime.timedelta(weeks=1)
    if recurrence == "hourly": return datetime.timedelta(hours=1)
    
    # Unit parsing
    try:
        if recurrence.endswith("s"):
            return datetime.timedelta(seconds=int(recurrence[:-1]))
        if recurrence.endswith("m"):
            return datetime.timedelta(minutes=int(recurrence[:-1]))
        if recurrence.endswith("h"):
            return datetime.timedelta(hours=int(recurrence[:-1]))
        if recurrence.endswith("d"):
            return datetime.timedelta(days=int(recurrence[:-1]))
        if recurrence.endswith("w"):
            return datetime.timedelta(weeks=int(recurrence[:-1]))
    except ValueError:
        pass
        
    return None

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
            # Save updated schedule (removing executed tasks, rescheduling recurring ones)
            new_schedule = list(remaining)
            
            for task in matches:
                # notification
                recurrence = task.get("recurrence")
                if recurrence:
                    # Calculate next time
                    try:
                        fmt = "%Y-%m-%d %H:%M"
                        dt = datetime.datetime.strptime(task["time"], fmt)
                        
                        delta = parse_recurrence(recurrence)
                        if delta:
                            dt += delta
                            # Update task time
                            task["time"] = dt.strftime(fmt)
                            new_schedule.append(task)
                            schedule_notifications.append(f"⏰ **Scheduled Task Due**: {task['task']} (Rescheduled for {task['time']})")
                        else:
                            schedule_notifications.append(f"⏰ **Scheduled Task Due**: {task['task']} (Error: Invalid recurrence '{recurrence}')")
                    except Exception as e:
                        schedule_notifications.append(f"⏰ **Scheduled Task Due**: {task['task']} (Error rescheduling: {e})")
                else:
                    schedule_notifications.append(f"⏰ **Scheduled Task Due**: {task['task']} (Time: {task['time']})")

            # Sort and save
            new_schedule.sort(key=lambda x: x["time"])
            
            with open(SCHEDULE_FILE, "w") as f:
                json.dump(new_schedule, f, indent=4)
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
            - If there is something the user needs to know or an action the agent must perform, write a short, clear instruction in PLAIN TEXT.
            - DO NOT WRITE CODE. DO NOT USE MARKDOWN CODE BLOCKS.
            - Example: "Create a file named 'test.txt' with content 'hello'."
            """
            
            config = load_config()
            llm = get_llm(config["provider"], config["model"], temperature=0.3)
            res = llm.invoke(prompt)
            # Handle list return from invoke (rare but possible)
            if isinstance(res, list):
                res = res[0]
            
            content = res.content
            if isinstance(content, list):
                # Extract text from parts if it's a list of dicts
                parts = []
                for p in content:
                    if isinstance(p, dict) and "text" in p:
                        parts.append(p["text"])
                    else:
                        parts.append(str(p))
                content = " ".join(parts)
            
            response = str(content).strip()
            
            # Update state file
            with open(HEARTBEAT_STATE_FILE, "w") as f:
                json.dump({"last_run": now, "status": "ok"}, f)

            if "Status: OK" in response:
                # Remove "Status: OK" to see if there are other instructions
                cleaned_response = response.replace("Status: OK", "").strip()
                if cleaned_response:
                    heartbeat_msg = cleaned_response
            else:
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
from tools.system import (
    reflect_and_evolve, 
    update_user_profile, 
    update_memory,
    execute_terminal_command
)
from tools.scheduler import schedule_task, cancel_task
from tools.search import web_search
from tools.skills.openweather import get_current_weather
from tools.skills.openweather import get_current_weather
# OpenClaw-style unified browser tool
from tools.skills.browser.browser import browser_act
# Use Vault Tools
from tools.vault import get_secret, set_secret, list_secrets
from tools.files import read_file, write_file, list_directory
from tools.skills.telegram.send_message import send_telegram_message




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
    content = str(chat_history[0].content)
    
    # FORCE EXECUTION for Scheduled Tasks
    if "⏰ **Scheduled Task Due**" in content:
        content = f"⚠️ SYSTEM OVERRIDE: IMMEDIATELY EXECUTE THE FOLLOWING SCHEDULED TASKS. DO NOT CHAT. USE TOOLS.\n\n{content}"

    if chat_history and isinstance(chat_history[0], HumanMessage):
        chat_history[0] = HumanMessage(content=system_prompt + "\n\n" + content)
    else:
        # Fallback if first message isn't Human
        chat_history = [HumanMessage(content=system_prompt + "\n\n" + content)] + chat_history
    
    messages = chat_history
    
    config = load_config()
    llm = get_llm(config["provider"], config["model"], temperature=0)

    tools = [reflect_and_evolve, update_memory, update_user_profile, execute_terminal_command, schedule_task, cancel_task, web_search]
    
    # Dynamic Skills
    skills_config = config.get("skills", {})

    if skills_config.get("openweather", {}).get("enabled", False):
        tools.append(get_current_weather)

    if skills_config.get("browser", {}).get("enabled", False):
        # OpenClaw-style unified browser tool
        tools.append(browser_act)

    # File tools are always available
    tools.extend([read_file, write_file, list_directory])
    
    # Vault Tools (Always available for memory management)
    tools.extend([get_secret, set_secret, list_secrets])
    
    # Telegram tool
    tools.append(send_telegram_message)

    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke(messages)
    
    # GUARD: If response is effectively empty (no content, no tool calls)
    # This happens sometimes with Gemini or if the model "chokes"
    if not response.content and not response.tool_calls:
        response.content = "..."
        
    # GUARD: If response has tool calls but no content, ensure content is partially filled
    # to prevent TUI from showing blank (though TUI usually waits for final result)
    # But if this is the FINAL result (e.g. tool execution failed?), we need text.
    if not response.content and response.tool_calls:
        # We can leave it empty if we are fairly sure it proceeds to tool execution.
        # But for safety:
        response.content = " " # Space is enough to be not None
        
    return {"messages": [response]}

# Define the tools the agent can use
# We catch the SystemExit to prevent the agent from killing the whole process
@tool 
def exit_conversation():
    """
    Ends the current conversation.
    """
    return "Goodbye!"

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", run_agent)
    # Note: ToolNode must have *all* potential tools registered, OR we need to dynamically build it?
    # ToolNode documentation says it executes tools called by the LLM.
    # Providing all tools safely is fine, as the LLM won't call them if not bound.
    # However, to be strict, we can just expose all.
    tools = [
        reflect_and_evolve, update_memory, update_user_profile, execute_terminal_command, 
        schedule_task, cancel_task, web_search, get_current_weather, 
        browser_act,
        get_secret, set_secret, list_secrets,
        read_file, write_file, list_directory, 
        exit_conversation, send_telegram_message
    ]
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
