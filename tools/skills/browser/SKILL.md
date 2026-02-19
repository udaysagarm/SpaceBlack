---
name: Browser Skill
description: Autonomous web browsing using OpenClaw-style Semantic Snapshots and reference-based interaction.
---

# Browser Skill (OpenClaw-Style)

This skill gives the agent the ability to control a real Chromium browser. It uses the same architectural approach as **OpenClaw**: instead of fragile CSS selectors, every page is rendered as a **Semantic Snapshot** — a numbered list of interactive elements drawn from the browser's Accessibility Tree. The agent clicks/types by **reference number**, not by guessing selectors.

## The Single Tool: `browser_act`

Everything is done through one tool with an `action` parameter.

### Actions

| Action | What it does | Required params |
|--------|-------------|-----------------|
| `navigate` | Go to a URL | `url` |
| `click` | Click an element | `ref` (number from snapshot) |
| `type` | Type into an input field | `ref`, `text` |
| `clear_and_type` | Clear a field then type | `ref`, `text` |
| `press` | Press a keyboard key | `key` (e.g. `"Enter"`) |
| `scroll` | Scroll the page | `direction` ("up"/"down"), `amount` (px) |
| `wait` | Wait for page to settle | `duration` (seconds) |
| `snapshot` | Read current page state | — |
| `screenshot` | Save a screenshot | — |
| `back` | Browser back | — |
| `forward` | Browser forward | — |
| `close` | Close the session | — |

### Semantic Snapshot Example

After every action, the agent receives a snapshot like:

```
URL: https://mail.com
Title: Mail.com - Free Email

  ## Welcome to Mail.com
  [  1] Link: Log In
  [  2] Link: Sign Up
  [  3] Input(searchbox): 'Search...' (placeholder)

(3 interactive elements found. Use ref=N to interact.)
```

The agent then calls: `browser_act(action="click", ref=1)` — no CSS needed.

### Example: Login Flow

```
browser_act(action="navigate", url="https://mail.com")
# → snapshot shows [1] Button: Log In

browser_act(action="click", ref=1)
# → snapshot shows [3] Input(textbox): 'Email', [4] Input(password): 'Password', [5] Button: Sign In

browser_act(action="type", ref=3, text="me@mail.com")
browser_act(action="type", ref=4, text="mypassword")
browser_act(action="click", ref=5)
```

## Dependencies

- `playwright` — `playwright install chromium` must be run once
- `beautifulsoup4`

## How It Works

1. **Browser Layer**: Isolated Chromium instance (non-headless by default so user can watch)
2. **Perception (Snapshot)**: AXTree fetched via Chrome DevTools Protocol → numbered element refs
3. **Action**: Ref ID resolved to DOM backend node ID via CDP → Playwright ElementHandle → click/type
4. **State**: Cookies/localStorage saved to `brain/vault/browser_state.json` after each action

## Security

- Masks WebDriver flags (anti-bot stealth)
- Blocks ads and heavy assets for speed
- Redirects popup windows into the same tab
- Session cookies persist between conversations (stored in vault)
