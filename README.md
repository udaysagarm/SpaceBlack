# Space Black (Ghost Agent)

**Space Black** is a self-evolving, terminal-based AI agent designed to live in your shell. It allows you to interact with LLMs (Gemini, OpenAI, Anthropic) directly from your terminal with persistent memory, autonomous scheduling, and web access.

![Terminal UI](https://textual.textualize.io/assets/images/gallery/code_browser.png)

## Features

-   **Persistent Memory**: Remembers your preferences, identity, and past contexts in `brain/USER.md` and `brain/memory/`.
-   **Personality Engine**: Developing a unique persona stored in `brain/SOUL.md` that evolves over time based on interactions.
-   **Task Scheduler**: Schedule commands and reminders. The agent executes them automatically in the background.
-   **Web Access**: Real-time internet search using Brave Search or DuckDuckGo to fetch current events.
-   **Headless Browser**: Can read dynamic websites (React/Vue/Angular) using a built-in Chromium engine.
-   **Terminal UI (TUI)**: Built with Textual for a responsive CLI experience.
-   **Modular Skills**: Extensible system for integrations like OpenWeather and Telegram. (Requires restart to enable/disable)
-   **Multi-Provider**: Switch between Google Gemini, OpenAI, and Anthropic models dynamically.
-   **Privacy-First**: All memory and configuration files are stored locally. Sensitive data is excluded from Git.

## Quick Start
1.  **Clone**: `git clone https://github.com/udaysagar/SpaceBlack.git`
2.  **Setup**: `./spaceblack onboard` (Installs Python dependencies + Browser binaries automatically)
3.  **Run**: `./spaceblack start`

The application will automatically detect missing configurations and launch a setup wizard to guide you through the process.

## Documentation
For detailed guides, please refer to the `docs/` directory:

-   [**Installation Guide**](docs/INSTALLATION.md)
-   [**User Manual**](docs/USAGE.md)
-   [**Core Tools**](docs/TOOLS.md)
-   [**Modular Skills**](docs/SKILLS.md)
-   [**Memory System**](docs/MEMORY.md)
-   [**Security & Privacy**](docs/SECURITY.md)
-   [**Architecture**](docs/ARCHITECTURE.md)

## License
MIT License. See LICENSE for details.
