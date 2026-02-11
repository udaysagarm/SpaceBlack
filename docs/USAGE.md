# User Manual

## Interface Overview
The interface is split into three main areas:
1.  **Sidebar (Left)**: Your "Soul" & Identity. Shows who the agent currently thinks it is.
2.  **Chat Area (Center)**: The main conversation history.
3.  **Input Bar (Bottom)**: Where you type commands.

## Core Commands

### Chat
Just type naturally!
-   *"Summarize the README file in this folder."*
-   *"Write a Python script to scrape a website."*
-   *"Who won the Super Bowl last year?"* (Uses Web Search)

### Configuration (`/config`)
Type `/config` in the input bar to open the **Settings Menu**.
-   **AI Provider**: Switch between Google (Gemini), OpenAI (GPT-4), or Anthropic (Claude).
-   **Model Name**: Manually override the model (e.g., `gemini-2.0-flash`, `gpt-4o-mini`).
-   **Web Search**: Toggle between Brave (API key required) and DuckDuckGo (Free).
-   **API Keys**: Update your keys securely without editing files.

### Task Scheduling
You can tell the agent to do things in the future.
-   *"Remind me to check the logs in 10 minutes."*
-   *"Create a backup of this file at 5:00 PM."*
-   *Status*: The agent checks every minute for due tasks.

### Web Search
The agent automatically decides when to search the web.
-   Explicit trigger: *"Search for latest react router documentation."*
-   Implicit trigger: *"What is the current stock price of Apple?"*

## Customization

### The "Brain"
The agent's memory and personality are stored in the `brain/` folder. You can edit these (carefully!):
-   `brain/SOUL.md`: The agent's personality. Edit this to change its vibe.
-   `brain/USER.md`: Your profile. The agent learns about you here.
-   `brain/AGENTS.md`: The "Constitution" and core rules.


### Reset
To reset the agent's memory of today, simply delete the file in `brain/memory/YYYY-MM-DD.md`.

## Collaboration & Sharing

### How to Share Code
If you want to share this project with others (e.g., via GitHub), you don't need to worry about your personal data or environment files. The project is configured to **ignore** them automatically:
-   `.venv/`: Your local Python environment (too big, machine-specific).
-   `.env`: Your API keys.
-   `brain/USER.md`: Your personal details.
-   `brain/memory/`: Your chat logs.

### Setting Up on a New Machine
When someone clones your code, they will need to set it up. 

**Option A: The Easy Way (Professional)**
1.  **First Time Setup (Run Once)**:
    ```bash
    ./spaceblack onboard
    ```
2.  **Daily Usage (Run Anytime)**:
    ```bash
    ./spaceblack start
    ```
    *(On Windows, just type `spaceblack onboard` or `spaceblack start` without the `./`)*

**Option B: The Manual Way**
1.  **Create Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Mac/Linux
    # .venv\Scripts\activate   # Windows
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run**:
    ```bash
    python main.py
    ```

The agent will automatically create a fresh `USER.md` for them!

