"""
OpenClaw-Style Autonomous Browser (v3 — Fast)
===============================================
Key fix in v3: snapshot uses a SINGLE JavaScript call to find, label, and tag
all interactive elements. Previous versions did 400+ individual CDP roundtrips
(one per element) which caused multi-minute hangs on complex sites like Amazon, X.com.

Architecture:
  Snapshot: single page.evaluate() → numbers elements → injects data-sbref=N → returns list
  Action:   page.locator('[data-sbref="N"]') — plain Playwright

Additional improvements:
  - Falls back from CDP AXTree to pure-JS snapshot if AXTree is slow/missing
  - Smart element filtering: focuses on what matters (inputs, buttons, links)
  - Grouped sections so the LLM can orient itself quickly
  - Configurable element cap to keep context tight
"""

import asyncio
import os
import json
import random
import datetime
from typing import Optional
from langchain_core.tools import tool
from playwright.async_api import async_playwright, Page

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR       = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
VAULT_DIR      = os.path.join(ROOT_DIR, "brain", "vault")
STATE_FILE     = os.path.join(VAULT_DIR, "browser_state.json")
SCREENSHOT_DIR = os.path.join(VAULT_DIR, "screenshots")
os.makedirs(VAULT_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

MAX_ELEMENTS = 80   # Cap: agent only needs a manageable list


# ── Browser Session ────────────────────────────────────────────────────────────
class BrowserSession:
    """Singleton Chromium session — stealth, persistent cookies, OpenClaw isolation."""
    _playwright = None
    _browser    = None
    _context    = None
    _page       = None

    @classmethod
    async def get_page(cls) -> Page:
        if not cls._playwright:
            cls._playwright = await async_playwright().start()

        if not cls._browser or not cls._browser.is_connected():
            cls._browser = await cls._playwright.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--start-maximized",
                    "--no-sandbox",
                ],
                ignore_default_args=["--enable-automation"],
            )

        if not cls._context:
            saved_state = None
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE) as f:
                        saved_state = json.load(f)
                except Exception:
                    pass

            ua = random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            ])
            cls._context = await cls._browser.new_context(
                storage_state=saved_state,
                user_agent=ua,
                viewport={"width": 1366, "height": 768},
                locale="en-US",
                timezone_id="America/New_York",
            )
            # Stealth
            await cls._context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )
            await cls._context.add_init_script(
                "window.chrome = { runtime:{}, loadTimes:function(){}, csi:function(){}, app:{} };"
            )
            await cls._context.add_init_script("""
                const _orig = window.navigator.permissions.query;
                window.navigator.permissions.query = (p) =>
                    p.name === 'notifications' ? Promise.resolve({ state: 'granted' }) : _orig(p);
            """)
            await cls._context.add_init_script(
                "window.open = function(url){ if(url) window.location.href=url; return window; };"
            )
            await cls._context.add_init_script("""
                document.addEventListener('click', function(e){
                    var t=e.target; while(t&&t.tagName!=='A') t=t.parentNode;
                    if(t&&t.tagName==='A') t.removeAttribute('target');
                }, true);
            """)

        if not cls._context.pages:
            cls._page = await cls._context.new_page()
        else:
            cls._page = cls._context.pages[-1]

        # Block ads / heavy assets
        try:
            await cls._page.route("**/*", lambda route:
                route.abort() if (
                    route.request.resource_type in ["image", "media", "font"]
                    or any(ad in route.request.url for ad in [
                        "doubleclick.net", "googleadservices", "googlesyndication",
                        "amazon-adsystem", "moatads", "criteo", "adnxs",
                    ])
                ) else route.continue_()
            )
        except Exception:
            pass

        return cls._page

    @classmethod
    async def save_state(cls):
        if cls._context:
            try:
                await cls._context.storage_state(path=STATE_FILE)
            except Exception:
                pass

    @classmethod
    async def close(cls):
        if cls._context:
            await cls.save_state()
            await cls._context.close()
            cls._context = None
        if cls._browser:
            await cls._browser.close()
            cls._browser = None


# ── Fast Semantic Snapshot ─────────────────────────────────────────────────────
# The SINGLE JavaScript call that does everything in one browser roundtrip:
# 1. Remove stale sbref attributes
# 2. Find all interactive/visible elements
# 3. Assign numbered refs and inject data-sbref attributes
# 4. Return a structured list for the agent to read

