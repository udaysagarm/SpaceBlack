
import os
import shutil
import subprocess
import datetime
from langchain_core.tools import tool
from brain.llm_factory import get_llm
from brain.memory_manager import (
    load_config, read_file_safe, 
    BRAIN_DIR, SOUL_FILE, USER_FILE
)

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
        
        Task: Rewrite the ENTIRE `SOUL.md` file to incorporate the new insight naturally.
        
        CRITICAL RULES:
        1. Output ONLY the new file content.
        2. Do NOT add conversational filler (e.g. "Here is the new file").
        3. The file MUST start with "# SOUL.md".
        4. Keep the original structure (Core Truths, Boundaries, Vibe).
        """
        response = merger_llm.invoke(merge_prompt)
        # Handle list return from invoke
        if isinstance(response, list):
             response = response[0]
             
        new_soul_content = response.content
        if isinstance(new_soul_content, list): new_soul_content = " ".join([str(p) for p in new_soul_content])

        # Validation: content must be substantial and start with header
        if len(new_soul_content) < 100 or "# SOUL.md" not in new_soul_content:
             return f"Error: LLM returned invalid content. Evolution aborted to protect SOUL.md. Output: {new_soul_content[:50]}..."

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
        # Deduplication Logic
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                lines = f.readlines()
                # Check last 3 lines for similar content
                last_few = lines[-3:] if len(lines) >= 3 else lines
                for line in last_few:
                     # Check if content exists in line (ignoring timestamp)
                    if content in line:
                         # Return success without writing to save space
                        return f"Logged to memory/{today}.md (Duplicate skipped)."

        with open(memory_file, "a") as f:
            f.write(f"[{timestamp}] {content}\n")
            
        # Post-write cleanup (optional but good for consistency)
        from tools.memory_cleaner import clean_memory_file
        clean_memory_file(memory_file)
        
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
