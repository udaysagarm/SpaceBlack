"""
browser.py — Space Black browser tool (OpenClaw/browser-use CDP architecture, v7)

Discovery : CDP Accessibility.getFullAXTree  → real AX tree, dialog-aware, no JS hacks
Interaction: CDP Input.dispatchMouseEvent + Input.insertText → real hardware events
             (Gmail, Workday, React, Angular all respond correctly)
Reference  : backendNodeId  — the browser's own stable node pointer, not data-sbref

All actions return a fresh snapshot string so the agent always knows the new page state.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import string
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.async_api import (
    Browser,
    BrowserContext,
    CDPSession,
    Page,
    Playwright,
    async_playwright,
)
from langchain_core.tools import tool


# ── Paths ──────────────────────────────────────────────────────────────────────
_ROOT   = Path(__file__).parent.parent.parent.parent  # project root
_STATE  = _ROOT / "brain" / "vault" / "browser_state.json"
_SHOTS  = _ROOT / "brain" / "screenshots"
_SHOTS.mkdir(parents=True, exist_ok=True)


# ── Element registry ───────────────────────────────────────────────────────────
@dataclass
class _Elem:
    backend_node_id: int    # CDP's own stable DOM reference
    role:            str    # "textbox", "button", "combobox", "link", …
    name:            str    # Accessible name shown to agent
    frame_url:       str = ""


# page_id → {ref_number: _Elem}
_REGISTRY: Dict[int, Dict[int, _Elem]] = {}


# Roles that are genuinely user-interactive — strictly whitelisted
# Everything structural/decorative (dialog, navigation, statictext, tooltip,
# layouttable, banner, etc.) is excluded so they don't crowd out input fields.
_INTERACTIVE_ROLES = {
    "button", "link",
    "textbox", "searchbox", "combobox", "spinbutton",
    "checkbox", "radio",
    "menuitem", "menuitemcheckbox", "menuitemradio",
    "option", "tab", "switch", "treeitem",
    "slider", "columnheader", "rowheader", "row", "gridcell",
    "listbox",
    # Include heading as read-only context nodes (agent needs them to understand page)
    "heading",
}

_MAX_ELEMENTS = 150   # generous cap — only interactive roles now, so fewer total


# ── AX tree DOM roles we care about ───────────────────────────────────────────



# ── Stealth JS injected at page creation ──────────────────────────────────────
_JS_STEALTH = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
window.chrome = {runtime: {}};
"""


# ── Page content extractor (unchanged from v6) ────────────────────────────────
_JS_CONTENT = """() => {
    const MAX = 7000;
    const lines = [];
    const seen = new Set();

    const add = (text, prefix) => {
        const t = (text || '').trim().replace(/\\s+/g, ' ');
        if (t.length > 3 && !seen.has(t)) { seen.add(t); lines.push((prefix||'') + t); }
    };

    // Priority: email/grid rows
    const rows = [...document.querySelectorAll(
        '[role="row"], tr[tabindex], [role="listitem"][tabindex], [data-convid], [data-messageid]'
    )].filter(el => {
        const s = window.getComputedStyle(el);
        if (s.display === 'none' || s.visibility === 'hidden') return false;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
    });

    if (rows.length > 0) {
        let n = 0;
        for (const row of rows) {
            if (n++ >= 40) { lines.push('...(more rows — scroll)'); break; }
            const t = (row.innerText || '').trim().replace(/\\s+/g, ' ');
            if (t.length > 3 && !seen.has(t)) {
                seen.add(t);
                lines.push('• ' + t.slice(0, 130));
            }
        }
        if (lines.join('\\n').length < MAX) {
            const headings = document.querySelectorAll('h1, h2, h3');
            headings.forEach(h => add(h.innerText, '# '));
        }
        return lines.join('\\n').slice(0, MAX);
    }

    // Fallback: semantic content
    const root = document.querySelector('main,[role="main"],article,#content') || document.body;
    const walk = (el, depth) => {
        if (depth > 6 || !el) return;
        if (['SCRIPT','STYLE','NAV','FOOTER','HEAD','NOSCRIPT'].includes(el.tagName||'')) return;
        const st = window.getComputedStyle(el);
        if (st.display === 'none' || st.visibility === 'hidden') return;
        if (el.nodeType === 3) { add(el.textContent); return; }
        const tag = (el.tagName||'').toLowerCase();
        if (['h1','h2','h3'].includes(tag)) add(el.innerText, '# ');
        else if (tag === 'li') add(el.innerText, '• ');
        else if (['p','td','th'].includes(tag)) add(el.innerText);
        for (const ch of el.childNodes) {
            if (lines.join('\\n').length >= MAX) return;
            walk(ch, depth + 1);
        }
    };
    walk(root, 0);
    return lines.join('\\n').slice(0, MAX) || document.title;
}"""


