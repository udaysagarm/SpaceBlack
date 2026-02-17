# Architecture Reference

## Core Components

### 1. The Brain (`brain/`)
The agent's state is strictly file-based.
- **`SOUL.md`**: System Prompt (Personality).
- **`MEMORY.md`**: Long-term semantic memory.
- **`SCHEDULE.json`**: Pending cron jobs and reminders.
- **`HEARTBEAT.md`**: Instructions for the background loop.

### 2. The Agent (`agent.py`)
- Built with **LangGraph**.
- Uses a **ReAct** loop (Reason → Act → Observe).
- Supports dynamic tool loading based on `config.json`.

### 3. The Interfaces
a. **TUI (`tui.py`)**:
   - Built with **Textual**.
   - Asynchronous UI loop.
   - Direct connection to `agent.py`.

b. **Daemon (`daemon.py`)**:
   - Headless process.
   - Runs `run_autonomous_heartbeat()` loop.
   - Monitors `SCHEDULE.json` for due tasks.
   - Listens for remote events (Telegram).

### 4. Tool System (`tools/`)
- **Native Tools**: File I/O, System info (built-in).
- **Skills**: Modular integrations (Weather, Browser, Telegram).
- **Design**: Tools are simple Python functions decorated with `@tool`.

---

## Data Flow

1. **User Input** (TUI or Telegram) → **Agent Graph**
2. **Agent** reads `brain/` files for context.
3. **Agent** decides to call a Tool or reply.
4. **Tool** executes (Web Search, File Write, etc.).
5. **Agent** generates final response.
6. **Output** sent back to User Interface.
