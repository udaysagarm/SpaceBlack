Lists available tools and specific, strict rules on how and when the agent is allowed to call them.

# Available Tools

This file lists the capabilities currently enabled for your Ghost Agent.

## System & Memory
-   **reflect_and_evolve**: I can update my own "Soul" (System Prompt) to adapt my personality and behavior based on our interactions.
-   **update_memory**: I can save important facts, events, and context to my long-term memory logs (`brain/memory/`).
-   **update_user_profile**: I can learn and store structured information about you (preferences, tech stack) in `brain/USER.md`.
-   **execute_terminal_command**: I can run non-interactive shell commands on your machine (e.g., `ls`, `git status`, `cat file`).

## Productivity
-   **schedule_task**: I can schedule reminders or command executions for a specific time in the future.
-   **web_search**: I can search the internet (via Brave or DuckDuckGo) to find real-time information, documentation, or news.

## Skills (Modular)
-   **get_current_weather**: (If openweather api enabled) I can fetch real-time weather data for any city.
-   **Telegram Gateway**: (If telegram bot configured/enabled) I can interact with you remotely via a Telegram bot.
