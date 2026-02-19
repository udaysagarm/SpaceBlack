# Space Black User Manual

## Running Ghost
To wake up **Ghost** (the agent), you run the **Space Black** executable.

### Interactive Mode (TUI)
Run this for your daily dev work.
```bash
./spaceblack start
```
- **Interface**: Full terminal UI where you chat with Ghost.
- **Controls**: Mouse supported. `Ctrl+C` to exit.
- **Ghost's Role**: Pair programmer, researcher, and assistant.

### Headless Mode (Daemon)
Run this on servers or for background monitoring.
```bash
./spaceblack daemon
```
- **Interface**: None (Silent).
- **Ghost's Role**: Background worker. Checks `SCHEDULE.json` every 60s.
- **Interaction**: Use Telegram to talk to Ghost while it runs in the background.

---

## Core Capabilities

### 1. Interacting with Ghost
Ghost is designed to be conversational but precise.
- "Help me debug this error in `main.py`."
- "What do you think about the project structure?"
- "Draft a new README based on the code."

### 2. Autonomous Web Browsing
Ghost can surf the web for you.
- "Go to github.com and check the trending repos."
- "Read the documentation for LangGraph and summarize the core concepts."
See [**Browsing Guide**](docs/BROWSING.md) for details.

### 3. Task Scheduling
Tell Ghost to do things in the future.
- "Remind me to check server logs in 20 minutes."
- "Every morning at 9am, check the weather."
- **Manage Tasks:** Type `/tasks` to see pending jobs.

### 4. Memory System
Ghost has a persistent memory.
- **Short-term**: Remembers the current conversation.
- **Long-term**: Stores facts in `brain/MEMORY.md`.
- **User Profile**: Learns your preferences in `brain/USER.md`.

---

## Keyboard Shortcuts (TUI)
- **Enter**: Send message to Ghost.
- **Ctrl+C**: Quit Space Black.