# ── Cookie/banner dismissal ────────────────────────────────────────────────────
async def _dismiss_banners(page: Page) -> None:
    selectors = [
        'button[id*="accept"]', 'button[id*="cookie"]', 'button[id*="consent"]',
        'button[class*="accept"]', 'button[class*="cookie"]',
        '[aria-label*="Accept"]', '[aria-label*="Close"]',
        'button:has-text("Accept all")', 'button:has-text("I agree")',
        'button:has-text("Got it")', 'button:has-text("OK")',
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=300):
                await btn.click(timeout=500)
                await asyncio.sleep(0.3)
                break
        except Exception:
            pass


# ── BrowserSession (singleton) ─────────────────────────────────────────────────
class BrowserSession:
    _playwright:  Optional[Playwright]     = None
    _browser:     Optional[Browser]        = None
    _context:     Optional[BrowserContext] = None
    _page:        Optional[Page]           = None
    _cdp:         Optional[CDPSession]     = None
    _lock:        asyncio.Lock             = asyncio.Lock()

    @classmethod
    async def get_page(cls) -> Tuple[Page, CDPSession]:
        async with cls._lock:
            if cls._page is None or cls._page.is_closed():
                await cls._launch()
            return cls._page, cls._cdp   # type: ignore[return-value]

    @classmethod
    async def _launch(cls) -> None:
        if cls._playwright is None:
            cls._playwright = await async_playwright().start()

        launch_args = [
            "--no-sandbox", "--disable-blink-features=AutomationControlled",
            "--disable-infobars", "--start-maximized",
            "--disable-web-security", "--disable-features=IsolateOrigins",
        ]

        cls._browser = await cls._playwright.chromium.launch(
            headless=False,
            args=launch_args,
        )

        storage: dict = {}
        if _STATE.exists():
            try:
                storage = json.loads(_STATE.read_text())
            except Exception:
                pass

        ctx_kwargs: dict = {
            "viewport": {"width": 1366, "height": 768},
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }
        if storage:
            ctx_kwargs["storage_state"] = storage

        cls._context = await cls._browser.new_context(**ctx_kwargs)
        await cls._context.add_init_script(_JS_STEALTH)

        cls._page = await cls._context.new_page()

        # ── Open a CDP session on this context for Accessibility + Input APIs ──
        cls._cdp = await cls._context.new_cdp_session(cls._page)
        await cls._cdp.send("Accessibility.enable")

    @classmethod
    async def save_state(cls) -> None:
        if cls._context:
            try:
                state = await cls._context.storage_state()
                _STATE.parent.mkdir(parents=True, exist_ok=True)
                _STATE.write_text(json.dumps(state))
            except Exception:
                pass

    @classmethod
    async def close_all(cls) -> None:
        await cls.save_state()
        if cls._cdp:
            try:
                await cls._cdp.detach()
            except Exception:
                pass
        if cls._browser:
            await cls._browser.close()
        if cls._playwright:
            await cls._playwright.stop()
        cls._playwright = cls._browser = cls._context = cls._page = cls._cdp = None


# ── CDP helpers ────────────────────────────────────────────────────────────────

async def _ax_snapshot(cdp: CDPSession) -> List[dict]:
    """Return the full AX tree as a flat list of AX node dicts."""
    try:
        result = await asyncio.wait_for(
            cdp.send("Accessibility.getFullAXTree", {}),
            timeout=8.0,
        )
        return result.get("nodes", [])
    except Exception as e:
        return []


def _ax_name(node: dict) -> str:
    """Extract the best accessible name from an AX node."""
    for prop in node.get("properties", []):
        if prop.get("name") in ("name",):
            return (prop.get("value", {}).get("value") or "").strip()
    nv = node.get("name", {})
    if isinstance(nv, dict):
        return (nv.get("value") or "").strip()
    return (nv or "").strip()


