# Project Space Black (Ghost Agent)

**Space Black** is a self-evolving, terminal-based AI agent designed to live in your shell. It allows you to interact with LLMs (Gemini, OpenAI, Anthropic) directly from your terminal with persistent memory, autonomous scheduling, and web access.

## Features

-   **Persistent Memory**: Remembers your preferences, identity, and past contexts in `brain/USER.md` and `brain/memory/`.
-   **Personality**: Developing a unique persona ("Ghost") stored in `brain/SOUL.md` that evolves over time.
-   **Task Scheduler**: Schedule commands and reminders (e.g., "Create a file at 2:00 PM"). The agent executes them automatically.
-   **Web Access**: Real-time internet search using **Brave Search** to fetch current events and documentation.
-   **Terminal UI (TUI)**: built with [Textual](https://textual.textualize.io/) for a beautiful, responsive CLI experience.
-   **Multi-Provider**: Switch between Google Gemini, OpenAI, and Anthropic models on the fly using `/config`.
-   **Cross-Platform**: Automatically detects your OS (Windows, macOS, Linux) and adapts commands accordingly (PowerShell vs Bash).
-   **Privacy-First**: All memory and configuration files are stored locally. Sensitive data is excluded from Git.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/udaysagar/SpaceBlack.git
    cd SpaceBlack
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Configuration**:
    The app will auto-create a `.env` file on first run, or you can create it manually:
    ```bash
    GOOGLE_API_KEY=your_key_here
    OPENAI_API_KEY=your_key_here
    ANTHROPIC_API_KEY=your_key_here
    BRAVE_API_KEY=your_key_here  # Required for Web Search
    ```

## Usage

Run the agent:
```bash
python main.py
```

### Commands
-   **Chat**: Just type naturally. "What's the weather?", "Refactor this code", etc.
-   **Schedule**: "Remind me to check logs in 5 minutes" or "Create a backup folder at 16:00".
-   **Web Search**: "Search for the latest Python version."
-   **Config**: Type `/config` to open the settings menu. You can change the AI provider and model (e.g., `gemini-2.0-flash`, `gpt-4o`) instantly.
-   **Exit**: Type `exit` or `quit`.

## Architecture
-   `main.py`: Entry point. Checks environment and launches TUI.
-   `tui.py`: The Textual UI, handling user input, display, and the "Heartbeat" loop.
-   `agent.py`: LangGraph agent logic. Defines tools (`web_search`, `schedule_task`, etc.) and the state graph.
-   `brain/`: **The Core**.
    -   `AGENTS.md`: System instructions and "Constitution".
    -   `SOUL.md`: The agent's personality (evolves).
    -   `USER.md`: User profile and preferences.
    -   `memory/`: Daily logs and long-term storage.
    -   `SCHEDULE.json`: Queue for time-based tasks.

## Documentation
For detailed guides, check the `docs/` folder:
-   [**Installation Guide**](docs/INSTALLATION.md)
-   [**User Manual**](docs/USAGE.md)
-   [**Architecture & Tech Stack**](docs/ARCHITECTURE.md)

## Privacy & Safety
-   **File Safety**: The agent cannot run dangerous commands (`rm`, `mv`, `dd`) without explicit confirmation.
-   **Authentication**: Permission to use `at` or `cron` is blocked to prevent system nagging; it uses an internal Python-based scheduler instead.
