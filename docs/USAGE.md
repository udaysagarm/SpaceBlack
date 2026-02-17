# Space Black User Manual

## Running the Agent

### Interactive Mode (TUI)
Run this for your daily dev work.
```bash
./spaceblack start
```
- **Interface**: Full terminal UI with chat, task list, and memory viewer.
- **Controls**: Mouse supported. `Ctrl+C` to exit.

### Headless Mode (Daemon)
Run this on servers or for background monitoring.
```bash
./spaceblack daemon
```
- **Interface**: None (Silent).
- **Function**: Runs every 60s to check `SCHEDULE.json` and `HEARTBEAT.md`.
- **Interaction**: Use Telegram to talk to the daemon.

---

## Core Features

### 1. Task Scheduling
Tell the agent to do things in the future.
- "Remind me to check server logs in 20 minutes"
- "Every morning at 9am, check the weather"

**Manage Tasks:**
- Type `/tasks` in the TUI to see and delete scheduled jobs.

### 2. File Operations
The agent can safely read/write files in your project.
- "Create a new file called test.py"
- "Read README.md and summarize it"
- "List files in the current directory"

### 3. Memory System
- **Short-term**: Remembers the current conversation.
- **Long-term**: Stores facts in `brain/MEMORY.md`.
- **User Profile**: Stores your preferences in `brain/USER.md`.

### 4. Web Search
- "Search for the latest React release notes"
- Uses Brave Search or DuckDuckGo (configurable).

---

## Keyboard Shortcuts (TUI)
- **Enter**: Send message
- **Ctrl+C**: Quit application
