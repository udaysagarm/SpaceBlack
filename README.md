# Space Black (Infrastructure) & Ghost (Agent)

> **"Space Black is the ship. Ghost is the pilot."**

**Space Black** is a terminal-based AI infrastructure designed to host autonomous agents. It provides the **body** (CLI, file system access, browser engine, memory system) that an AI agent needs to live and work on your local machine.

**Ghost** is the default AI agent running on Space Black. It is a self-evolving, persistent personality that acts as your pair programmer, researcher, and assistant.

![Terminal UI](https://textual.textualize.io/assets/images/gallery/code_browser.png)

## What is Space Black?

Space Black is the **Operating System for Agents**. It solves the hard problems of letting LLMs run locally:
- **Massive Model Support**: Drop-down access to the absolute latest AI models (`gpt-4.5-preview`, `o1`, `gemini-2.5-flash`, `claude-3-7-sonnet`, `grok-2`, `deepseek-r1`, `llama-3.3`), encompassing OpenAI, Google, Anthropic, xAI, Groq, Mistral, and local Ollama.
- **Terminal UI**: A beautiful, responsive TUI built with Textual, featuring dynamic dropdowns to prevent typos.
- **Local Memory**: Long-term storage (`brain/`) for context, ensuring the agent "remembers" you.
- **Tool System**: Safe file I/O, command execution, and system monitoring.
- **Browser Engine**: A full Chromium-based autonomous browser wrapper.

## Who is Ghost?

Ghost is the **Agent** living inside.
- **Identity**: Defines its own personality in `brain/SOUL.md`.
- **Autonomy**: Can plan multi-step tasks (e.g., "Research this error, fix the code, run the tests").
- **Browsing**: Uses the Space Black browser to surf the live web, read documentation, and interact with sites.
- **Evolution**: Updates its own system prompt based on your feedback.

## Key Features

### 🧠 Persistent Memory
Ghost remembers. It maintains a relationship with you, storing preferences and project details in `brain/USER.md` and semantic memories in `brain/memory/`.

### 🔐 Secure Vault System
Ghost stores credentials securely prioritizing the native OS Keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service), with an additional AES-encrypted local file vault fallback, ensuring API keys and passwords are never kept in plaintext.

### 🌐 Autonomous Web Browsing
Ghost can surf the web like a human.
- **Vision**: Sees page structure (Accessibility Tree), not just HTML soup.
- **Interaction**: Clicks, types, scrolls, and navigates dynamic SPAs (React/Vue).
- **Persistence**: Maintains cookies and sessions (stays logged in).
[Read more about Browsing](docs/BROWSING.md)

### ⚡ Background Daemon
Run `ghost daemon` (or `ghost.bat daemon` on Windows) to let Ghost work tirelessly in the background. It polls `brain/HEARTBEAT.md` autonomously and executes scheduled cron jobs. Ghost can even message you proactively on Telegram or Slack when a job finishes.

### 🎙️ Native Voice Integration
Talk to Ghost naturally. Space Black integrates seamless Speech-to-Text and highly realistic Text-to-Speech directly in the TUI using cloud providers (OpenAI, Google, Groq, etc.). Fully compatible across macOS, Windows, Linux, and Raspberry Pi.

### 🛠️ Modular Skills
Extend Ghost's capabilities with skills defined in `config.json`:
- **Google Workspace**: Gmail, Calendar, Drive, Docs, and Sheets integration via local OAuth.
- **macOS Control**: Deep integration with Apple Mail, Notes, Reminders, Finder, and Calendar via native AppleScript (macOS only).
- **Discord & Slack**: Run background bots to manage servers, chat in channels, and access your personal gateway.
- **GitHub**: Control repositories, issues, branches, and code files directly.
- **Stripe & PayPal**: Secure billing, invoices, payouts, and payments gateway.
- **Telegram**: Chat with Ghost from your phone.
- **Weather**: Real-time forecasts.
- **Browser**: Full web access.

*Currently sitting at a dense ~11,750+ lines of Python and infrastructure code, constantly evolving.*

## Quick Start

### One-Line Install
```bash
curl -fsSL https://spaceblack.info/install.sh | bash
```

> Also available via GitHub:
> ```bash
> curl -fsSL https://raw.githubusercontent.com/udaysagarm/SpaceBlack/main/install.sh | bash
> ```

### Manual Install
```bash
git clone https://github.com/udaysagarm/SpaceBlack.git
cd SpaceBlack
./ghost start
```

*First run auto-installs dependencies and launches the agent.*

For all commands across macOS, Linux, Windows, and Raspberry Pi, see [**Commands**](docs/COMMANDS.md).

## Documentation

Space Black is documented extensively in the `docs/` directory:

-   [**Installation**](docs/INSTALLATION.md): All install methods (curl, source, .deb, .rpm).
-   [**Commands**](docs/COMMANDS.md): Full CLI reference for all platforms.
-   [**User Manual**](docs/USAGE.md): How to interact with Ghost.
-   [**Autonomous Browsing**](docs/BROWSING.md): Details on the browser engine.
-   [**Architecture**](docs/ARCHITECTURE.md): How Space Black works under the hood.
-   [**Tools**](docs/TOOLS.md): The toolset available to Ghost.
-   [**Packaging**](docs/PACKAGING.md): Building and distributing Linux packages.
-   [**Memory & Soul**](docs/MEMORY.md): How the agent's mind works.
-   [**Security**](docs/SECURITY.md): Privacy and data safety.

## License
MIT License.
