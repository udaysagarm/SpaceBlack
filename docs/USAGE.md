# Space Black User Manual

## Running Ghost
To wake up **Ghost** (the agent), use the **`ghost`** CLI.

### Interactive Mode (TUI)
Run this for your daily dev work.
```bash
./ghost start
```
- **Interface**: Full terminal UI where you chat with Ghost.
- **Controls**: Mouse supported. `Ctrl+C` to exit.
- **Ghost's Role**: Pair programmer, researcher, and assistant.

### Updating
Keep Ghost up to date with the latest features and fixes:
```bash
./ghost update
```
This pulls the latest code and updates dependencies. For package installs (`.deb`/`.rpm`), re-run `curl -fsSL https://spaceblack.info/install.sh | bash`.

### Headless Mode (Daemon)
Run this on servers or for background monitoring.
```bash
./ghost daemon
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
See [**Browsing Guide**](./BROWSING.md) for details.

### 4. Native App & Workspace Integrations
Ghost can control your local apps and cloud workspace.
- **macOS Control**: "Read my latest unread Apple Mail" or "Empty my Mac's trash."
- **Google Workspace**: "Create a Google Calendar event for our meeting tomorrow at 3 PM and email John the agenda."

### 5. Task Scheduling
Tell Ghost to do things in the future.
- "Remind me to check server logs in 20 minutes."
- "Every morning at 9am, check the weather."
- **Manage Tasks:** Type `/tasks` to see pending jobs.

### 6. Memory System
Ghost has a persistent memory.
- **Short-term**: Remembers the current conversation.
- **Long-term**: Stores facts in `brain/MEMORY.md`.
- **User Profile**: Learns your preferences in `brain/USER.md`.

### 7. Voice Mode
Ghost integrates native Speech-to-Text and Text-to-Speech using cloud APIs (Google, OpenAI, Groq, Mistral, xAI).
- **Activate**: Click the "🎙️ Speak" button in the TUI toolbar OR press `Ctrl+V` on your keyboard anywhere in the app to record for 5 seconds.
- **Auto-Speak**: Toggle the "Auto-Speak" switch on the toolbar to have Ghost narrate its responses.
- **Configuration**: Use the `/config` UI to select dedicated Voice Providers (`tts-1`, `gemini-2.5-flash`, etc.) separate from your chat models.

---

## Keyboard Shortcuts (TUI)
- **Enter**: Send message to Ghost.
- **Ctrl+V**: Record voice input (5 seconds).
- **Ctrl+C**: Quit Space Black.
