Lists available tools and specific, strict rules on how and when the agent is allowed to call them.

# Available Tools

This file lists the capabilities currently enabled for your Ghost Agent.

## System & Memory
-   **reflect_and_evolve**: I can update my own "Soul" (System Prompt) to adapt my personality and behavior based on our interactions.
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
-   **Google Workspace**: (If configured) I can manage Gmail, export/read Google Docs & Sheets, upload/share Google Drive files, and manage Calendar events using `gmail_act`, `drive_act`, `docs_act`, `sheets_act`, and `calendar_act`.
-   **macOS Control**: (If on Mac) I can control Apple Mail, Calendar, Notes, Reminders, Finder, and system UI natively using `macos_act`.
-   **GitHub Actions**: (If configured) I can manage repositories, issues, and commit code using `github_act`.
-   **Discord Bot**: (If configured) I can interact with Discord channels and servers using `discord_act`.

## File System (Native)
-   **read_file**: I can read the content of text files directly (faster/safer than `cat`).
-   **write_file**: I can write text content to files directly (faster/safer than `echo`).
-   **list_directory**: I can list files and folders in a directory (faster/safer than `ls`).