def _ax_role(node: dict) -> str:
    rv = node.get("role", {})
    if isinstance(rv, dict):
        return (rv.get("value") or "").lower().strip()
    return (rv or "").lower().strip()


def _ax_ignored(node: dict) -> bool:
    return bool(node.get("ignored", False))


def _ax_backend_id(node: dict) -> Optional[int]:
    bid = node.get("backendDOMNodeId")
    if bid:
        return int(bid)
    return None


def _build_registry(nodes: List[dict]) -> Tuple[Dict[int, _Elem], List[dict]]:
    """
    Walk the flat AX node list. Only register roles in _INTERACTIVE_ROLES.
    This is a strict whitelist — structural/decorative nodes are never registered,
    so interactive elements like Gmail's To combobox always get a ref number.
    Returns (registry_dict, display_rows).
    """
    registry: Dict[int, _Elem] = {}
    rows: List[dict] = []
    ref = 0

    for node in nodes:
        if ref >= _MAX_ELEMENTS:
            break
        if _ax_ignored(node):
            continue
        role = _ax_role(node)
        # Strict whitelist — only interactive roles get registered
        if role not in _INTERACTIVE_ROLES:
            continue
        backend_id = _ax_backend_id(node)
        if not backend_id:
            continue
        name = _ax_name(node)
        # Skip empty-label buttons/links (invisible noise)
        if not name and role in ("button", "link", "menuitem"):
            continue

        ref += 1
        registry[ref] = _Elem(
            backend_node_id=backend_id,
            role=role,
            name=name,
        )
        rows.append({"ref": ref, "role": role, "name": name})

    return registry, rows



async def _take_snapshot(page: Page, cdp: CDPSession) -> str:
    """Build snapshot string and update the global registry."""
    title = await page.title()
    url   = page.url

    nodes   = await _ax_snapshot(cdp)
    reg, rows = _build_registry(nodes)
    _REGISTRY[id(page)] = reg

    parts: List[str] = [f"URL: {url}", f"Title: {title}", ""]
    if not rows:
        parts.append("(no interactive elements found)")
    else:
        # Group by role family for readability
        for r in rows:
            role_label = r["role"].capitalize()
            name       = r["name"] or "(no label)"
            parts.append(f"[{r['ref']:>3}] {role_label}: {repr(name)}")

    return "\n".join(parts)


# ── CDP interaction primitives ─────────────────────────────────────────────────

async def _get_box(cdp: CDPSession, backend_node_id: int) -> Optional[Tuple[float, float]]:
    """Return (cx, cy) centre coordinates for the element, or None."""
    try:
        result = await cdp.send("DOM.getBoxModel", {"backendNodeId": backend_node_id})
        box = result.get("model", {}).get("content")  # [x0,y0, x1,y1, x2,y2, x3,y3]
        if box and len(box) >= 8:
            xs = [box[i] for i in range(0, 8, 2)]
            ys = [box[i] for i in range(1, 8, 2)]
            return sum(xs) / 4, sum(ys) / 4
    except Exception:
        pass
    # Fallback: ask JS for the bounding rect
    try:
        js = f"""
        (function() {{
            const el = document.querySelector('[data-sbref]') || null;
            // use CDP resolved node instead — we'll try DOM.resolveNode
            return null;
        }})()
        """
    except Exception:
        pass
    return None


async def _cdp_resolve_node(cdp: CDPSession, backend_node_id: int) -> Optional[str]:
    """Resolve a backendNodeId to a Runtime.RemoteObjectId (JS object handle)."""
    try:
        r = await cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})
        return r.get("object", {}).get("objectId")
    except Exception:
        return None


async def _cdp_focus(cdp: CDPSession, backend_node_id: int) -> None:
    """Focus element via CDP DOM domain."""
    try:
        await cdp.send("DOM.focus", {"backendNodeId": backend_node_id})
    except Exception:
        pass


async def _cdp_click(cdp: CDPSession, cx: float, cy: float) -> None:
    """Click at (cx, cy) using real CDP mouse events."""
    base = {"x": cx, "y": cy, "button": "left", "clickCount": 1,
            "modifiers": 0, "buttons": 0}
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mouseMoved"})
    await asyncio.sleep(0.05)
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mousePressed", "buttons": 1})
    await asyncio.sleep(0.05)
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mouseReleased", "buttons": 0})


