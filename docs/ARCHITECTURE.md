# Architecture Reference

## Concept: Infrastructure vs. Agent
**Space Black** is the host infrastructure (Body). **Ghost** is the autonomous agent (Mind).

## Core Components

### 1. The Brain (`brain/`)
Ghost's state is strictly file-based.
- **`SOUL.md`**: System Prompt (Ghost's Personality & Instructions).
- **`MEMORY.md`**: Long-term semantic memory.
- **`USER.md`**: Profile of you (the user).
- **`SCHEDULE.json`**: Pending tasks.
- **`HEARTBEAT.md`**: Background loop instructions.
- **`chat_history.json`**: Serialized session history to maintain context without token overflow.
- **`memory/heartbeat-state.json`**: State tracking for the background daemon to ensure tasks run at correct intervals.
- **`vault/`**: Secure storage for browser sessions and secrets.

### 2. The Agent Logic (`agent.py`)
This is the "Ghost" implementation.
- Built with **LangGraph**.
- Uses a **ReAct** loop (Reason → Act → Observe).
- Dynamically loads tools from `tools/` based on `config.json`.

### 3. The Interfaces (Space Black)
a. **TUI (`tui.py`)**:
   - The visual terminal interface.
   - Connects user input to `agent.py`.

b. **Daemon (`daemon.py`)**:
   - Headless runner.
   - Executes the `run_autonomous_heartbeat()` loop.
   - Listens for remote events (Telegram).

### 4. Tool System (`tools/`)
The capabilities Space Black provides to Ghost.
- **Native Tools**: File I/O, System info.
- **Platform Integrations**: Google Workspace (OAuth2 docs, drive, mail), macOS Native Control (AppleScript).
- **Skills**: Modular integrations (Weather, Telegram).
- **Browser Engine**: The autonomous browsing capability.

### 5. Autonomous Browser Engine
Space Black provides a persistent browser environment for Ghost.
- **Vision**: **Chrome DevTools Protocol (CDP)** fetches the Accessibility Tree.
- **Action**: **Playwright** handles interactions.
- **Persistence**: Session state (cookies, local storage) saved in `brain/vault/`.
See [**BROWSING.md**](./BROWSING.md) for details.

---

## Data Flow

1. **User Input** (TUI or Telegram) → **Space Black**
2. **Space Black** passes input to **Ghost (Agent Graph)**
3. **Ghost** reads `brain/` files for context.
4. **Ghost** decides to use a Tool (e.g., Browser).
5. **Tool** executes via **Space Black Infrastructure**.
6. **Ghost** observes result and generates response.
7. **Response** sent back to User via TUI.
