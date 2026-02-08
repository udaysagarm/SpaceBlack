
import os
import shutil
import subprocess
import datetime
import json
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
CONSTITUTION_FILE = os.path.join(BRAIN_DIR, "constitution.md")
SOUL_FILE = os.path.join(BRAIN_DIR, "soul.md")
SOUL_DEFAULT_FILE = os.path.join(BRAIN_DIR, "soul_default.md")
USER_FILE = os.path.join(BRAIN_DIR, "user.md")

def load_config():
    """Loads the provider and model from config.json."""
    default_config = {"provider": "openai", "model": "gpt-4o"}
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return default_config

# --- Tools ---

@tool
def reflect_and_evolve(insight: str):
    """
    Updates the soul.md file with new personality traits or behavioral adaptations based on user feedback.
    Includes a safety check to ensure the AI doesn't brick itself.
    """
    try:
        # 1. Read existing soul
        if not os.path.exists(SOUL_FILE):
             shutil.copy(SOUL_DEFAULT_FILE, SOUL_FILE)
        
        with open(SOUL_FILE, "r") as f:
            current_soul = f.read()

        # 2. Create a backup
        shutil.copy(SOUL_FILE, os.path.join(BRAIN_DIR, "soul.bak"))

        # 3. Construct the new soul using an LLM call to merge them
        config = load_config()
        # Use a simpler/faster model or the same one. For simplicity using the configured one.
        merger_llm = get_llm(config["provider"], config["model"], temperature=0.7)
        
        merge_prompt = f"""
        You are an AI personality architect.
        Current Persona: "{current_soul}"
        New Insight/Trait to Integrate: "{insight}"
        
        Task: Rewrite the persona to incorporate the new insight naturally. 
        Keep it concise (under 200 words). 
        Do NOT remove core helpfulness unless explicitly told to be unhelpful (which is rare).
        Ensure the output is valid text.
        """
        response = merger_llm.invoke(merge_prompt)
        new_soul_content = response.content

        # Sanity Check (Simple length check for now, can be more complex)
        if len(new_soul_content) < 10:
             return "Error: New soul content too short. Aborting evolution."

        # 4. WRITE the new soul
        with open(SOUL_FILE, "w") as f:
            f.write(new_soul_content)
            
        return "I have evolved. My new personality is set."
    except Exception as e:
        return f"Failed to evolve: {str(e)}"

@tool
def update_memory(content: str):
    """
    Appends the content to the daily memory file.
    Use this to log important actions or user preferences.
    """
    today = datetime.date.today().isoformat()
    memory_file = os.path.join(BRAIN_DIR, f"memory_{today}.md")
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    try:
        with open(memory_file, "a") as f:
            f.write(f"[{timestamp}] {content}\n")
        return f"Logged to memory_{today}.md"
    except Exception as e:
        return f"Failed to log memory: {str(e)}"

@tool
def execute_terminal_command(command: str):
    """
    Executes a terminal command on the system.
    SAFETY: Does NOT allow 'rm', 'mv', 'dd', '> /dev/null' without explicit user confirmation (which handled by UI layer, but here we block it if not confirmed).
    For this agent, if a command is dangerous, return a request for confirmation instead of executing.
    """
    forbidden_substrings = ["rm ", "mv ", "dd ", "> /dev/null", ":(){:|:&};:"]
    
    # Check for dangerous commands
    for taboo in forbidden_substrings:
        if taboo in command:
            return f"SAFETY BLOCK: The command '{command}' contains dangerous operations ({taboo}). Please ask the user for explicit confirmation before re-trying."

    interactive_tools = ["nano", "vim", "ssh", "python", "ipython"]
    cmd_parts = command.split()
    if cmd_parts and cmd_parts[0] in interactive_tools:
        return "Error: Interactive command-line tools are not supported. Use non-interactive alternatives."

    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        output = result.stdout + result.stderr
        return output if output.strip() else "(Command executed with no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Execution failed: {str(e)}"


# --- Graph State ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    soul_content: str

# --- Graph Nodes ---

def load_context(state: AgentState):
    """
    Reads the Constitution, Soul, and User context from files.
    Returns the system message to be prepended.
    """
    # Load Constitution
    try:
        with open(CONSTITUTION_FILE, "r") as f:
            constitution = f.read()
    except:
        constitution = "SAFETY CRITICAL: Constitution missing."

    # Load Soul (with recovery)
    if not os.path.exists(SOUL_FILE):
        if os.path.exists(SOUL_DEFAULT_FILE):
            shutil.copy(SOUL_DEFAULT_FILE, SOUL_FILE)
        else:
             with open(SOUL_FILE, "w") as f: f.write("I am a helpful assistant.")
    
    with open(SOUL_FILE, "r") as f:
        soul = f.read()

    # Load User Context
    user_context = ""
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            user_context = f.read()
            
    system_prompt = f"""
    [CONSTITUTION - STRICT RULES (READ-ONLY)]
    {constitution}

    [CURRENT SOUL - ADAPTIVE PERSONA (READ/WRITE)]
    {soul}

    [USER CONTEXT]
    {user_context}
    
    You are an intelligent terminal agent. 
    You have tools to execute commands, update your memory, and even EVOLVE your own personality (soul) if the user gives feedback.
    Always adhere to the Constitution.
    """
    
    return {"soul_content": soul, "system_message": system_prompt}


def run_agent(state: AgentState):
    """
    The main reasoning node.
    """
    context_data = load_context(state) 
    system_msg = SystemMessage(content=context_data["system_message"])
    
    messages = [system_msg] + state["messages"]
    
    config = load_config()
    llm = get_llm(config["provider"], config["model"], temperature=0)
    
    tools = [reflect_and_evolve, update_memory, execute_terminal_command]
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# --- Graph Definition ---

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", run_agent)
    tools = [reflect_and_evolve, update_memory, execute_terminal_command]
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END
        
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

# Accessor for UI
app = build_graph()
