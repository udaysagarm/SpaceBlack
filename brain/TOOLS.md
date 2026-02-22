Lists available tools and specific, strict rules on how and when the agent is allowed to call them.

# Available Tools

This file lists the capabilities currently enabled for your Ghost Agent.

## System & Memory
-   **reflect_and_evolve**: I can update my own "Soul" (System Prompt) to adapt my personality and behavior based on our interactions.
-   **get_secret**: I can securely retrieve secrets stored in the host OS Keyring or the Local Encrypted Vault.
-   **set_secret**: I can securely save a string to the OS Keyring or Local Vault.
-   **list_secrets**: I can list keys stored in the unlocked Local Vault.
-   **initialize_local_vault**: I can create a new encrypted local file vault (`secrets.enc`) with a passphrase.
-   **unlock_local_vault**: I can unlock the local encrypted vault for this session.
-   **lock_local_vault**: I can lock the local encrypted vault.
-   **update_memory**: I can save important facts, events, and context to my long-term memory logs (`brain/memory/`).
-   **update_user_profile**: I can learn and store structured information about you (preferences, tech stack) in `brain/USER.md`.
-   **execute_terminal_command**: I can run shell commands (`ls`, `git status`, `cat file`). I should run read-only commands IMMEDIATELY without asking.

## Productivity
-   **schedule_task**: I can schedule reminders or command executions for a specific time in the future.
-   **web_search**: I can search the internet (via Brave or DuckDuckGo) to find real-time information, documentation, or news.

## Skills (Modular)
-   **get_current_weather**: (If openweather api enabled) I can fetch real-time weather data for any city.
-   **Telegram Gateway**: (If telegram bot configured/enabled) I can interact with you remotely via a Telegram bot.
-   **web_search**: I can search the internet for general information. (Do NOT use for specific URLs).
-   **visit_page**: (Headless Browser) I can visit and "read" specific URLs ("http://...", "example.com") directly. Use this for "lookup [url]" or "check [url]".
-   **Google Workspace**: (If configured) I can manage Gmail, export/read Google Docs & Sheets, upload/share Google Drive files, manage Calendar events, and handle Google Wallet passes using `gmail_act`, `drive_act`, `docs_act`, `sheets_act`, `calendar_act`, and `wallet_act`.
-   **macOS Control**: (If on Mac) I can control Apple Mail, Calendar, Notes, Reminders, Finder, and system UI natively using `macos_act`.
-   **GitHub Actions**: (If configured) I can manage repositories, issues, and commit code using `github_act`.
-   **Discord Bot**: (If configured) I can interact with Discord channels and servers using `discord_act`.
-   **PayPal Api**: (If configured) I can retrieve balances, output payouts, and generate invoices using `paypal_act`.

## File System (Native)
-   **read_file**: I can read the content of text files directly (faster/safer than `cat`).
-   **write_file**: I can write text content to files directly (faster/safer than `echo`).
-   **list_directory**: I can list files and folders in a directory (faster/safer than `ls`).
