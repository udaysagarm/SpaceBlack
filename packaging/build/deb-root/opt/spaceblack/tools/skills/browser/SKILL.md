---
name: Browser Skill
description: Autonomous web browsing using OpenClaw-style Semantic Snapshots, intelligent waits, and CDP interaction.
---

# Browser Skill (OpenClaw Architecture)

This skill gives the agent autonomous control of a real Chromium browser. It uses the same architectural approach as **OpenClaw**: every page is rendered as a **Semantic Snapshot** — a structured text representation with page content AND numbered interactive elements drawn from the browser's Accessibility Tree.

The agent reads the page like a screen-reader would: headings, paragraphs, labels **and** interactive elements (`[ref=N]`). It acts by reference number — no CSS selectors needed.

## The Single Tool: `browser_act`

Everything goes through one tool with an `action` parameter.

### Actions

| Action | What it does | Required params |
|--------|-------------|-----------------|
| `navigate` | Go to a URL | `url` |
| `click` | Click an element | `ref` |
| `fill` | Clear + fill an input field | `ref`, `text` |
| `type` | Append text to a field | `ref`, `text` |
| `press` | Press a keyboard key | `key` (e.g. `"Enter"`, `"Tab"`, `"Control+a"`) |
| `hover` | Hover over an element | `ref` |
| `select_option` | Pick from dropdown | `ref`, `value` or `text` |
| `upload_file` | Upload a file | `ref`, `filepath` |
| `scroll` | Scroll the page | `direction` (`"up"`/`"down"`), `amount` (px) |
| `wait` | Simple wait + re-snapshot | `duration` (seconds) |
| `wait_for` | Wait for condition | `selector` or `url` pattern |
| `snapshot` | Re-read current page state | — |
| `get_text` | Extract readable text content | — |
| `screenshot` | Save a screenshot | — |
| `back` / `forward` | Browser navigation | — |
| `new_tab` | Open URL in new tab | `url` |
| `switch_tab` | Change active tab | `index` |
| `close_tab` | Close current tab | — |
| `close` | Close the browser | — |

### Semantic Snapshot (what the agent sees)

After every action, the agent receives a structured view of the page:

```
URL: https://mail.com
Title: Mail.com - Free Email

  ## Welcome to Mail.com
  Sign in to your account
  [  1] Link: 'Log In'
  [  2] Link: 'Sign Up'
  [  3] Textbox: 'Email' value=''
  Already have an account? Sign in below.

(3 interactive elements. Use ref=N to interact.)
```

The snapshot includes **both** readable content (headings, text) **and** interactive elements with `[ref=N]` markers. This gives the agent full page comprehension.

### Example: Login Flow

```
browser_act(action="navigate", url="https://mail.com")
# → snapshot shows page structure + [1] Link: 'Log In'

browser_act(action="click", ref=1)
# → page navigates, snapshot shows login form:
#   [3] Textbox: 'Email', [4] Textbox: 'Password', [5] Button: 'Sign In'

browser_act(action="fill", ref=3, text="me@mail.com")
browser_act(action="fill", ref=4, text="mypassword")
browser_act(action="click", ref=5)
# → logged in, snapshot shows inbox
```

### Autonomous Workflow

1. **Navigate** to a URL → read the snapshot
2. **Understand** the page from headings, text, and labels
3. **Find** the element you need by ref number
4. **Act** (click/fill/type) using `ref=N`
5. **Read** the new snapshot returned after each action
6. **Repeat** until the task is complete — no human intervention needed

### Intelligent Waits

- `wait_for(selector="#login-form")` — wait for a CSS selector to appear
- `wait_for(url="**/dashboard")` — wait for URL to match a pattern
- `wait(duration=3)` — simple timed wait
- **Auto-wait**: every action automatically waits for the page to settle (network idle) before returning the snapshot

## Dependencies

- `playwright` — run `playwright install chromium` once after install

## Architecture

1. **Session**: Persistent Chromium profile (logins survive restarts)
2. **Perception**: CDP `Accessibility.getFullAXTree` → hierarchical snapshot
3. **Interaction**: CDP mouse/keyboard events with 3-level fallback (box-coords → JS click → focus+Enter)
4. **Recovery**: Stale refs reported cleanly; CDP auto-reconnects if session dies
5. **Stealth**: WebDriver flag masking, realistic user-agent, plugin spoofing
