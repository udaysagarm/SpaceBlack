# Architecture & Technology Stack

Space Black is designed as a **Local-First, Terminal-Native Agent**. It operates entirely on the host machine, ensuring data privacy and a responsive workflow.

## Technology Stack

### Frontend (TUI)
-   **Textual**: A Python framework for creating sophisticated TUI applications. It provides CSS-like styling, widgets, and event handling within the terminal.
-   **AsyncIO**: The UI is fully asynchronous, preventing the interface from freezing during computation.

### Backend (AI Logic)
-   **LangGraph**: Manages the agent's state machine (cyclic graph). This allows for complex workflows (e.g., "Thought -> Tool Call -> Result -> Thought").
-   **LangChain**: Provides the standardized interface for different LLM providers (Google, OpenAI, Anthropic).
-   **Tools**: Custom Python functions decorated with `@tool` that the LLM can invoke (File I/O, Web Search, System Commands).

### Memory System
Space Black uses **Markdown Files** as its database. This design choice prioritizes transparency and portability.
-   **Transparency**: Users can read and edit the agent's memory with any text editor.
-   **Portability**: Easy to sync via Git or Dropbox.

#### Core Files
-   `brain/memory/YYYY-MM-DD.md`: Daily logs. The agent writes thoughts and actions here.
-   `brain/SOUL.md`: The "System Prompt" that defines the persona.
-   `brain/USER.md`: Structured facts about the user.

## Design Philosophy
1.  **Unix Philosophy**: Operates in the shell, works with text streams, and respects standard IO.
2.  **Cross-Platform**: Uses `platform` detection to adapt commands for Windows (PowerShell) vs. Mac/Linux (Bash).
3.  **Privacy**: No telemetry. Keys live in `.env`. Memory lives in `brain/`.

## Directory Structure
```
.
├── main.py              # Application Entry Point
├── tui.py               # Textual UI Implementation
├── agent.py             # LangGraph State Machine
├── tools/               # Agent Capabilities
│   ├── skills/          # Modular Integrations (Telegram, Weather)
│   └── ...              # Core Tools (Search, System)
├── brain/               # Persistent Storage
│   ├── memory/          # Daily Logs
│   ├── SOUL.md          # Personality Definition
│   └── AGENTS.md        # System Directives
└── docs/                # Documentation
```
