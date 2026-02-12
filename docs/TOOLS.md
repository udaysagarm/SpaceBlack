# Core Tools

Space Black comes equipped with a set of core tools that allow the agent to interact with the system, manage memory, and access the internet. These tools are defined in `agent.py` and the `tools/` directory.

## System Tools

### execute_terminal_command
Executes shell commands on the host machine.
-   **Security**: Restricted to non-interactive commands.
-   **input**: `command` (string) - The command to execute.

### reflect_and_evolve
Allows the agent to update its own "Soul" (System Prompt) based on new experiences or user feedback.
-   **Usage**: Invoked when the agent detects a significant change in behavior or personality requirement.
-   **Storage**: Updates `brain/SOUL.md`.

### update_memory
Writes key information to the long-term memory logs.
-   **Usage**: Storing facts, events, or context for future reference.
-   **Storage**: Appends to `brain/memory/YYYY-MM-DD.md`.

### update_user_profile
Updates the structured user profile.
-   **Usage**: Learning new facts about the user (name, preferences, tech stack).
-   **Storage**: Updates `brain/USER.md`.

## Scheduler Tools

### schedule_task
Adds a task to the execution queue for a future time.
-   **Input**: 
    -   `task`: Description of the task.
    -   `time`: Target time (HH:MM format).
-   **Storage**: Updates `brain/SCHEDULE.json`.
-   **Mechanism**: The `tui.py` event loop checks this file every minute.

## Search Tools

### web_search
Performs a real-time web search.
-   **Providers**: Brave Search (Requires API Key) or DuckDuckGo (Free).
-   **Usage**: Fetching current events, documentation, or facts not in the LLM's training data.
