# User Manual

## Interface Overview
The interface is designed for efficiency and is split into three main areas:
1.  **Sidebar (Left)**: Displays the current identity ("Soul") of the agent.
2.  **Chat Area (Center)**: The main conversation history log.
3.  **Input Bar (Bottom)**: The command line interface for user input.

## Core Commands

### Chat Interaction
Simply type your request in natural language.
-   "Summarize the README file in this directory."
-   "Write a Python script to scrape a website."
-   "Who won the Super Bowl last year?" (Triggers Web Search)

### Configuration (`/config`)
Type `/config` in the input bar to open the **Settings Menu**.
-   **AI Provider**: Switch between Google (Gemini), OpenAI (GPT-4), or Anthropic (Claude).
-   **Model Name**: Manually override the model (e.g., `gemini-2.0-flash`, `gpt-4o-mini`).
-   **Web Search**: Toggle between Brave (API key required) and DuckDuckGo (Free).
-   **API Keys**: Update your keys securely without editing configuration files manually.

### Skills Manager (`/skills`)
Type `/skills` to open the **Skills Manager**. This interface manages modular extensions.
-   **OpenWeather**: Enable real-time weather data.
-   **Telegram Bot**: Configure the Telegram Gateway for remote access.
    -   Enter your **Bot Token** and **Allowed User ID**.
    -   Toggle the service to **ON**.
    -   Execute the bot script: `python tools/skills/telegram/bot.py`.

### Task Scheduling
You can instruct the agent to perform actions in the future.
-   "Remind me to check the logs in 10 minutes."
-   "Create a backup of this file at 17:00."

**Status**: The agent checks the schedule every minute for due tasks.

### Web Search
The agent autonomously decides when to search the web based on your prompt.
-   **Explicit trigger**: "Search for latest React documentation."
-   **Implicit trigger**: "What is the current stock price of Apple?"

## Data management

### The "Brain"
The agent's memory and personality are stored in the `brain/` directory. While you can edit these files, do so with caution.
-   `brain/SOUL.md`: Defines the agent's personality.
-   `brain/USER.md`: Stores your user profile and preferences.
-   `brain/AGENTS.md`: Contains the system constitution and core rules.

### Reset Context
To reset the agent's memory for the current day, delete the corresponding log file in `brain/memory/YYYY-MM-DD.md`.

## Collaboration

### Sharing Code
This project is configured to exclude sensitive data from version control. You can safely push the code to a public repository without leaking:
-   `.venv/`: Local Python environment.
-   `.env`: API keys.
-   `brain/USER.md`: Personal details.
-   `brain/memory/`: Chat history.

### Setting Up on a New Machine
When a new user clones the repository, running `./spaceblack onboard` (or `spaceblack onboard` on Windows) will trigger the **Setup Wizard**, which will generate a fresh `USER.md` and guide them through configuring their own API keys.
