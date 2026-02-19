# Core Tools

Space Black comes equipped with a set of core tools that allow the agent to interact with the system, manage memory, and access the internet. These tools are defined in `agent.py` and the `tools/` directory.

### 🔐 Vault (Secure Storage)
Manage sensitive credentials (API keys, passwords) securely.
*   `get_secret(key)`: Retrieve a secret.
*   `set_secret(key, value)`: Save a secret (local only, git-ignored).
*   `list_secrets()`: See what keys are available.

### 🌐 Interactive Browser (Autonomous)
Advanced browsing with state persistence (cookies) and interaction.
*   `browser_go_to(url)`: Navigate to a URL.
*   `browser_click(selector)`: Click elements (buttons, links).
*   `browser_type(selector, text)`: Type into forms.
*   `browser_scroll(direction, amount)`: Scroll the page.
*   `browser_get_state()`: Get a text representation of the page's interactive elements.
*   `browser_screenshot()`: Save a snapshot of the current view.

### 🛠️ System Tools
Core agent capabilities.
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
    -   `recurrence`: (Optional) Interval for repeating tasks. Examples: "1m", "1h", "daily".
-   **Storage**: Updates `brain/SCHEDULE.json`.
-   **Mechanism**: The `tui.py` event loop checks this file every minute. Recurring tasks are automatically rescheduled.

## Search Tools

### web_search
-   **Usage**: "Search for 'Python best practices' online."
-   **Provider**: Brave Search or DuckDuckGo (Configurable).

## File System (Native)

The agent has direct, safe access to the local file system using Python's native libraries. This is faster and more reliable than shell commands.

### `read_file`
-   **Description**: Reads the content of a text file.
-   **Usage**: "Read `brain/SOUL.md`."
-   **Constraint**: Cannot read binary files.

### `write_file`
-   **Description**: Writes text content to a file (overwrites existing).
-   **Usage**: "Create a file named `notes.txt` with this content..."
-   **Safety**: Use with caution. Always verify path before writing.

### `list_directory`
-   **Description**: Lists files and subdirectories in a given path.
-   **Usage**: "List the files in the `brain` folder."
