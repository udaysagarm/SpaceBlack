# Modular Skills

Space Black features a modular skills system that allows you to extend the agent's capabilities. Skills are managed via the `/skills` command in the TUI or by editing `config.json`.

## Telegram Bot Gateway
Enables remote interaction with your agent via Telegram.

### Configuration
-   **Bot Token**: Obtained from @BotFather on Telegram.
-   **Allowed User ID**: Your numerical Telegram User ID (get it from @userinfobot). This ensures only you can talk to your agent.

### Architecture
The bot runs as a separate process from the main TUI but shares the same "Brain" (memory files).
-   **Script**: `tools/skills/telegram/bot.py`
-   **Communication**: The bot imports the agent logic directly and invokes it for every message.

### Usage
1.  Configure credentials in `/skills`.
2.  Start the bot: `python tools/skills/telegram/bot.py`
3.  Message your bot on Telegram.

## OpenWeather
Provides real-time weather information.

### Configuration
-   **API Key**: Requires a free API key from OpenWeatherMap.

### Usage
Once enabled, the agent can automatically answer questions like "What is the weather in London?". 
-   **Tool**: `get_current_weather`
-   **Data Source**: OpenWeatherMap API (Current Weather endpoint).