async def _cdp_type(cdp: CDPSession, text: str) -> None:
    """
    Insert text into the currently focused element using CDP Input.insertText.
    This fires real composition events — required by Gmail, Workday, React, etc.
    """
    await cdp.send("Input.insertText", {"text": text})


async def _cdp_key(cdp: CDPSession, key: str) -> None:
    """
    Dispatch a named key event (Tab, Enter, Escape, Backspace, ArrowDown…).
    Also supports combos like Control+a, Control+Enter.
    """
    # Key name → CDP key name mapping
    _KEY_MAP = {
        "Tab": ("Tab", 9), "Enter": ("Return", 13), "Return": ("Return", 13),
        "Escape": ("Escape", 27), "Backspace": ("Backspace", 8),
        "Delete": ("Delete", 46), "ArrowDown": ("ArrowDown", 40),
        "ArrowUp": ("ArrowUp", 38), "ArrowLeft": ("ArrowLeft", 37),
        "ArrowRight": ("ArrowRight", 39),
        "Control+a": ("a", 65, 2),   # 2 = Ctrl modifier
        "Control+Enter": ("Return", 13, 2),
        "Control+c": ("c", 67, 2), "Control+v": ("v", 86, 2),
        "Control+x": ("x", 88, 2), "Control+z": ("z", 90, 2),
        "Control+Shift+C": ("c", 67, 6),  # Ctrl+Shift
        "Control+Shift+B": ("b", 66, 6),
    }
    mapped = _KEY_MAP.get(key)
    mods = 0
    if mapped:
        key_name = mapped[0]
        key_code = mapped[1]
        mods = mapped[2] if len(mapped) > 2 else 0
    else:
        key_name = key
        key_code = ord(key[0]) if len(key) == 1 else 0

    for t in ("keyDown", "keyUp"):
        await cdp.send("Input.dispatchKeyEvent", {
            "type": t,
            "key": key_name,
            "windowsVirtualKeyCode": key_code,
            "nativeVirtualKeyCode": key_code,
            "modifiers": mods,
            "code": f"Key{key_name.upper()}" if len(key_name) == 1 else key_name,
            "isKeypad": False,
        })
        await asyncio.sleep(0.03)


async def _fill_element(
    page: Page,
    cdp: CDPSession,
    ref: int,
    text: str,
) -> str:
    """
    Fill an element: get coords → click to focus → clear → insertText.
    Returns status string.
    """
    reg = _REGISTRY.get(id(page), {})
    if ref not in reg:
        return f"Error: ref [{ref}] not in registry. Run snapshot first."
    elem = reg[ref]

    # Strategy A: CDP click via DOM.getBoxModel
    cx, cy = None, None
    box = await _get_box(cdp, elem.backend_node_id)
    if box:
        cx, cy = box

    if cx is not None:
        await _cdp_click(cdp, cx, cy)
        await asyncio.sleep(0.15)
    else:
        # Fallback: focus via DOM.focus
        await _cdp_focus(cdp, elem.backend_node_id)
        await asyncio.sleep(0.15)

    # Strategy 1: DOM.focus then insertText
    try:
        # Select all existing text and delete it
        await _cdp_key(cdp, "Control+a")
        await asyncio.sleep(0.05)
        await _cdp_key(cdp, "Delete")
        await asyncio.sleep(0.05)
        await _cdp_type(cdp, text)
        return f"ok-cdp-insertText"
    except Exception as e1:
        pass

    # Strategy 2: Playwright locator fill (for standard inputs)
    try:
        loc = page.locator(f"[data-sbref='{ref}']").first
        if await loc.count() > 0:
            await loc.fill(text, timeout=3000)
            return f"ok-playwright-fill"
    except Exception as e2:
        pass

    return f"Error: all fill strategies failed for [{ref}]"


