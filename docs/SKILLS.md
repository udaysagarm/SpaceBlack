# Modular Skills

Space Black is extensible. You can enable/disable skills in `config.json` or via the TUI Settings (coming soon).

## 1. Telegram Gateway
Interact with your agent remotely.

- **Status**: ✅ Implemented
- **Config**:
```json
"skills": {
    "telegram": {
        "enabled": true,
        "bot_token": "YOUR_BOT_TOKEN",
        "allowed_user_id": "YOUR_TELEGRAM_ID"
    }
}
```
- **Usage**:
    1. Message your bot on Telegram.
    2. The daemon (or specific TUI instance) receives the message.
    3. The agent processes it and replies back.

## 2. Headless Browser
Read content from modern, dynamic websites (React, Vue, etc.).

- **Status**: ✅ Implemented
- **Tools**: `visit_page(url)`
- **Usage**:
    - "Go to example.com and tell me the title"
    - "Check the pricing on vercel.com"
- **Tech**: Uses Playwright to render JavaScript before reading text.

## 3. Weather
Fetch real-time weather data.

- **Status**: ✅ Implemented
- **Config**:
```json
"skills": {
    "openweather": {
        "enabled": true,
        "api_key": "YOUR_API_KEY"
    }
}
```
- **Usage**: "What's the weather in Tokyo?"

## 4. Spotify (Planned)
Control music playback.
- **Status**: 🚧 Coming Soon