_JS_SNAPSHOT = """() => {
    // Clear old refs
    document.querySelectorAll('[data-sbref]').forEach(el => el.removeAttribute('data-sbref'));

    const MAX = """ + str(MAX_ELEMENTS) + """;
    const results = [];
    let ref = 0;

    // Selectors we care about — ordered by priority
    const SELECTOR = [
        'input:not([type=hidden]):not([disabled])',
        'textarea:not([disabled])',
        'select:not([disabled])',
        'button:not([disabled])',
        'a[href]',
        '[role="button"]:not([disabled])',
        '[role="link"]',
        '[role="textbox"]',
        '[role="searchbox"]',
        '[role="combobox"]',
        '[role="checkbox"]',
        '[role="radio"]',
        '[role="menuitem"]',
        '[role="option"]',
        '[role="tab"]',
        '[role="switch"]',
    ].join(',');

    const seen = new Set();
    const candidates = document.querySelectorAll(SELECTOR);

    for (const el of candidates) {
        if (ref >= MAX) break;

        // Skip duplicates
        if (seen.has(el)) continue;
        seen.add(el);

        // Skip hidden/disabled
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
        if (el.disabled || el.getAttribute('aria-disabled') === 'true') continue;
        if (el.getAttribute('aria-hidden') === 'true') continue;

        // Skip elements with zero size (invisible)
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) continue;

        // Get best label
        let label = (
            el.getAttribute('aria-label') ||
            el.getAttribute('title') ||
            el.getAttribute('placeholder') ||
            el.innerText ||
            el.value ||
            el.getAttribute('name') ||
            ''
        ).trim().replace(/\\s+/g, ' ').slice(0, 80);

        // Determine type
        const tag  = el.tagName.toLowerCase();
        const role = el.getAttribute('role') || tag;
        const type = el.getAttribute('type') || '';

        let kind;
        if (tag === 'input') {
            if (['submit','button','reset','image'].includes(type)) kind = 'Button';
            else if (type === 'checkbox') kind = 'Checkbox';
            else if (type === 'radio')    kind = 'Radio';
            else kind = `Input(${type || 'text'})`;
        } else if (tag === 'textarea') {
            kind = 'Input(textarea)';
        } else if (tag === 'select') {
            // Get selected option text
            const opt = el.options[el.selectedIndex];
            if (opt) label = label || opt.text;
            kind = 'Select';
        } else if (tag === 'button' || role === 'button') {
            kind = 'Button';
        } else if (tag === 'a' || role === 'link') {
            kind = 'Link';
        } else if (['textbox','searchbox','combobox'].includes(role)) {
            kind = `Input(${role})`;
        } else if (role === 'checkbox') {
            kind = 'Checkbox';
        } else if (role === 'radio') {
            kind = 'Radio';
        } else if (role === 'tab') {
            kind = 'Tab';
        } else if (role === 'menuitem') {
            kind = 'MenuItem';
        } else {
            kind = role.charAt(0).toUpperCase() + role.slice(1);
        }

        // Skip links with no meaningful label (noise)
        if (kind === 'Link' && !label) continue;

        ref++;
        el.setAttribute('data-sbref', String(ref));
        results.push({ ref, kind, label });
    }

    return results;
}"""


async def _take_snapshot(page: Page) -> str:
    """
    Fast semantic snapshot — one single JS call for discovery and tagging.
    Falls back to a minimal error message if page is not ready.
    Output is capped at MAX_ELEMENTS and kept concise for the LLM.
    """
    url   = page.url
    title = ""
    try:
        title = await asyncio.wait_for(page.title(), timeout=3.0)
    except Exception:
        pass

    lines = [f"URL: {url}", f"Title: {title}", ""]

    # Open tabs
    tab_lines = []
    for p in page.context.pages:
        try:
            t    = await asyncio.wait_for(p.title(), timeout=2.0)
            u    = p.url
            mark = " ← active" if p == page else ""
            tab_lines.append(f"  - {t} [{u}]{mark}")
        except Exception:
            tab_lines.append("  - (unknown tab)")
    if tab_lines:
        lines.append("Tabs:\n" + "\n".join(tab_lines))
        lines.append("")

    # Run the single JS snapshot call
    try:
        elements = await asyncio.wait_for(page.evaluate(_JS_SNAPSHOT), timeout=8.0)
    except asyncio.TimeoutError:
        lines.append("  [Snapshot timed out — page may still be loading]")
        lines.append("  Try: browser_act(action='wait', duration=3)")
        return "\n".join(lines)
    except Exception as e:
        lines.append(f"  [Snapshot error: {e}]")
        return "\n".join(lines)

    if not elements:
        lines.append("  [No interactive elements found — page may be loading or blank]")
        lines.append("  Try: browser_act(action='wait', duration=2)")
        return "\n".join(lines)

    # Format element list
    lines.append("Interactive Elements:")
    for el in elements:
        ref   = el["ref"]
        kind  = el["kind"]
        label = el["label"] or "(no label)"
        lines.append(f"  [{ref:>3}] {kind}: {label}")

    total = len(elements)
    capped = " (capped — scroll down and call snapshot again for more)" if total >= MAX_ELEMENTS else ""
    lines.append(f"\n  ({total} elements found{capped})")
    lines.append("  Use ref=N numbers above to click/type. Example: browser_act(action='click', ref=2)")

    return "\n".join(lines)


