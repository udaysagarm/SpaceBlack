# Core Tools

**Space Black** provides these tools to **Ghost** (the agent). Ghost uses them autonomously to complete your requests.

### 🔐 Vault (Secure Storage)
Manage sensitive credentials, user specifics, and background data securely. The Vault prioritizes the host OS Native Password Storage system (macOS Keychain, Windows Credential Manager, Linux Secret Service), with an additional Local Encrypted File Vault (`secrets.enc`) as a fallback.

*   `initialize_local_vault(passphrase)`: Create a new encrypted local vault with a secret phrase.
*   `unlock_local_vault(passphrase)`: Unlock the encrypted local vault for the current session.
*   `lock_local_vault()`: Lock the encrypted local vault, clearing decryption keys from memory.
*   `get_secret(key)`: Retrieve a securely stored string, checking OS Keyring first, then the local vault.
*   `set_secret(key, value, store_in_local_vault=False)`: Save a string securely to the OS Keyring (default) or Local Vault.
*   `list_secrets()`: See what keys are currently stored in the unlocked Local Vault (OS Keyring keys are hidden by default for security).

### 🌐 Autonomous Web Browsing
Space Black gives Ghost a full headless browser to interact with the web.
*   `browser_go_to(url)`: Navigate to a URL.
*   `browser_click(selector)`: Click elements (buttons, links).
*   `browser_type(selector, text)`: Type into forms.
*   `browser_scroll(direction, amount)`: Scroll the page.
*   `browser_get_state()`: Get the Accessibility Tree (Ghost's "vision").
*   `browser_screenshot()`: Save a snapshot.

**See [BROWSING.md](./BROWSING.md) for the full guide on Browsing capabilities.**

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

## Scheduler Tools (Cron Jobs)
Space Black runs a background daemon that constantly checks for due tasks.

### `schedule_task`
Adds a task to the execution queue (acts as a cron job or scheduled reminder).
-   **Usage**: Can define absolute times (`2026-10-10 14:00`) or relative recurrences (`daily`, `1h`, `30m`). When the task executes, the Daemon routes it to Ghost natively.
-   **Storage**: Updates `brain/SCHEDULE.json`.

### `cancel_task`
Removes a pending task from the queue.
-   **Usage**: Passing the exact task summary or ID to stop a recurring background job.

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
*   `wallet_act(action, ...)`: Create and manage Google Wallet passes (classes and objects).

### macOS Native Control
When running on macOS (with the skill enabled), Ghost can control local applications via AppleScript using a single endpoint:
*   `macos_act(action, ...)`: Controls Apple Mail, Calendar, Notes, Reminders, Finder, and System state. Handle operations locally without web APIs.

### Developer & Service APIs
*   `github_act(action, ...)`: Direct control over GitHub via API. Can read repos, manage issues, create branches, and directly manipulate code files.
*   `stripe_act(action, ...)`: Secure gateway to the Stripe API. Check accounts, list invoices, manage customers, and generate checkout sessions.
*   `paypal_act(action, ...)`: Access the PayPal Developer API to check balances, securely send payouts (with explicit console confirmation required), and draft invoices.
*   `discord_act(action, ...)`: Background Discord bot controller. Can send messages, list guild members, read channels, and manage DMs.
*   `slack_act(action, ...)`: Background Socket Mode Slack bot. Send DM/Channel messages, read histories, and react to threads.
*   `get_current_weather(location)`: Fetches real-time weather from OpenWeather.
*   `send_telegram_message(message)`: Broadcasts a message to the user via the Telegram Gateway.
