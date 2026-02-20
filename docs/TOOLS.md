# Core Tools

**Space Black** provides these tools to **Ghost** (the agent). Ghost uses them autonomously to complete your requests.

### 🔐 Vault (Secure Storage)
Manage sensitive credentials (API keys, passwords) securely.
*   `get_secret(key)`: Retrieve a secret.
*   `set_secret(key, value)`: Save a secret (local only, git-ignored).
*   `list_secrets()`: See what keys are available.

### 🌐 Autonomous Web Browsing
Space Black gives Ghost a full headless browser to interact with the web.
*   `browser_go_to(url)`: Navigate to a URL.
*   `browser_click(selector)`: Click elements (buttons, links).
*   `browser_type(selector, text)`: Type into forms.
*   `browser_scroll(direction, amount)`: Scroll the page.
*   `browser_get_state()`: Get the Accessibility Tree (Ghost's "vision").
*   `browser_screenshot()`: Save a snapshot.

**See [BROWSING.md](docs/BROWSING.md) for the full guide on Browsing capabilities.**

### 🛠️ System Tools
Core capabilities for interacting with your machine.
### `execute_terminal_command`
Executes shell commands.
-   **Security**: Restricted to non-interactive commands.
-   **input**: `command` (string).

### `reflect_and_evolve`
Allows Ghost to update its own "Soul" (System Prompt).
-   **Usage**: Invoked when Ghost learns something new about how you want it to behave.
-   **Storage**: Updates `brain/SOUL.md`.

### `update_memory`
Writes to long-term memory.
-   **Usage**: Storing facts, events, or context.
-   **Storage**: `brain/memory/YYYY-MM-DD.md`.

### `update_user_profile`
Updates your user profile.
-   **Usage**: Learning about you (name, tech stack, preferences).
-   **Storage**: `brain/USER.md`.

## Scheduler Tools

### `schedule_task`
Adds a task to the execution queue.
-   **Storage**: Updates `brain/SCHEDULE.json`.
-   **Mechanism**: The Space Black daemon checks this file every minute.

## Search Tools

### `web_search`
Quick search for information.
-   **Usage**: "Search for 'Python best practices'."
-   **Difference from Browsing**: `web_search` gets a list of results. `browser_go_to` actually visits the page to read/interact.

## File System (Native)

Ghost has safe, direct access to the local file system.

### `read_file`
-   **Description**: Reads text content.
-   **Usage**: "Read `brain/SOUL.md`."

### `write_file`
-   **Description**: Writes text content (overwrites).
-   **Usage**: "Create `notes.txt`."

### `list_directory`
-   **Description**: Lists files in a folder.

## Integration Tools

### Google Workspace
When the Google skill is enabled via standard OAuth2, Ghost gains access to the following `@tool` endpoints:
*   `gmail_act(action, ...)`: Send, read, search, and manage emails.
*   `calendar_act(action, ...)`: Create, list, delete, and check calendar events.
*   `drive_act(action, ...)`: Upload, download, move, share, and list Drive files.
*   `docs_act(action, ...)`: Create, append, and read Google Docs.
*   `sheets_act(action, ...)`: Create, read, and write cell ranges to Google Sheets.

### macOS Native Control
When running on macOS (with the skill enabled), Ghost can control local applications via AppleScript using a single endpoint:
*   `macos_act(action, ...)`: Controls Apple Mail, Calendar, Notes, Reminders, Finder, and System state. Handle operations locally without web APIs.
