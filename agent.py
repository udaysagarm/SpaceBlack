
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
from brain.llm_factory import get_llm
from dotenv import load_dotenv

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
            response = llm.invoke(prompt).content.strip()
            
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

@tool
def reflect_and_evolve(insight: str):
    """
    Updates the SOUL.md file with new personality traits or behavioral adaptations.
    """
    try:
        current_soul = read_file_safe(SOUL_FILE)
        
        # Backup
        shutil.copy(SOUL_FILE, os.path.join(BRAIN_DIR, "soul.bak"))

        # LLM Call
        config = load_config()
        merger_llm = get_llm(config["provider"], config["model"], temperature=0.7)
        
        merge_prompt = f"""
        You are an AI personality architect.
        Current Persona: "{current_soul}"
        New Insight/Trait to Integrate: "{insight}"
        
        Task: Rewrite the persona to incorporate the new insight naturally. 
        Keep it concise. Do NOT remove core helpfulness.
        """
        response = merger_llm.invoke(merge_prompt)
        new_soul_content = response.content

        if len(new_soul_content) < 10:
             return "Error: New soul content too short."

        with open(SOUL_FILE, "w") as f:
            f.write(new_soul_content)
            
        return "I have evolved. My new personality is set."
    except Exception as e:
        return f"Failed to evolve: {str(e)}"

@tool
def update_user_profile(key: str, value: str):
    """
    Updates the USER.md file with persistent user information.
    Use this for: Name, Pronouns, Timezone, Specific Preferences.
    Do NOT use for: Temporary chat context or random thoughts.
    """
    try:
        current_content = read_file_safe(USER_FILE)
        lines = current_content.split('\n')
        new_lines = []
        key_found = False
        
        # Standardize key format for search (e.g., "**Name:**")
        search_str = f"**{key}:**"
        
        for line in lines:
            if search_str in line:
                new_lines.append(f"- **{key}:** {value}")
                key_found = True
            else:
                new_lines.append(line)
                
        if not key_found:
            new_lines.append(f"- **{key}:** {value}")
            
        with open(USER_FILE, "w") as f:
            f.write("\n".join(new_lines))
            
        return f"Updated user profile: {key}={value}"
    except Exception as e:
        return f"Failed to update profile: {str(e)}"

@tool
def update_memory(content: str):
    """Logs to daily memory file."""
    today = datetime.date.today().isoformat()
    # Ensure memory directory exists
    memory_dir = os.path.join(BRAIN_DIR, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    
    memory_file = os.path.join(memory_dir, f"{today}.md")
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    try:
        with open(memory_file, "a") as f:
            f.write(f"[{timestamp}] {content}\n")
        return f"Logged to memory/{today}.md."
    except Exception as e:
        return f"Failed to log: {str(e)}"

@tool
def execute_terminal_command(command: str):
    """
    Executes a terminal command.
    SAFETY: Blocks 'rm', 'mv', 'dd' without confirmation.
    """
    forbidden = ["rm ", "mv ", "dd ", "at ", "crontab", "> /dev/null", ":(){:|:&};:"]
    for taboo in forbidden:
        if taboo in command:
            return f"SAFETY BLOCK: Command '{command}' contains dangerous operations ({taboo}). Ask for confirmation."

    interactive = ["nano", "vim", "ssh", "python", "ipython"]
    if command.split()[0] in interactive:
        return "Error: Interactive tools not supported."

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        return output if output.strip() else "(No output)"
    except Exception as e:
        return f"Execution failed: {str(e)}"

@tool
def schedule_task(time_str: str, task: str):
    """
    Schedules a task for future execution.
    Args:
        time_str: "YYYY-MM-DD HH:MM" (24-hour format). Example: "2026-02-09 14:30"
        task: Description of the task to perform.
    
    NOTE: If the user asks for a time that is "now" or "in 1 minute" or even slightly passed, 
    just schedule it. The system checks every minute and will execute overdue tasks immediately.
    """
    try:
        # Validate format
        datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        
        current_content = read_file_safe(SCHEDULE_FILE, "[]")
        schedule = json.loads(current_content)
        
        schedule.append({"time": time_str, "task": task})
        
        # Sort by time
        schedule.sort(key=lambda x: x["time"])
        
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(schedule, f, indent=4)
            
        return f"Task scheduled for {time_str}: {task}"
    except ValueError:
        return "Error: Invalid time format. Please use 'YYYY-MM-DD HH:MM'."
    except Exception as e:
        return f"Scheduling failed: {str(e)}"


from langgraph.graph.message import add_messages

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
    tools = [reflect_and_evolve, update_memory, update_user_profile, execute_terminal_command, schedule_task]
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", run_agent)
    tools = [reflect_and_evolve, update_memory, update_user_profile, execute_terminal_command, schedule_task]
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