def _ref_selector(ref: int) -> str:
    return f'[data-sbref="{ref}"]'


# ── Unified Tool ───────────────────────────────────────────────────────────────
@tool
async def browser_act(
    action: str,
    url: Optional[str]       = None,
    ref: Optional[int]       = None,
    text: Optional[str]      = None,
    direction: Optional[str] = "down",
    amount: Optional[int]    = 500,
    duration: Optional[int]  = 2,
    key: Optional[str]       = None,
) -> str:
    """
    Unified autonomous browser control — OpenClaw style.

    WORKFLOW:
    1. browser_act(action="navigate", url="https://site.com")   → see numbered elements
    2. browser_act(action="click", ref=N)                        → click element N
    3. browser_act(action="type",  ref=N, text="hello")          → type into element N
    ALWAYS read the snapshot numbers first. NEVER guess ref numbers.

    ACTIONS:
    - navigate      : Go to URL.   Requires: url="https://..."
    - snapshot      : Re-read page without acting.
    - click         : Click element. Requires: ref=N
    - type          : Type into input. Requires: ref=N, text="..."
    - clear_and_type: Clear then type. Requires: ref=N, text="..."
    - press         : Press keyboard key. Requires: key="Enter" / "Tab" / "Escape" / etc.
    - scroll        : Scroll page. Optional: direction="down"/"up", amount=500 (pixels)
    - wait          : Wait for loading. Optional: duration=2 (seconds)
    - screenshot    : Save a screenshot.
    - back          : Go back.
    - forward       : Go forward.
    - close         : Close browser.
    """
    action = action.lower().strip()

    if action == "close":
        await BrowserSession.close()
        return "Browser closed."

    try:
        page = await BrowserSession.get_page()
    except Exception as e:
        return f"Browser start failed: {e}"

    # ── NAVIGATE ───────────────────────────────────────────────────────────────
    if action == "navigate":
        if not url:
            return "Error: navigate needs url=..."
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            # Brief settle for JS SPAs — but DON'T wait for networkidle (hangs forever on X/Amazon)
            await asyncio.sleep(1.5)
            await BrowserSession.save_state()
            return f"Navigated to {url}.\n\n{await _take_snapshot(page)}"
        except Exception as e:
            return f"Navigation error: {e}"

    # ── SNAPSHOT ───────────────────────────────────────────────────────────────
    if action == "snapshot":
        return await _take_snapshot(page)

    # ── WAIT ───────────────────────────────────────────────────────────────────
    if action == "wait":
        secs = duration or 2
        await asyncio.sleep(secs)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=4000)
        except Exception:
            pass
        return f"Waited {secs}s.\n\n{await _take_snapshot(page)}"

    # ── SCROLL ─────────────────────────────────────────────────────────────────
    if action == "scroll":
        px = amount or 500
        dy = px if (direction or "down") == "down" else -px
        await page.evaluate(f"window.scrollBy(0, {dy})")
        await asyncio.sleep(0.3)
        return f"Scrolled {direction} {px}px.\n\n{await _take_snapshot(page)}"

    # ── BACK / FORWARD ─────────────────────────────────────────────────────────
    if action == "back":
        await page.go_back(wait_until="domcontentloaded", timeout=10000)
        await BrowserSession.save_state()
        return f"Went back.\n\n{await _take_snapshot(page)}"

    if action == "forward":
        await page.go_forward(wait_until="domcontentloaded", timeout=10000)
        await BrowserSession.save_state()
        return f"Went forward.\n\n{await _take_snapshot(page)}"

    # ── PRESS ──────────────────────────────────────────────────────────────────
    if action == "press":
        if not key:
            return "Error: press needs key=... (e.g. key='Enter')"
        await page.keyboard.press(key)
        await asyncio.sleep(0.8)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=4000)
        except Exception:
            pass
        await BrowserSession.save_state()
        return f"Pressed '{key}'.\n\n{await _take_snapshot(page)}"

    # ── SCREENSHOT ─────────────────────────────────────────────────────────────
    if action == "screenshot":
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOT_DIR, f"shot_{ts}.png")
        await page.screenshot(path=path, full_page=False)
        return f"Screenshot: {path}"

    # ── CLICK / TYPE ───────────────────────────────────────────────────────────
    if action in ("click", "type", "clear_and_type"):
        if ref is None:
            return (
                f"Error: '{action}' needs ref=N. "
                "Run browser_act(action='snapshot') first to see element numbers."
            )

        selector = _ref_selector(ref)

        # Verify the element exists (our JS tag is present in DOM)
        count = 0
        try:
            count = await page.locator(selector).count()
        except Exception:
            pass

        if count == 0:
            return (
                f"Element [{ref}] not in DOM — snapshot may be stale. "
                "Call browser_act(action='snapshot') to refresh element numbers."
            )

        locator = page.locator(selector).first

        # ── CLICK ──────────────────────────────────────────────────────────
        if action == "click":
            try:
                await locator.scroll_into_view_if_needed(timeout=3000)
                await locator.click(timeout=6000)
                await asyncio.sleep(0.8)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass
                await BrowserSession.save_state()
                return f"Clicked [{ref}].\n\n{await _take_snapshot(page)}"
            except Exception as e:
                # Force-click fallback (bypasses overlays / pointer-events:none)
                try:
                    await page.evaluate(f"""
                        const el = document.querySelector('[data-sbref="{ref}"]');
                        if (el) {{ el.dispatchEvent(new MouseEvent('click', {{bubbles:true, cancelable:true}})); }}
                    """)
                    await asyncio.sleep(0.8)
                    await BrowserSession.save_state()
                    return f"Clicked [{ref}] (JS fallback).\n\n{await _take_snapshot(page)}"
                except Exception as e2:
                    return f"Click failed [{ref}]: {e} | JS: {e2}"

        # ── TYPE / CLEAR_AND_TYPE ──────────────────────────────────────────
        if action in ("type", "clear_and_type"):
            if text is None:
                return "Error: type needs text=..."
            try:
                await locator.scroll_into_view_if_needed(timeout=3000)
                await locator.click(timeout=3000)
                if action == "clear_and_type":
                    await page.keyboard.press("Control+a")
                    await page.keyboard.press("Delete")
                    await asyncio.sleep(0.1)
                await locator.type(text, delay=45)
                await BrowserSession.save_state()
                verb = "Cleared and typed" if action == "clear_and_type" else "Typed"
                return f"{verb} {repr(text)} into [{ref}].\n\n{await _take_snapshot(page)}"
            except Exception as e:
                # JS fallback — set .value and fire React-compatible events
                try:
                    await page.evaluate(f"""
                        const el = document.querySelector('[data-sbref="{ref}"]');
                        if (el) {{
                            el.focus();
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                                window.HTMLInputElement.prototype, 'value') ||
                                Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
                            if (nativeInputValueSetter) nativeInputValueSetter.set.call(el, {json.dumps(text)});
                            else el.value = {json.dumps(text)};
                            el.dispatchEvent(new Event('input',  {{bubbles:true}}));
                            el.dispatchEvent(new Event('change', {{bubbles:true}}));
                        }}
                    """)
                    return f"Typed (JS) {repr(text)} into [{ref}].\n\n{await _take_snapshot(page)}"
                except Exception as e2:
                    return f"Type failed [{ref}]: {e} | JS: {e2}"

    # ── UNKNOWN ────────────────────────────────────────────────────────────────
    return (
        f"Unknown action '{action}'. "
        "Valid: navigate, snapshot, click, type, clear_and_type, press, scroll, wait, screenshot, back, forward, close"
    )
