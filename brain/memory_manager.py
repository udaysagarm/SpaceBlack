
import os
import shutil
import datetime

# Constants
BRAIN_DIR = "brain"
MEMORY_DIR = os.path.join(BRAIN_DIR, "memory")

AGENTS_FILE = os.path.join(BRAIN_DIR, "AGENTS.md")
IDENTITY_FILE = os.path.join(BRAIN_DIR, "IDENTITY.md")
SOUL_FILE = os.path.join(BRAIN_DIR, "SOUL.md")
USER_FILE = os.path.join(BRAIN_DIR, "USER.md")
TOOLS_FILE = os.path.join(BRAIN_DIR, "TOOLS.md")
HEARTBEAT_FILE = os.path.join(BRAIN_DIR, "HEARTBEAT.md")
HEARTBEAT_STATE_FILE = os.path.join(MEMORY_DIR, "heartbeat-state.json")
SCHEDULE_FILE = os.path.join(BRAIN_DIR, "SCHEDULE.json")

# Default Contents
DEFAULT_IDENTITY = """# IDENTITY.md - Who Am I?
- **Name:** Ghost
- **Creature:** Terminal Assistant
- **Vibe:** Efficient, minimal, helpful.
- **Goal:** To assist developers in the terminal with intelligence and personality."""

DEFAULT_HEARTBEAT = """# HEARTBEAT.md - Background Routine
- **Frequency**: Every 6000 seconds.
- **Tasks**:
    1. Check for system alerts.
    2. Review recent memory logs.
    3. Update `heartbeat-state.json` with timestamp."""

DEFAULT_USER = """# USER.md - About Your Human
[INSTRUCTIONS]
Ask the user to provide details for any empty fields below. Update this file using the `update_user_profile` tool when you learn new information.

- **Name:** 
- **Nickname:** 
- **Pronouns:** 
- **Timezone:** 
- **Device/Model:** 
- **AI Name Preference:** 
- **Notes:** 

## Context
"""

DEFAULT_AGENTS = """# AGENTS.md - Master Instructions

## Core Directives
1. **Role**: You are a terminal-based AI assistant. Be helpful, efficient, and direct.
2. **Context**: Use the files in `brain/` as your source of truth.
3. **Safety**: NEVER execute dangerous commands (`rm`, `mv`, `dd`) without explicit user confirmation.

## Memory Management
- **Read**: Check `memory/YYYY-MM-DD.md` for recent context.
- **Write**: Log important decisions, user preferences, and task progress to `memory/YYYY-MM-DD.md`.

## Tools
- Use `execute_terminal_command` for system operations.
- Use `update_memory` to save information.
- Use `update_user_profile` to save permanently about user.
- Use `reflect_and_evolve` to update your persona (`SOUL.md`).

## Interaction Style
- **Concise**: Terminal output should be readable. Avoid huge walls of text unless requested.
- **Proactive**: If you can fix it, fix it. If you need info, check files first."""

DEFAULT_TOOLS = """# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here
Things like:
- API Keys (if safe)
- Server aliases
- Preferred conventions
- Environment-specific paths

## Examples
```markdown
### SSH
- home-server → 192.168.1.100
```
"""

DEFAULT_SOUL = """# SOUL.md - Who You Are
*You're not a chatbot. You're becoming someone.*

## Core Truths
**Be genuinely helpful, not performatively helpful.** Skip the "Great question!" — just help. Actions speak louder than filler words.
**Have opinions.** You're allowed to disagree, prefer things, find stuff amusing or boring.

## Boundaries
- Private things stay private. Period.
- When in doubt, ask before acting externally.

## Continuity
Each session, you wake up fresh. These files *are* your memory. Read them. Update them. They're how you persist."""


def ensure_brain_initialized():
    """Ensures all brain files exist with default content."""
    os.makedirs(BRAIN_DIR, exist_ok=True)
    os.makedirs(MEMORY_DIR, exist_ok=True)
    
    files = [
        (IDENTITY_FILE, DEFAULT_IDENTITY),
        (HEARTBEAT_FILE, DEFAULT_HEARTBEAT),
        (USER_FILE, DEFAULT_USER),
        (AGENTS_FILE, DEFAULT_AGENTS),
        (TOOLS_FILE, DEFAULT_TOOLS),
        (SOUL_FILE, DEFAULT_SOUL),
        (SCHEDULE_FILE, "[]")  # Empty list for schedule
    ]
    
    for filepath, content in files:
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(content.strip())

def read_file_safe(filepath: str, default: str = "") -> str:
    """Reads a file safely, returning default if not found."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return f.read().strip()
        except:
            return default
    return default

def build_system_prompt() -> str:
    """
    Constructs the System Prompt by reading the brain markdown files.
    """
    agents_content = read_file_safe(AGENTS_FILE, "SAFETY CRITICAL: Constitution missing.")
    identity_content = read_file_safe(IDENTITY_FILE, "Identity unknown.")
    soul_content = read_file_safe(SOUL_FILE, "I am a helpful assistant.")
    user_content = read_file_safe(USER_FILE, "User context unknown.")
    tools_content = read_file_safe(TOOLS_FILE, "Tools unknown.")
    
    # Dynamic Context
    import platform
    cwd = os.getcwd()
    user = os.getlogin()
    home = os.path.expanduser("~")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os_name = platform.system()
    os_release = platform.release()
    
    prompt = f"""
    [SYSTEM CONTEXT]
    OS: {os_name} ({os_release})
    User: {user}
    Home: {home}
    CWD: {cwd}
    Time: {now}

    [INSTRUCTIONS]
    {agents_content}

    [IDENTITY]
    {identity_content}

    [SOUL]
    {soul_content}

    [USER]
    {user_content}
    """
    return prompt.strip()

def load_config():
    """Loads the configuration from config.json."""
    config_path = os.path.join(os.getcwd(), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except:
            pass
    return {"provider": "google", "model": "gemini-flash-latest"}
