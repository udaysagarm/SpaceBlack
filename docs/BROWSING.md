# Autonomous Web Browsing

**Ghost** (the agent) uses **Space Black's** advanced autonomous browsing capabilities to interact with the modern web. Unlike simple HTML scrapers, Space Black provides a full headless browser environment that can see, click, type, and scroll just like a human.

## Core Capabilities

The browser engine is designed to handle dynamic, JavaScript-heavy websites (React, Vue, Angular, etc.) that traditional CLI tools cannot access.

### 1. Vision (Accessibility Tree)
Ghost doesn't just "read source code." It uses the **Chrome DevTools Protocol (CDP)** to fetch the **Accessibility Tree (AXTree)**. This provides a semantic understanding of the page, allowing Ghost to identify:
- Buttons and Links (by their text or purpose)
- Form Fields (by their labels)
- Headings and Structural Elements
- Interactive States (Disabled, Expanded, etc.)

### 2. Interaction
Ghost can perform human-like actions:
- **Click**: `browser_click(selector)` - Click elements by their ID or semantic label.
- **Type**: `browser_type(selector, text)` - Fill out forms, search bars, and login fields.
- **Scroll**: `browser_scroll(direction, amount)` - Move through long pages or infinite scrolls.
- **Navigate**: `browser_go_to(url)` - Visit any accessible URL.
- **Go Back/Forward**: Navigate browser history.

### 3. Loop (Think-Act-Observe)
Browsing is not a one-shot process. Ghost enters a **browsing loop**:
1.  **Observe**: Ghost looks at the current page state (Vision).
2.  **Think**: Ghost analyzes the page to find the element needed for its goal.
3.  **Act**: Ghost performs an action (e.g., clicks "Login").
4.  **Wait**: The browser waits for the network and DOM to settle.
5.  **Repeat**: Ghost observes the new page state.

### 4. Stealth & Anti-Detection
Modern websites often block bots. Space Black's browser includes stealth features:
- **User-Agent Rotation**: Mimics a real desktop browser.
- **Flag Masking**: Hides "navigator.webdriver" and other automation flags.
- **Human-like Delays**: randomized pauses between actions to avoid bot detection patterns.

### 5. Persistence
The browser session maintains state across actions:
- **Cookies**: Logged-in sessions persist (e.g., if Ghost logs into GitHub, it stays logged in).
- **Local Storage**: Site preferences are saved.
- **Session Vault**: Sensitive session data is stored securely in `brain/vault/`.

## Usage Examples

You can ask Ghost to perform complex web tasks naturally:

### Research
> "Go to news.ycombinator.com and tell me the top 3 stories about AI."

### Navigation & Interaction
> "Go to amazon.com, search for 'mechanical keyboard', and tell me the price of the first result."

### Data Extraction
> "Go to the Python 3.12 release notes and summarize the new features."

### Troubleshooting
> "Go to stackoverflow.com and find the solution to 'React useEffect infinite loop'."

## Technical Details

- **Engine**: Chromium (via Playwright)
- **Protocol**: Chrome DevTools Protocol (CDP)
- **State Storage**: `brain/vault/browser_session/`
- **Headless Mode**: Defaults to `True` (runs in background), but can be set to `False` in `config.json` for debugging (watch Ghost browse).

## Limitations

- **CAPTCHAs**: While Ghost can solve some simple challenges, complex CAPTCHAs (like reCAPTCHA v3) may still block access.
- **2FA**: Two-Factor Authentication requires user intervention (Ghost will pause and ask for the code).
- **Heavy Media**: Video playback is disabled to save resources.
