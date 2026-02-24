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

## 4. Google Workspace
Integrate deeply with Gmail, Google Calendar, Google Drive, Google Docs, and Google Sheets natively via OAuth2 consent.

- **Status**: ✅ Implemented
- **Config**: Configurable via the Terminal UI (Settings -> Skills).
```json
"skills": {
    "google": {
        "enabled": true,
        "client_id": "YOUR_OAUTH_CLIENT_ID",
        "client_secret": "YOUR_OAUTH_CLIENT_SECRET"
    }
}
```
- **Usage**:
    - "Read my latest emails."
    - "Search my Google Drive for the budget spreadsheet and read it."
    - "Draft an email to John and create a calendar event for tomorrow at 2 PM."

## 5. macOS Native Control
Access and control Apple-native applications running locally on your Mac using secure AppleScript execution.

- **Status**: ✅ Implemented (macOS only)
- **Config**: Auto-detected on macOS via the Terminal UI.
```json
"skills": {
    "macos": {
        "enabled": true
    }
}
```
- **Capabilities**:
    - **Apple Mail**: Send, read, reply to, and search emails.
    - **Apple Calendar**: Create, delete, and list events.
    - **Apple Notes**: Read, create, delete, and search local notes.
    - **Apple Reminders**: List, create, complete, and delete reminders.
    - **Finder**: Move, copy, delete, and list files.
    - **System**: Control volume, brightness, clipboard, and application states.
- **Usage**:
    - "Read my unread Apple Mail."
    - "Create an Apple Note with my grocery list."
    - "Empty my Mac's trash and set my volume to 50%."

## 6. Discord Bot
Run a background Discord bot that you can interact with, and allow Ghost to read channels, send DMs, add emojis, and manage the server.

- **Status**: ✅ Implemented
- **Config**: Configurable via the Terminal UI (Settings -> Skills).
```json
"skills": {
    "discord": {
        "enabled": true,
        "bot_token": "YOUR_DISCORD_BOT_TOKEN"
    }
}
```
- **Usage**:
    - "Summarize the last 25 messages in the general channel."
    - "Send a DM to Bob telling him the deployment is done."

## 7. GitHub Integrations
Control repositories, issues, branches, and code files directly using GitHub's developer APIs.

- **Status**: ✅ Implemented
- **Config**: Configurable via the Terminal UI (Settings -> Skills).
```json
"skills": {
    "github": {
        "enabled": true,
        "api_key": "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
    }
}
```
- **Usage**:
    - "Check if there are any open issues in `owner/repo`."
    - "Create a new branch off main and commit this typo fix to the `README.md`."

## 8. Stripe Billing
Manage customers, check balances, list prices, and create checkout sessions securely using the Stripe API.

- **Status**: ✅ Implemented
- **Config**: Configurable via the Terminal UI (Settings -> Skills). *(Note: Never share your Secret Key externally.)*
```json
"skills": {
    "stripe": {
        "enabled": true,
        "api_key": "sk_test_..."
    }
}
```
- **Usage**:
    - "Check my Stripe balance."
    - "Generate a checkout session link for the 'Premium' tier price."
    - "Create a new customer named Alice."

## 9. PayPal API (Payments & Payouts)
Manage your PayPal account by checking balances, sending payouts natively with explicit security confirmations, and generating invoices via the PayPal Developer API.

- **Status**: ✅ Implemented
- **Config**: Configurable via the Terminal UI (Settings -> Skills).
```json
"skills": {
    "paypal": {
        "enabled": true,
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_SECRET",
        "environment": "sandbox"
    }
}
```
- **Usage**:
    - "Check my PayPal balance."
    - "Create a test invoice for test@example.com."
    - "Send a $5 payout to john.doe@example.com."

## 10. Slack Bot
Deploy a Socket Mode Slack Bot that you can interact with, and allow the agent to read channels, answer questions via an Intelligent Classifier, and send DMs. Automatically secures Vault data based on channel context.

- **Status**: ✅ Implemented
- **Config**: Configurable via the Terminal UI (Settings -> Skills).
```json
"skills": {
    "slack": {
        "enabled": true,
        "bot_token": "xoxb-YOUR_BOT_TOKEN",
        "app_token": "xapp-YOUR_APP_TOKEN",
        "allowed_user_id": "U1234567"
    }
}
```
- **Usage**:
    - "Summarize the last 25 messages in the #general channel."
    - "Send a DM to Bob telling him the deployment is done."
    - "What is the status of the Jira ticket mentioned above?"

## 11. Voice Interactions
Talk to the agent using high-quality multimodal APIs from Google Gemini or OpenAI without needing heavy local models.

- **Status**: ✅ Implemented
- **Config**: Relies on the main AI provider configuration in `config.json`.
- **Usage**:
    - Click the "🎙️ Speak" button in the TUI to dictate prompts.
    - Enable the "Auto-Speak" toggle in TUI for the agent to talk back to you using native TTS endpoints.