async def _click_element(page: Page, cdp: CDPSession, ref: int) -> str:
    reg = _REGISTRY.get(id(page), {})
    if ref not in reg:
        return f"Error: ref [{ref}] not in registry."
    elem = reg[ref]

    box = await _get_box(cdp, elem.backend_node_id)
    if box:
        cx, cy = box
        await _cdp_click(cdp, cx, cy)
        return "ok-cdp-click"

    # Fallback: Playwright locator click via backendNodeId JS lookup
    try:
        obj_id = await _cdp_resolve_node(cdp, elem.backend_node_id)
        if obj_id:
            await cdp.send("Runtime.callFunctionOn", {
                "functionDeclaration": "function() { this.click(); }",
                "objectId": obj_id,
            })
            return "ok-js-click"
    except Exception:
        pass

    return f"Error: could not click [{ref}]"


# ── Main tool ──────────────────────────────────────────────────────────────────

@tool
async def browser_act(
    action:    str,
    url:       Optional[str] = None,
    ref:       Optional[int] = None,
    text:      Optional[str] = None,
    value:     Optional[str] = None,
    filepath:  Optional[str] = None,
    direction: Optional[str] = "down",
    amount:    Optional[int] = 600,
    duration:  Optional[int] = 2,
    key:       Optional[str] = None,
    index:     Optional[int] = None,
) -> str:
    """
    Autonomous browser — site-agnostic across Gmail, Amazon, Workday, Reddit, X.com.

    DISCOVERY  : CDP Accessibility.getFullAXTree → real AX tree, works through dialogs.
    INTERACTION: CDP Input.insertText + Input.dispatchMouseEvent → real hardware events.
                 Gmail, React forms, Workday — all respond correctly.

    ACTIONS:
    ────────────────────────────────────────────────────────────────────────────────
    navigate       Go to URL          url="https://..."
    snapshot       Re-read page       (no args)
    get_text       Page text only     (no args) — emails, articles
    click          Click element      ref=N
    fill           Clear + fill field ref=N, text="..."   ← BEST for any input
    type           Append to field    ref=N, text="..."
    press          Keyboard key       key="Tab"/"Enter"/"Escape"/"Control+Enter"/"ArrowDown"
    hover          Hover element      ref=N
    select_option  Pick dropdown      ref=N, value="val" OR text="Label"
    upload_file    Upload a file      ref=N, filepath="/abs/path/file.pdf"
    scroll         Scroll page        direction="down"/"up", amount=600
    wait           Wait + re-snapshot duration=2
    screenshot     Save screenshot    (no args)
    back/forward   Browser nav        (no args)
    new_tab        Open in new tab    url="https://..."
    switch_tab     Change tab         index=N
    close_tab      Close tab          (no args)
    close          Close browser      (no args)
    ────────────────────────────────────────────────────────────────────────────────
    GMAIL COMPOSE — correct workflow:
      snapshot → find [N] Button: 'Compose' → click(ref=N)
      wait(duration=2)
      snapshot → find [M] Combobox: 'To'    → fill(ref=M, text="addr@email.com")
      press(key="Tab")
      snapshot → find [P] Textbox: 'Subject' → fill(ref=P, text="Subject here")
      snapshot → find [Q] Textbox: 'Message Body' → fill(ref=Q, text="Body here")
      snapshot → find [R] Button: 'Send' → click(ref=R)

    MAIL.COM, WORKDAY — same fill/click pattern. wait(duration=3) after page loads.
    AMAZON — select_option for dropdowns. scroll to see more products.
    ────────────────────────────────────────────────────────────────────────────────
    """
    action = action.lower().strip()

    if action == "close":
        await BrowserSession.close_all()
        return "Browser closed."

    try:
        page, cdp = await BrowserSession.get_page()
    except Exception as e:
        return f"Browser start failed: {e}"

    # ── NAVIGATE ────────────────────────────────────────────────────────────────
    if action == "navigate":
        if not url:
            return "Error: navigate needs url=..."
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2.5)
            await _dismiss_banners(page)
            await BrowserSession.save_state()
            snap = await _take_snapshot(page, cdp)
            return f"Navigated to {url}.\n\n{snap}"
        except Exception as e:
            return f"Navigation error: {e}"

    # ── SNAPSHOT ─────────────────────────────────────────────────────────────────
    if action == "snapshot":
        return await _take_snapshot(page, cdp)

    # ── GET_TEXT ─────────────────────────────────────────────────────────────────
    if action == "get_text":
        try:
            content = await asyncio.wait_for(page.evaluate(_JS_CONTENT), timeout=6.0)
            title   = await page.title()
            return f"URL: {page.url}\nTitle: {title}\n\n--- Content ---\n{content.strip() or '(nothing)'}"
        except Exception as e:
            return f"get_text error: {e}"

    # ── WAIT ─────────────────────────────────────────────────────────────────────
    if action == "wait":
        await asyncio.sleep(duration or 2)
        return await _take_snapshot(page, cdp)

    # ── SCREENSHOT ───────────────────────────────────────────────────────────────
    if action == "screenshot":
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(_SHOTS / f"shot_{ts}.png")
        await page.screenshot(path=path, full_page=False)
        return f"Screenshot saved: {path}"

    # ── SCROLL ───────────────────────────────────────────────────────────────────
    if action == "scroll":
        dy = -(amount or 600) if direction == "up" else (amount or 600)
        await page.mouse.wheel(0, dy)
        await asyncio.sleep(0.6)
        return await _take_snapshot(page, cdp)

    # ── BACK / FORWARD ───────────────────────────────────────────────────────────
    if action == "back":
        await page.go_back(wait_until="domcontentloaded", timeout=10000)
        await asyncio.sleep(1.5)
        return await _take_snapshot(page, cdp)

    if action == "forward":
        await page.go_forward(wait_until="domcontentloaded", timeout=10000)
        await asyncio.sleep(1.5)
        return await _take_snapshot(page, cdp)

    # ── TAB MANAGEMENT ───────────────────────────────────────────────────────────
    if action == "new_tab":
        if not url:
            return "Error: new_tab needs url=..."
        ctx = BrowserSession._context
        if not ctx:
            return "Error: no browser context."
        new_page = await ctx.new_page()
        BrowserSession._page = new_page
        BrowserSession._cdp  = await ctx.new_cdp_session(new_page)
        await BrowserSession._cdp.send("Accessibility.enable")
        cdp  = BrowserSession._cdp
        page = new_page
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2.0)
        return await _take_snapshot(page, cdp)

    if action == "switch_tab":
        ctx = BrowserSession._context
        if not ctx:
            return "Error: no browser context."
        pages = ctx.pages
        idx   = index or 0
        if idx < 0 or idx >= len(pages):
            return f"Error: tab index {idx} out of range (0–{len(pages)-1})."
        BrowserSession._page = pages[idx]
        BrowserSession._cdp  = await ctx.new_cdp_session(pages[idx])
        await BrowserSession._cdp.send("Accessibility.enable")
        cdp  = BrowserSession._cdp
        page = BrowserSession._page
        return await _take_snapshot(page, cdp)

    if action == "close_tab":
        ctx = BrowserSession._context
        if not ctx:
            return "Error: no browser context."
        await page.close()
        remaining = ctx.pages
        if remaining:
            BrowserSession._page = remaining[-1]
            BrowserSession._cdp  = await ctx.new_cdp_session(remaining[-1])
            await BrowserSession._cdp.send("Accessibility.enable")
            return await _take_snapshot(BrowserSession._page, BrowserSession._cdp)
        return "Tab closed. No remaining tabs."

    # ── PRESS ────────────────────────────────────────────────────────────────────
    if action == "press":
        if not key:
            return "Error: press needs key=..."
        await _cdp_key(cdp, key)
        await asyncio.sleep(0.4)
        return await _take_snapshot(page, cdp)

    # ── HOVER ────────────────────────────────────────────────────────────────────
    if action == "hover":
        if ref is None:
            return "Error: hover needs ref=N"
        reg = _REGISTRY.get(id(page), {})
        if ref not in reg:
            return f"Error: ref [{ref}] not found."
        elem = reg[ref]
        box  = await _get_box(cdp, elem.backend_node_id)
        if box:
            cx, cy = box
            await cdp.send("Input.dispatchMouseEvent", {
                "type": "mouseMoved", "x": cx, "y": cy,
                "button": "none", "modifiers": 0,
            })
            await asyncio.sleep(0.7)
            return await _take_snapshot(page, cdp)
        return f"Could not get coordinates for [{ref}]."

    # ── CLICK ────────────────────────────────────────────────────────────────────
    if action == "click":
        if ref is None:
            return "Error: click needs ref=N"
        status = await _click_element(page, cdp, ref)
        await asyncio.sleep(0.8)
        await BrowserSession.save_state()
        snap = await _take_snapshot(page, cdp)
        return f"Clicked [{ref}] ({status}).\n\n{snap}"

    # ── FILL ─────────────────────────────────────────────────────────────────────
    if action == "fill":
        if ref is None:
            return "Error: fill needs ref=N"
        if text is None:
            return "Error: fill needs text=..."
        status = await _fill_element(page, cdp, ref, text)
        await asyncio.sleep(0.3)
        await BrowserSession.save_state()
        snap = await _take_snapshot(page, cdp)
        return f"Filled [{ref}] with {repr(text)} ({status}).\n\n{snap}"

    # ── TYPE (append) ─────────────────────────────────────────────────────────────
    if action == "type":
        if ref is None:
            return "Error: type needs ref=N"
        if text is None:
            return "Error: type needs text=..."
        reg = _REGISTRY.get(id(page), {})
        if ref not in reg:
            return f"Error: ref [{ref}] not found."
        elem = reg[ref]
        box  = await _get_box(cdp, elem.backend_node_id)
        if box:
            cx, cy = box
            await _cdp_click(cdp, cx, cy)
            await asyncio.sleep(0.15)
        else:
            await _cdp_focus(cdp, elem.backend_node_id)
            await asyncio.sleep(0.15)
        await _cdp_type(cdp, text)
        await asyncio.sleep(0.3)
        snap = await _take_snapshot(page, cdp)
        return f"Typed {repr(text)} into [{ref}].\n\n{snap}"

    # ── SELECT_OPTION ─────────────────────────────────────────────────────────────
    if action == "select_option":
        if ref is None:
            return "Error: select_option needs ref=N"
        reg = _REGISTRY.get(id(page), {})
        if ref not in reg:
            return f"Error: ref [{ref}] not found."
        elem    = reg[ref]
        # Resolve to JS object for select interaction
        obj_id  = await _cdp_resolve_node(cdp, elem.backend_node_id)
        if not obj_id:
            return f"Error: could not resolve element [{ref}]."
        try:
            if value:
                await cdp.send("Runtime.callFunctionOn", {
                    "functionDeclaration": f"function() {{ this.value = {json.dumps(value)}; this.dispatchEvent(new Event('change', {{bubbles:true}})); }}",
                    "objectId": obj_id,
                })
            elif text:
                await cdp.send("Runtime.callFunctionOn", {
                    "functionDeclaration": f"""function() {{
                        for (const opt of this.options) {{
                            if (opt.text.trim() === {json.dumps(text)}) {{
                                this.value = opt.value;
                                this.dispatchEvent(new Event('change', {{bubbles:true}}));
                                break;
                            }}
                        }}
                    }}""",
                    "objectId": obj_id,
                })
            snap = await _take_snapshot(page, cdp)
            return f"Selected option in [{ref}].\n\n{snap}"
        except Exception as e:
            return f"select_option error: {e}"

    # ── UPLOAD_FILE ───────────────────────────────────────────────────────────────
    if action == "upload_file":
        if ref is None:
            return "Error: upload_file needs ref=N"
        if not filepath:
            return "Error: upload_file needs filepath=..."
        reg = _REGISTRY.get(id(page), {})
        if ref not in reg:
            return f"Error: ref [{ref}] not found."
        elem = reg[ref]
        obj_id = await _cdp_resolve_node(cdp, elem.backend_node_id)
        if not obj_id:
            return f"Error: could not resolve [{ref}]."
        try:
            # Use Playwright's set_input_files via JS-resolved node
            loc = page.locator(f"[data-upload-ref]").first
            # CDP-based file input via DOM
            r = await cdp.send("DOM.resolveNode", {"backendNodeId": elem.backend_node_id})
            node_obj_id = r.get("object", {}).get("objectId")
            if node_obj_id:
                await cdp.send("DOM.setFileInputFiles", {
                    "files": [str(filepath)],
                    "backendNodeId": elem.backend_node_id,
                })
            snap = await _take_snapshot(page, cdp)
            return f"Uploaded {filepath} to [{ref}].\n\n{snap}"
        except Exception as e:
            return f"upload_file error: {e}"

    return f"Unknown action: '{action}'. See docstring for valid actions."
