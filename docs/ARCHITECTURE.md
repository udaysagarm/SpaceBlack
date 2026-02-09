# Architecture & Tech Stack

Space Black is designed as a **Local-First, Terminal-Native Agent**. It runs entirely on your machine, keeping your data private and your workflow fast.

## Technology Stack

### Frontend (TUI)
-   **[Textual](https://textual.textualize.io/)**: A Python framework for creating sophisticated TUI applications. It provides CSS-like styling, widgets, and event handling within the terminal.
-   **AsyncIO**: The UI is fully asynchronous, ensuring the interface never freezes while the AI is "thinking".

### Backend (AI Logic)
-   **[LangGraph](https://langchain-ai.github.io/langgraph/)**: Manages the agent's state machine (cyclic graph). This allows for complex workflows like "Thought -> Tool Call -> Result -> Thought".
-   **[LangChain](https://www.langchain.com/)**: Provides the standardized interface for different LLM providers (Google, OpenAI, Anthropic).
-   **Tools**: Custom Python functions decorated with `@tool` that the LLM can invoke (File I/O, Web Search, System Commands).

### Memory System (The "Brain")
Unlike traditional databases, Space Black uses **Markdown Files** as its database. This is intentional:
1.  **Transparency**: You can read and edit your agent's memory with any text editor.
2.  **Portability**: Easy to sync via Git or Dropbox.

-   `brain/short_term/`: (In-memory) Active conversation context.
-   `brain/memory/YYYY-MM-DD.md`: Daily logs. The agent writes thoughts and actions here.
-   `brain/SOUL.md`: The "System Prompt" that defines the persona.
-   `brain/USER.md`: Structured facts about the user.

## Design Philosophy
1.  **Unix Philosophy**: It lives in the shell, works with text streams, and respects standard IO.
2.  **Cross-Platform**: Uses `platform` detection to adapt commands for Windows (PowerShell) vs Mac/Linux (Bash).
3.  **Privacy**: No telemetry. Keys live in `.env`. Memory lives in `brain/`.

## Directory Structure
```
.
├── main.py              # Entry point
├── tui.py               # Textual UI implementation
├── agent.py             # LangGraph State Machine
├── agent_logic.py       # Helper functions
├── brain/               # Persistent Storage
│   ├── memory/          # Daily logs
│   ├── SOUL.md          # Personality
│   └── AGENTS.md        # System Directives
└── docs/                # Documentation
```
