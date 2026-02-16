---
name: Browser Skill
description: Provides headless web browsing capabilities to read dynamic websites.
---

# Browser Skill

This skill enables the agent to "see" the web using a headless Chromium browser. Unlike simple `requests`, this can render JavaScript, making it possible to read modern Single Page Applications (SPAs) like React, Vue, or Angular sites.

## Tools

### `visit_page`
- **Description**: Visits a URL, renders the JavaScript, and returns the text content converted to Markdown.
- **Usage**: Use this when `web_search` results are insufficient or when you need to read a specific documentation page, article, or dynamic site.
- **Parameters**: 
    - `url` (str): The full URL to visit (e.g., `https://example.com`).

## Dependencies
- `playwright`
- `beautifulsoup4`
- `html2text`
- **System Requirement**: `playwright install chromium` must be run once.

## Security Constraints
- The browser runs in headless mode.
- Scripts are executed, so be cautious with untrusted URLs.
- No file downloads or uploads are supported yet.
