"""
browser.py — Space Black autonomous browser (OpenClaw architecture, v8)

Architecture (mirrors OpenClaw):
  1. Semantic Snapshots  — CDP Accessibility.getFullAXTree → structured text with
     both readable content AND numbered interactive refs.  The agent sees the page
     like a screen-reader: headings, paragraphs, labels, plus [ref=N] on every
     clickable/typeable element.
  2. Intelligent Waits   — networkidle / URL-change / selector-based waits replace
     dumb sleep() calls.  Every mutating action auto-waits before re-snapshotting.
  3. CDP Interaction      — Real hardware-level mouse+keyboard via Input domain.
     Click, type, key combos, drag, file upload — all via CDP, not JS hacks.
  4. Self-Healing Refs    — If a ref goes stale after navigation, the tool auto
     re-snapshots and reports the new state instead of crashing.
  5. Persistent Profiles  — user_data_dir keeps logins alive across restarts.

Single tool entry-point: browser_act(action, ...)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_core.tools import tool
from playwright.async_api import (
    Browser,
    BrowserContext,
    CDPSession,
    Page,
    Playwright,
    async_playwright,
    TimeoutError as PlaywrightTimeout,
)

log = logging.getLogger("spaceblack.browser")

# ── Paths ──────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_PROFILE_DIR = _ROOT / "brain" / "vault" / "browser_profile"
_SHOTS_DIR = _ROOT / "brain" / "screenshots"
_SHOTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────────
_MAX_SNAPSHOT_CHARS = 4000
_MAX_ELEMENTS = 80
_SMART_WAIT_TIMEOUT = 4000          # ms — networkidle fallback
_NAV_TIMEOUT = 30_000               # ms
_DEFAULT_VIEWPORT = {"width": 1366, "height": 768}

# Roles that the agent can interact with
_INTERACTIVE_ROLES = frozenset({
    "button", "link",
    "textbox", "searchbox", "combobox", "spinbutton",
    "checkbox", "radio",
    "menuitem", "menuitemcheckbox", "menuitemradio",
    "option", "tab", "switch", "treeitem",
    "slider", "listbox",
    "columnheader", "rowheader", "gridcell",
})

# Roles that provide readable context (shown as inline text in snapshot)
_CONTENT_ROLES = frozenset({
    "heading", "paragraph", "text", "statictext",
    "blockquote", "caption", "code",
    "listitem", "cell", "definition",
    "status", "alert", "log", "marquee", "timer",
    "contentinfo", "complementary", "main", "article",
    "navigation", "banner", "region", "form",
    "dialog", "alertdialog",
})

_STEALTH_JS = """\
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
window.chrome = {runtime: {}};
"""

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


# ═══════════════════════════════════════════════════════════════════════════════
#  Element Registry
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class _Elem:
    """An interactive element discovered in the AX tree or iframe."""
    backend_node_id: int
    role: str
    name: str
    value: str = ""
    description: str = ""
    frame_index: int = 0    # 0 = main frame, 1+ = child frame
    selector: str = ""      # CSS selector (used for iframe elements)


# page_id → {ref: _Elem}
_REGISTRY: Dict[int, Dict[int, _Elem]] = {}


async def _discover_iframe_elements(page: Page, registry: Dict[int, _Elem], start_ref: int) -> Tuple[Dict[int, _Elem], List[str], int]:
    """
    Discover interactive elements inside ALL iframes using Playwright JS.
    Returns updated registry, snapshot lines, and next ref counter.
    Works on any site — email clients, banking, embedded apps, SPAs.
    """
    lines: List[str] = []
    ref = start_ref

    for fi, frame in enumerate(page.frames):
        if fi == 0:
            continue  # Main frame handled by AX tree
        try:
            elements = await asyncio.wait_for(
                frame.evaluate("""() => {
                    const results = [];
                    const selectors = 'a[href], button, input, textarea, select, ' +
                        '[role="button"], [role="link"], [role="menuitem"], [role="tab"], ' +
                        '[role="checkbox"], [role="radio"], [role="switch"], [role="textbox"], ' +
                        '[role="searchbox"], [role="combobox"], [contenteditable="true"]';
                    const els = document.querySelectorAll(selectors);
                    for (const el of els) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;
                        if (el.offsetParent === null && getComputedStyle(el).position !== 'fixed') continue;

                        const role = el.getAttribute('role') || el.tagName.toLowerCase();
                        const name = (el.getAttribute('aria-label') ||
                                      el.textContent?.trim()?.slice(0, 80) || '');
                        const value = el.value || '';
                        const type = el.getAttribute('type') || '';

                        // Build a unique selector
                        let sel = '';
                        if (el.id) {
                            sel = '#' + CSS.escape(el.id);
                        } else {
                            const tag = el.tagName.toLowerCase();
                            const ariaLabel = el.getAttribute('aria-label');
                            if (ariaLabel) {
                                sel = tag + '[aria-label="' + ariaLabel.replace(/"/g, '\\"') + '"]';
                            } else if (el.name) {
                                sel = tag + '[name="' + el.name.replace(/"/g, '\\"') + '"]';
                            } else if (el.className && typeof el.className === 'string') {
                                const cls = el.className.trim().split(/\\s+/).filter(Boolean).slice(0, 3).join('.');
                                sel = tag + (cls ? '.' + cls : '');
                            } else {
                                sel = tag;
                            }
                            // Add nth-of-type if needed for uniqueness
                            const matches = document.querySelectorAll(sel);
                            if (matches.length > 1) {
                                const idx = Array.from(matches).indexOf(el);
                                sel += ':nth-of-type(' + (idx + 1) + ')';
                            }
                        }

                        results.push({ role, name, value, type, selector: sel });
                    }
                    return results.slice(0, 50);
                }"""),
                timeout=5.0,
            )

            if not elements:
                continue

            # Add a frame header
            frame_url = frame.url[:60] if frame.url else "(embedded)"
            lines.append(f"\n── Frame [{fi}]: {frame_url} ──")

            for el_data in elements:
                if ref >= start_ref + _MAX_ELEMENTS:
                    break
                ref += 1
                role = el_data.get("role", "element")
                name = el_data.get("name", "")
                value = el_data.get("value", "")
                selector = el_data.get("selector", "")
                el_type = el_data.get("type", "")

                registry[ref] = _Elem(
                    backend_node_id=0,  # Not available for iframe elements
                    role=role,
                    name=name,
                    value=value,
                    frame_index=fi,
                    selector=selector,
                )

                label = role.capitalize()
                detail = repr(name) if name else "(no label)"
                if el_type:
                    detail += f" type={el_type}"
                if value and role in ("input", "textarea", "textbox", "searchbox"):
                    detail += f" value={repr(value[:30])}"
                lines.append(f"  [{ref:>3}] {label}: {detail}")

        except Exception as e:
            log.debug("iframe element discovery failed for frame %d: %s", fi, e)
            continue

    return registry, lines, ref


# ═══════════════════════════════════════════════════════════════════════════════
#  AX Tree Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _ax_prop(node: dict, prop_name: str) -> str:
    """Extract a named property value from an AX node."""
    for p in node.get("properties", []):
        if p.get("name") == prop_name:
            v = p.get("value", {})
            if isinstance(v, dict):
                return str(v.get("value", "")).strip()
            return str(v).strip()
    return ""


def _ax_role(node: dict) -> str:
    rv = node.get("role", {})
    if isinstance(rv, dict):
        return (rv.get("value") or "").lower().strip()
    return (rv or "").lower().strip()


def _ax_name(node: dict) -> str:
    nv = node.get("name", {})
    if isinstance(nv, dict):
        return (nv.get("value") or "").strip()
    return (nv or "").strip()


def _ax_value(node: dict) -> str:
    vv = node.get("value", {})
    if isinstance(vv, dict):
        return (vv.get("value") or "").strip()
    return (vv or "").strip()


def _ax_backend_id(node: dict) -> Optional[int]:
    bid = node.get("backendDOMNodeId")
    return int(bid) if bid else None


def _ax_ignored(node: dict) -> bool:
    return bool(node.get("ignored", False))


def _ax_children_ids(node: dict) -> List[str]:
    return [c.get("nodeId", "") for c in node.get("childIds", [])] if "childIds" in node else node.get("childIds", [])


# ═══════════════════════════════════════════════════════════════════════════════
#  Snapshot Builder — The Core
# ═══════════════════════════════════════════════════════════════════════════════

async def _get_ax_tree(cdp: CDPSession) -> List[dict]:
    """Fetch the full accessibility tree via CDP (main frame only)."""
    try:
        result = await asyncio.wait_for(
            cdp.send("Accessibility.getFullAXTree", {}),
            timeout=10.0,
        )
        return result.get("nodes", [])
    except Exception as e:
        log.warning("AX tree fetch failed: %s", e)
        return []


async def _extract_frames_text(page: Page, limit: int = 4000) -> str:
    """
    Extract visible text content from ALL frames (main + iframes) using JS.
    This reliably reaches dynamically loaded content inside iframes that
    the main-frame AX tree cannot see (email clients, banking apps, SPAs).
    """
    parts: List[str] = []
    total = 0
    for frame in page.frames:
        if total >= limit:
            break
        try:
            text = await asyncio.wait_for(
                frame.evaluate("""() => {
                    // Try semantic containers first, fall back to body
                    const candidates = [
                        'main', '[role="main"]', 'article', '#content',
                        '.inbox', '.message-list', '.mail-list',
                        '.email-list', 'table', '[role="grid"]',
                        '[role="list"]', '[role="tabpanel"]',
                    ];
                    let root = null;
                    for (const sel of candidates) {
                        root = document.querySelector(sel);
                        if (root) break;
                    }
                    if (!root) root = document.body;
                    return root.innerText.slice(0, 4000);
                }"""),
                timeout=3.0,
            )
            if text and len(text.strip()) > 20:
                parts.append(text.strip())
                total += len(text)
        except Exception:
            pass
    return "\n---\n".join(parts)[:limit] if parts else ""


def _build_snapshot(nodes: List[dict]) -> Tuple[Dict[int, _Elem], str]:
    """
    Walk the AX tree and produce:
      1. A registry of interactive elements (ref → _Elem)
      2. A human-readable snapshot string showing page structure

    The snapshot includes BOTH content (headings, text, labels) and
    interactive elements with [ref=N] markers — mirroring OpenClaw's
    approach of giving the agent full page comprehension.
    """
    registry: Dict[int, _Elem] = {}
    lines: List[str] = []
    ref_counter = 0
    total_chars = 0

    # Build node-id lookup for parent-child relationships
    id_to_node: Dict[str, dict] = {}
    for n in nodes:
        nid = n.get("nodeId", "")
        if nid:
            id_to_node[nid] = n

    # Track the depth of each node for indentation
    depth_map: Dict[str, int] = {}
    root_ids = []
    child_set = set()
    for n in nodes:
        for cid in n.get("childIds", []):
            child_set.add(cid)
    for n in nodes:
        nid = n.get("nodeId", "")
        if nid and nid not in child_set:
            root_ids.append(nid)

    def walk(node_id: str, depth: int):
        nonlocal ref_counter, total_chars

        if total_chars >= _MAX_SNAPSHOT_CHARS:
            return
        if ref_counter >= _MAX_ELEMENTS:
            return

        node = id_to_node.get(node_id)
        if not node:
            return
        if _ax_ignored(node):
            # Still walk children — some ignored containers have visible children
            for cid in node.get("childIds", []):
                walk(cid, depth)
            return

        role = _ax_role(node)
        name = _ax_name(node)
        value = _ax_value(node)
        backend_id = _ax_backend_id(node)
        indent = "  " * min(depth, 6)

        # ── Interactive element → assign ref ──
        if role in _INTERACTIVE_ROLES and backend_id:
            # Skip unnamed buttons/links (invisible noise)
            if not name and role in ("button", "link", "menuitem"):
                for cid in node.get("childIds", []):
                    walk(cid, depth + 1)
                return

            ref_counter += 1
            registry[ref_counter] = _Elem(
                backend_node_id=backend_id,
                role=role,
                name=name,
                value=value,
            )

            label = f"{role.capitalize()}"
            detail = repr(name) if name else "(no label)"
            if value and role in ("textbox", "searchbox", "combobox", "spinbutton"):
                detail += f" value={repr(value)}"
            elif value and role in ("checkbox", "radio", "switch"):
                detail += f" [{value}]"

            line = f"{indent}[{ref_counter:>3}] {label}: {detail}"
            lines.append(line)
            total_chars += len(line)
            # Don't recurse into interactive element children
            return

        # ── Content element → show inline text ──
        if role in _CONTENT_ROLES and name:
            if role == "heading":
                line = f"{indent}## {name}"
            elif role in ("dialog", "alertdialog"):
                line = f"{indent}⚠ DIALOG: {name}"
            elif role in ("alert", "status"):
                line = f"{indent}! {name}"
            elif role in ("navigation",):
                line = f"{indent}[nav: {name}]"
            elif role == "listitem":
                line = f"{indent}• {name}"
            else:
                line = f"{indent}{name}"

            # Truncate very long text blocks
            if len(line) > 200:
                line = line[:197] + "..."
            lines.append(line)
            total_chars += len(line)

        # ── Static text (leaf content) ──
        elif role in ("statictext", "text") and name:
            text = name[:200].strip()
            if text and len(text) > 5:
                line = f"{indent}{text}"
                lines.append(line)
                total_chars += len(line)

        # Recurse into children
        for cid in node.get("childIds", []):
            walk(cid, depth + 1)

    # Walk from roots
    for rid in root_ids:
        walk(rid, 0)

    # If tree walk produced nothing, try flat fallback
    if not lines:
        for node in nodes:
            if total_chars >= _MAX_SNAPSHOT_CHARS or ref_counter >= _MAX_ELEMENTS:
                break
            if _ax_ignored(node):
                continue
            role = _ax_role(node)
            name = _ax_name(node)
            backend_id = _ax_backend_id(node)

            if role in _INTERACTIVE_ROLES and backend_id:
                if not name and role in ("button", "link", "menuitem"):
                    continue
                ref_counter += 1
                registry[ref_counter] = _Elem(
                    backend_node_id=backend_id,
                    role=role,
                    name=name,
                    value=_ax_value(node),
                )
                line = f"[{ref_counter:>3}] {role.capitalize()}: {repr(name)}"
                lines.append(line)
                total_chars += len(line)
            elif role in _CONTENT_ROLES and name and len(name) > 3:
                prefix = "## " if role == "heading" else ""
                line = f"{prefix}{name[:200]}"
                lines.append(line)
                total_chars += len(line)

    snapshot_body = "\n".join(lines) if lines else "(empty page — no content detected)"
    return registry, snapshot_body


async def _take_snapshot(page: Page, cdp: CDPSession) -> str:
    """Build a full semantic snapshot and update the global registry."""
    try:
        title = await page.title()
    except Exception:
        title = "(unknown)"
    url = page.url

    nodes = await _get_ax_tree(cdp)
    registry, body = _build_snapshot(nodes)
    _REGISTRY[id(page)] = registry

    interactive_count = len(registry)

    # Tab list
    tab_info = ""
    try:
        ctx = page.context
        pages = ctx.pages
        if len(pages) > 1:
            tab_lines = []
            for i, p in enumerate(pages):
                marker = "→" if p == page else " "
                tab_lines.append(f"  {marker} [{i}] {p.url[:80]}")
            tab_info = "\nTabs:\n" + "\n".join(tab_lines) + "\n"
    except Exception:
        pass

    header = f"URL: {url}\nTitle: {title}{tab_info}"

    # Discover iframe interactive elements (buttons, links, inputs in iframes)
    iframe_lines: List[str] = []
    if len(page.frames) > 1:
        try:
            registry, iframe_lines, _ = await _discover_iframe_elements(page, registry, interactive_count)
            _REGISTRY[id(page)] = registry  # Update with iframe elements
        except Exception as e:
            log.debug("iframe element discovery failed: %s", e)

    total_interactive = len(registry)
    footer = f"\n({total_interactive} interactive elements. Use ref=N to interact.)"

    iframe_section = ""
    if iframe_lines:
        iframe_section = "\n" + "\n".join(iframe_lines)

    return f"{header}\n\n{body}{iframe_section}{footer}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Browser Session (Singleton)
# ═══════════════════════════════════════════════════════════════════════════════

class BrowserSession:
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _page: Optional[Page] = None
    _cdp: Optional[CDPSession] = None
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def get_page(cls) -> Tuple[Page, CDPSession]:
        async with cls._lock:
            if cls._page is None or cls._page.is_closed():
                await cls._launch()
            # Verify CDP session is still alive
            try:
                await asyncio.wait_for(
                    cls._cdp.send("Accessibility.getFullAXTree", {}),
                    timeout=3.0,
                )
            except Exception:
                # CDP session died — re-establish
                log.info("CDP session stale, re-establishing...")
                try:
                    cls._cdp = await cls._context.new_cdp_session(cls._page)
                    await cls._cdp.send("Accessibility.enable")
                except Exception as e:
                    log.error("CDP re-establish failed: %s", e)
                    await cls._launch()
            return cls._page, cls._cdp

    @classmethod
    async def _launch(cls) -> None:
        # Clean up any existing session
        if cls._browser:
            try:
                await cls._browser.close()
            except Exception:
                pass
        if cls._playwright:
            try:
                await cls._playwright.stop()
            except Exception:
                pass

        cls._playwright = await async_playwright().start()

        _PROFILE_DIR.mkdir(parents=True, exist_ok=True)

        launch_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--start-maximized",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]

        # Use persistent context for real login persistence
        cls._context = await cls._playwright.chromium.launch_persistent_context(
            user_data_dir=str(_PROFILE_DIR),
            headless=True,
            args=launch_args,
            viewport=_DEFAULT_VIEWPORT,
            user_agent=_USER_AGENT,
            locale="en-US",
            timezone_id="America/New_York",
            ignore_https_errors=True,
        )

        await cls._context.add_init_script(_STEALTH_JS)

        # Use existing page or create new one
        if cls._context.pages:
            cls._page = cls._context.pages[0]
        else:
            cls._page = await cls._context.new_page()

        cls._cdp = await cls._context.new_cdp_session(cls._page)
        await cls._cdp.send("Accessibility.enable")
        cls._browser = None  # persistent context doesn't use separate browser

    @classmethod
    async def close_all(cls) -> None:
        if cls._cdp:
            try:
                await cls._cdp.detach()
            except Exception:
                pass
        if cls._context:
            try:
                await cls._context.close()
            except Exception:
                pass
        if cls._browser:
            try:
                await cls._browser.close()
            except Exception:
                pass
        if cls._playwright:
            try:
                await cls._playwright.stop()
            except Exception:
                pass
        cls._playwright = cls._browser = cls._context = cls._page = cls._cdp = None


# ═══════════════════════════════════════════════════════════════════════════════
#  Intelligent Wait System
# ═══════════════════════════════════════════════════════════════════════════════

async def _smart_wait(page: Page, timeout_ms: int = _SMART_WAIT_TIMEOUT) -> None:
    """
    OpenClaw-style smart wait: try networkidle first, fall back to domcontentloaded,
    then a minimal sleep. Never blocks longer than timeout_ms.
    """
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PlaywrightTimeout:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=1000)
        except PlaywrightTimeout:
            pass
    # Small buffer for JS framework rendering (React, Vue, etc.)
    await asyncio.sleep(0.3)


async def _wait_for_navigation_settle(page: Page) -> None:
    """Wait after a click that might cause navigation."""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=5000)
    except PlaywrightTimeout:
        pass
    await _smart_wait(page, 3000)


# ═══════════════════════════════════════════════════════════════════════════════
#  CDP Interaction Primitives
# ═══════════════════════════════════════════════════════════════════════════════

async def _get_box(cdp: CDPSession, backend_node_id: int) -> Optional[Tuple[float, float]]:
    """Get center coordinates of an element via CDP DOM.getBoxModel."""
    try:
        # Scroll element into view first
        await cdp.send("DOM.scrollIntoViewIfNeeded", {"backendNodeId": backend_node_id})
        await asyncio.sleep(0.1)
    except Exception:
        pass

    try:
        result = await cdp.send("DOM.getBoxModel", {"backendNodeId": backend_node_id})
        box = result.get("model", {}).get("content")
        if box and len(box) >= 8:
            xs = [box[i] for i in range(0, 8, 2)]
            ys = [box[i] for i in range(1, 8, 2)]
            cx = sum(xs) / 4
            cy = sum(ys) / 4
            # Sanity check: coordinates should be within viewport
            if cx > 0 and cy > 0:
                return cx, cy
    except Exception:
        pass
    return None


async def _cdp_click(cdp: CDPSession, cx: float, cy: float) -> None:
    """Click at coordinates using real CDP mouse events (move → press → release)."""
    base = {"x": cx, "y": cy, "button": "left", "clickCount": 1, "modifiers": 0}
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mouseMoved", "buttons": 0})
    await asyncio.sleep(0.03)
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mousePressed", "buttons": 1})
    await asyncio.sleep(0.03)
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mouseReleased", "buttons": 0})


async def _cdp_focus(cdp: CDPSession, backend_node_id: int) -> bool:
    """Focus element via CDP DOM.focus. Returns True on success."""
    try:
        await cdp.send("DOM.focus", {"backendNodeId": backend_node_id})
        return True
    except Exception:
        return False


async def _cdp_type(cdp: CDPSession, text: str) -> None:
    """Insert text using CDP Input.insertText (fires real composition events)."""
    await cdp.send("Input.insertText", {"text": text})


async def _cdp_key(cdp: CDPSession, key: str) -> None:
    """
    Dispatch a key event. Supports named keys and combos:
    Tab, Enter, Escape, Backspace, Delete, ArrowDown, ArrowUp,
    Control+a, Control+Enter, Control+c, Control+v, etc.
    """
    _KEY_MAP = {
        "Tab":       ("Tab", 9, 0),
        "Enter":     ("Return", 13, 0),
        "Return":    ("Return", 13, 0),
        "Escape":    ("Escape", 27, 0),
        "Backspace": ("Backspace", 8, 0),
        "Delete":    ("Delete", 46, 0),
        "Space":     (" ", 32, 0),
        "ArrowDown": ("ArrowDown", 40, 0),
        "ArrowUp":   ("ArrowUp", 38, 0),
        "ArrowLeft": ("ArrowLeft", 37, 0),
        "ArrowRight":("ArrowRight", 39, 0),
        "Home":      ("Home", 36, 0),
        "End":       ("End", 35, 0),
        "PageUp":    ("PageUp", 33, 0),
        "PageDown":  ("PageDown", 34, 0),
        # Combos (modifier bitmask: Alt=1, Ctrl=2, Meta=4, Shift=8)
        "Control+a": ("a", 65, 2),
        "Control+c": ("c", 67, 2),
        "Control+v": ("v", 86, 2),
        "Control+x": ("x", 88, 2),
        "Control+z": ("z", 90, 2),
        "Control+Enter": ("Return", 13, 2),
        "Shift+Tab": ("Tab", 9, 8),
        "Shift+Enter": ("Return", 13, 8),
    }

    mapped = _KEY_MAP.get(key)
    if mapped:
        key_name, key_code, mods = mapped
    else:
        key_name = key
        key_code = ord(key[0]) if len(key) == 1 else 0
        mods = 0

    code = f"Key{key_name.upper()}" if len(key_name) == 1 else key_name

    for t in ("keyDown", "keyUp"):
        await cdp.send("Input.dispatchKeyEvent", {
            "type": t,
            "key": key_name,
            "windowsVirtualKeyCode": key_code,
            "nativeVirtualKeyCode": key_code,
            "modifiers": mods,
            "code": code,
            "isKeypad": False,
        })
        await asyncio.sleep(0.02)


async def _resolve_node(cdp: CDPSession, backend_node_id: int) -> Optional[str]:
    """Resolve backendNodeId to a Runtime RemoteObjectId."""
    try:
        r = await cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})
        return r.get("object", {}).get("objectId")
    except Exception:
        return None


async def _js_click(cdp: CDPSession, backend_node_id: int) -> bool:
    """Fallback: click element via JS .click()."""
    obj_id = await _resolve_node(cdp, backend_node_id)
    if not obj_id:
        return False
    try:
        await cdp.send("Runtime.callFunctionOn", {
            "functionDeclaration": "function() { this.scrollIntoView({block:'center'}); this.click(); }",
            "objectId": obj_id,
        })
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  High-Level Actions
# ═══════════════════════════════════════════════════════════════════════════════

def _get_elem(page: Page, ref: int) -> Optional[_Elem]:
    """Look up an element by ref in the registry."""
    return _REGISTRY.get(id(page), {}).get(ref)


async def _do_click(page: Page, cdp: CDPSession, ref: int) -> str:
    """Click an element — supports both main frame (CDP) and iframe (Playwright) elements."""
    elem = _get_elem(page, ref)
    if not elem:
        return f"Error: ref [{ref}] not found. Run snapshot to refresh."

    url_before = page.url

    # ── Iframe element: use Playwright frame locator ──
    if elem.frame_index > 0 and elem.selector:
        try:
            frame = page.frames[elem.frame_index]
            locator = frame.locator(elem.selector).first
            await locator.scroll_into_view_if_needed(timeout=3000)
            await locator.click(timeout=5000)
            method = "frame-click"
        except Exception as e:
            return f"Error: could not click [{ref}] in iframe ({elem.role}: {elem.name}): {e}"
    else:
        # ── Main frame: CDP click with fallbacks ──
        box = await _get_box(cdp, elem.backend_node_id)
        if box:
            cx, cy = box
            await _cdp_click(cdp, cx, cy)
            method = "cdp-click"
        else:
            if await _js_click(cdp, elem.backend_node_id):
                method = "js-click"
            else:
                if await _cdp_focus(cdp, elem.backend_node_id):
                    await _cdp_key(cdp, "Enter")
                    method = "focus-enter"
                else:
                    return f"Error: could not click [{ref}] ({elem.role}: {elem.name})"

    # Wait for potential navigation or JS update
    await asyncio.sleep(0.3)
    url_after = page.url
    if url_after != url_before:
        await _wait_for_navigation_settle(page)
    else:
        await _smart_wait(page, 2000)

    return f"Clicked [{ref}] {elem.role}: {repr(elem.name)} ({method})"


async def _do_fill(page: Page, cdp: CDPSession, ref: int, text: str) -> str:
    """Fill an element — supports both main frame (CDP) and iframe (Playwright)."""
    elem = _get_elem(page, ref)
    if not elem:
        return f"Error: ref [{ref}] not found. Run snapshot to refresh."

    # ── Iframe element: use Playwright frame locator ──
    if elem.frame_index > 0 and elem.selector:
        try:
            frame = page.frames[elem.frame_index]
            locator = frame.locator(elem.selector).first
            await locator.click(timeout=3000)
            await asyncio.sleep(0.1)
            await locator.fill(text, timeout=3000)
            await asyncio.sleep(0.15)
            return f"Filled [{ref}] {elem.role}: {repr(elem.name)} with {repr(text)}"
        except Exception as e:
            return f"Error: could not fill [{ref}] in iframe: {e}"

    # ── Main frame: CDP ──
    box = await _get_box(cdp, elem.backend_node_id)
    if box:
        cx, cy = box
        await _cdp_click(cdp, cx, cy)
        await asyncio.sleep(0.1)
    else:
        if not await _cdp_focus(cdp, elem.backend_node_id):
            return f"Error: could not focus [{ref}] ({elem.role}: {elem.name})"
        await asyncio.sleep(0.1)

    await _cdp_key(cdp, "Control+a")
    await asyncio.sleep(0.05)
    await _cdp_key(cdp, "Delete")
    await asyncio.sleep(0.05)
    await _cdp_type(cdp, text)
    await asyncio.sleep(0.15)

    return f"Filled [{ref}] {elem.role}: {repr(elem.name)} with {repr(text)}"


async def _do_type(page: Page, cdp: CDPSession, ref: int, text: str) -> str:
    """Type into an element — supports both main frame (CDP) and iframe (Playwright)."""
    elem = _get_elem(page, ref)
    if not elem:
        return f"Error: ref [{ref}] not found. Run snapshot to refresh."

    # ── Iframe element ──
    if elem.frame_index > 0 and elem.selector:
        try:
            frame = page.frames[elem.frame_index]
            locator = frame.locator(elem.selector).first
            await locator.click(timeout=3000)
            await asyncio.sleep(0.1)
            await locator.type(text, timeout=3000)
            await asyncio.sleep(0.1)
            return f"Typed {repr(text)} into [{ref}] {elem.role}: {repr(elem.name)}"
        except Exception as e:
            return f"Error: could not type into [{ref}] in iframe: {e}"

    # ── Main frame: CDP ──
    box = await _get_box(cdp, elem.backend_node_id)
    if box:
        cx, cy = box
        await _cdp_click(cdp, cx, cy)
        await asyncio.sleep(0.1)
    else:
        if not await _cdp_focus(cdp, elem.backend_node_id):
            return f"Error: could not focus [{ref}]"
        await asyncio.sleep(0.1)

    await _cdp_type(cdp, text)
    await asyncio.sleep(0.1)

    return f"Typed {repr(text)} into [{ref}] {elem.role}: {repr(elem.name)}"


async def _do_hover(page: Page, cdp: CDPSession, ref: int) -> str:
    """Hover over an element — supports both main frame and iframe."""
    elem = _get_elem(page, ref)
    if not elem:
        return f"Error: ref [{ref}] not found."

    # ── Iframe element ──
    if elem.frame_index > 0 and elem.selector:
        try:
            frame = page.frames[elem.frame_index]
            locator = frame.locator(elem.selector).first
            await locator.hover(timeout=3000)
            return f"Hovered over [{ref}] {elem.role}: {repr(elem.name)}"
        except Exception as e:
            return f"Error: could not hover [{ref}] in iframe: {e}"

    # ── Main frame: CDP ──
    box = await _get_box(cdp, elem.backend_node_id)
    if not box:
        return f"Error: could not get coordinates for [{ref}]"

    cx, cy = box
    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mouseMoved", "x": cx, "y": cy,
        "button": "none", "modifiers": 0,
    })
    await asyncio.sleep(0.5)
    return f"Hovering over [{ref}] {elem.role}: {repr(elem.name)}"


async def _do_select_option(cdp: CDPSession, page: Page, ref: int,
                             value: Optional[str], text: Optional[str]) -> str:
    """Select an option in a <select> or custom dropdown."""
    elem = _get_elem(page, ref)
    if not elem:
        return f"Error: ref [{ref}] not found."

    obj_id = await _resolve_node(cdp, elem.backend_node_id)
    if not obj_id:
        return f"Error: could not resolve [{ref}]"

    try:
        if value:
            await cdp.send("Runtime.callFunctionOn", {
                "functionDeclaration": f"""function() {{
                    this.value = {json.dumps(value)};
                    this.dispatchEvent(new Event('change', {{bubbles:true}}));
                }}""",
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
        else:
            return "Error: select_option needs value=... or text=..."
        return f"Selected option in [{ref}]"
    except Exception as e:
        return f"select_option error: {e}"


async def _do_upload(cdp: CDPSession, page: Page, ref: int, filepath: str) -> str:
    """Upload a file via CDP DOM.setFileInputFiles."""
    elem = _get_elem(page, ref)
    if not elem:
        return f"Error: ref [{ref}] not found."

    if not os.path.isfile(filepath):
        return f"Error: file not found: {filepath}"

    try:
        await cdp.send("DOM.setFileInputFiles", {
            "files": [str(filepath)],
            "backendNodeId": elem.backend_node_id,
        })
        await asyncio.sleep(0.5)
        return f"Uploaded {filepath} to [{ref}]"
    except Exception as e:
        return f"upload error: {e}"


async def _get_page_text(page: Page, cdp: CDPSession) -> str:
    """
    Extract readable page content.
    Combines AX tree text (main frame) + JS extraction from ALL frames
    for maximum content coverage on any website.
    """
    # 1. AX tree content (main frame — good for structured content)
    nodes = await _get_ax_tree(cdp)
    ax_lines: List[str] = []
    total = 0
    limit = 4000
    seen_texts = set()

    for node in nodes:
        if total >= limit:
            break
        if _ax_ignored(node):
            continue
        role = _ax_role(node)
        name = _ax_name(node)
        if not name or len(name.strip()) < 3:
            continue

        key = name.strip()[:100]
        if key in seen_texts:
            continue
        seen_texts.add(key)

        if role in ("heading",):
            line = f"## {name}"
        elif role in ("listitem",):
            line = f"\u2022 {name}"
        elif role in ("link",):
            line = f"[{name}]"
        elif role in ("statictext", "text", "paragraph", "blockquote",
                       "cell", "gridcell", "caption", "definition",
                       "contentinfo", "article", "main", "region",
                       "complementary", "group", "section"):
            line = name
        elif role in ("row",):
            line = f"| {name}"
        elif role in ("img", "image"):
            line = f"[Image: {name}]"
        elif role in ("label",):
            line = f"{name}:"
        elif role in ("status", "alert", "log"):
            line = f"! {name}"
        elif role in ("treeitem",):
            line = f"  > {name}"
        elif role in ("tab",):
            line = f"[Tab: {name}]"
        elif role in ("dialog", "alertdialog"):
            line = f"DIALOG: {name}"
        elif role in ("button",) and len(name) > 10:
            line = f"[{name}]"
        elif role in ("generic", "none", "presentation") and len(name) > 20:
            line = name
        else:
            continue

        if len(line) > 300:
            line = line[:297] + "..."
        ax_lines.append(line)
        total += len(line)

    ax_content = "\n".join(ax_lines) if ax_lines else ""

    # 2. JS extraction from ALL frames (always runs — catches iframe content)
    js_content = await _extract_frames_text(page, limit=4000)

    # 3. Merge: AX content first, then any JS content that adds new info
    if ax_content and js_content:
        return f"{ax_content}\n\n── Additional Page Content ──\n{js_content}"[:6000]
    elif js_content:
        return js_content[:6000]
    elif ax_content:
        return ax_content
    else:
        return "(empty page — no content detected)"


async def _dismiss_banners(page: Page) -> None:
    """Try to dismiss cookie/consent banners."""
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
                return
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Tool — browser_act
# ═══════════════════════════════════════════════════════════════════════════════

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
    selector:  Optional[str] = None,
) -> str:
    """
    Autonomous browser control — site-agnostic. Works on Gmail, Amazon, Reddit,
    login pages, dashboards, SPAs, and any website.

    ACTIONS:
    ────────────────────────────────────────────────────────────────────────────
    navigate       Go to URL              url="https://..."
    snapshot       Re-read page state     (no args — returns full page structure)
    get_text       Extract readable text  (no args — articles, emails, content)
    click          Click element          ref=N
    fill           Clear + fill field     ref=N, text="..."
    type           Append to field        ref=N, text="..."
    press          Keyboard key           key="Tab"/"Enter"/"Escape"/"Control+a"
    hover          Hover element          ref=N
    select_option  Pick dropdown          ref=N, value="val" OR text="Label"
    upload_file    Upload a file          ref=N, filepath="/path/to/file"
    scroll         Scroll page            direction="down"/"up", amount=600
    wait           Wait + re-snapshot     duration=2 (seconds)
    wait_for       Wait for condition     selector="#login-form" / url="**/dash"
    screenshot     Save screenshot        (no args)
    back           Browser back           (no args)
    forward        Browser forward        (no args)
    new_tab        Open new tab           url="https://..."
    switch_tab     Change tab             index=N
    close_tab      Close current tab      (no args)
    close          Close browser          (no args)
    ────────────────────────────────────────────────────────────────────────────

    WORKFLOW (how to browse autonomously):
      1. navigate to URL → read the snapshot
      2. Understand the page structure from headings and text
      3. Find the element you need by ref number
      4. click/fill/type using ref=N
      5. Read the new snapshot returned after each action
      6. Repeat until task is complete

    TIPS:
      • Every action returns a fresh snapshot — no need to call snapshot separately
      • Use fill (not type) for input fields — it clears first
      • After clicking a link/button, the snapshot shows the NEW page
      • Use wait_for when you need a specific element to appear (SPAs, slow pages)
      • Use get_text for reading article content, emails, long text
    """
    action = action.lower().strip()

    # ── CLOSE ──────────────────────────────────────────────────────────────
    if action == "close":
        await BrowserSession.close_all()
        return "Browser closed."

    # Get page (auto-launches if needed)
    try:
        page, cdp = await BrowserSession.get_page()
    except Exception as e:
        return f"Browser launch failed: {e}\n{traceback.format_exc()}"

    try:
        return await _dispatch(action, page, cdp,
                               url=url, ref=ref, text=text, value=value,
                               filepath=filepath, direction=direction,
                               amount=amount, duration=duration, key=key,
                               index=index, selector=selector)
    except Exception as e:
        log.error("browser_act error: %s", traceback.format_exc())
        # Try to recover with a fresh snapshot
        try:
            snap = await _take_snapshot(page, cdp)
            return f"Error during '{action}': {e}\n\nCurrent page state:\n{snap}"
        except Exception:
            return f"Error during '{action}': {e}"


async def _dispatch(action: str, page: Page, cdp: CDPSession, **kw) -> str:
    """Dispatch to the appropriate action handler."""

    # ── NAVIGATE ───────────────────────────────────────────────────────────
    if action == "navigate":
        url = kw.get("url")
        if not url:
            return "Error: navigate needs url=..."
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT)
            await _smart_wait(page)
            await _dismiss_banners(page)
        except PlaywrightTimeout:
            pass  # Page may still be usable
        except Exception as e:
            return f"Navigation error: {e}"
        snap = await _take_snapshot(page, cdp)
        return f"Navigated to {url}\n\n{snap}"

    # ── SNAPSHOT ───────────────────────────────────────────────────────────
    if action == "snapshot":
        return await _take_snapshot(page, cdp)

    # ── GET_TEXT ────────────────────────────────────────────────────────────
    if action == "get_text":
        title = await page.title()
        content = await _get_page_text(page, cdp)
        return f"URL: {page.url}\nTitle: {title}\n\n{content}"

    # ── CLICK ──────────────────────────────────────────────────────────────
    if action == "click":
        ref = kw.get("ref")
        if ref is None:
            return "Error: click needs ref=N"
        result = await _do_click(page, cdp, ref)
        snap = await _take_snapshot(page, cdp)
        return f"{result}\n\n{snap}"

    # ── FILL ───────────────────────────────────────────────────────────────
    if action == "fill":
        ref, text = kw.get("ref"), kw.get("text")
        if ref is None:
            return "Error: fill needs ref=N"
        if text is None:
            return "Error: fill needs text=..."
        result = await _do_fill(page, cdp, ref, text)
        snap = await _take_snapshot(page, cdp)
        return f"{result}\n\n{snap}"

    # ── TYPE ───────────────────────────────────────────────────────────────
    if action == "type":
        ref, text = kw.get("ref"), kw.get("text")
        if ref is None:
            return "Error: type needs ref=N"
        if text is None:
            return "Error: type needs text=..."
        result = await _do_type(page, cdp, ref, text)
        snap = await _take_snapshot(page, cdp)
        return f"{result}\n\n{snap}"

    # ── PRESS ──────────────────────────────────────────────────────────────
    if action == "press":
        key = kw.get("key")
        if not key:
            return "Error: press needs key=..."
        await _cdp_key(cdp, key)
        await asyncio.sleep(0.3)
        snap = await _take_snapshot(page, cdp)
        return f"Pressed {key}\n\n{snap}"

    # ── HOVER ──────────────────────────────────────────────────────────────
    if action == "hover":
        ref = kw.get("ref")
        if ref is None:
            return "Error: hover needs ref=N"
        result = await _do_hover(page, cdp, ref)
        snap = await _take_snapshot(page, cdp)
        return f"{result}\n\n{snap}"

    # ── SELECT_OPTION ──────────────────────────────────────────────────────
    if action == "select_option":
        ref = kw.get("ref")
        if ref is None:
            return "Error: select_option needs ref=N"
        result = await _do_select_option(cdp, page, ref, kw.get("value"), kw.get("text"))
        snap = await _take_snapshot(page, cdp)
        return f"{result}\n\n{snap}"

    # ── UPLOAD_FILE ────────────────────────────────────────────────────────
    if action == "upload_file":
        ref = kw.get("ref")
        filepath = kw.get("filepath")
        if ref is None:
            return "Error: upload_file needs ref=N"
        if not filepath:
            return "Error: upload_file needs filepath=..."
        result = await _do_upload(cdp, page, ref, filepath)
        snap = await _take_snapshot(page, cdp)
        return f"{result}\n\n{snap}"

    # ── SCROLL ─────────────────────────────────────────────────────────────
    if action == "scroll":
        direction = kw.get("direction", "down")
        amount = kw.get("amount", 600)
        dy = -(amount) if direction == "up" else amount
        await page.mouse.wheel(0, dy)
        await asyncio.sleep(0.4)
        snap = await _take_snapshot(page, cdp)
        return f"Scrolled {direction} {amount}px\n\n{snap}"

    # ── WAIT ───────────────────────────────────────────────────────────────
    if action == "wait":
        duration = kw.get("duration", 2)
        await asyncio.sleep(duration)
        snap = await _take_snapshot(page, cdp)
        return f"Waited {duration}s\n\n{snap}"

    # ── WAIT_FOR (OpenClaw power-up) ───────────────────────────────────────
    if action == "wait_for":
        selector = kw.get("selector")
        url = kw.get("url")
        timeout = (kw.get("duration") or 10) * 1000

        try:
            if selector:
                await page.wait_for_selector(selector, timeout=timeout)
            elif url:
                await page.wait_for_url(url, timeout=timeout)
            else:
                await page.wait_for_load_state("networkidle", timeout=timeout)
        except PlaywrightTimeout:
            pass

        snap = await _take_snapshot(page, cdp)
        return f"Wait complete\n\n{snap}"

    # ── SCREENSHOT ─────────────────────────────────────────────────────────
    if action == "screenshot":
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(_SHOTS_DIR / f"shot_{ts}.png")
        await page.screenshot(path=path, full_page=False)
        return f"Screenshot saved: {path}"

    # ── BACK / FORWARD ─────────────────────────────────────────────────────
    if action == "back":
        await page.go_back(wait_until="domcontentloaded", timeout=10000)
        await _smart_wait(page)
        snap = await _take_snapshot(page, cdp)
        return f"Went back\n\n{snap}"

    if action == "forward":
        await page.go_forward(wait_until="domcontentloaded", timeout=10000)
        await _smart_wait(page)
        snap = await _take_snapshot(page, cdp)
        return f"Went forward\n\n{snap}"

    # ── TAB MANAGEMENT ─────────────────────────────────────────────────────
    if action == "new_tab":
        url = kw.get("url")
        if not url:
            return "Error: new_tab needs url=..."
        ctx = BrowserSession._context
        if not ctx:
            return "Error: no browser context"
        new_page = await ctx.new_page()
        BrowserSession._page = new_page
        BrowserSession._cdp = await ctx.new_cdp_session(new_page)
        await BrowserSession._cdp.send("Accessibility.enable")
        try:
            await new_page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT)
            await _smart_wait(new_page)
        except PlaywrightTimeout:
            pass
        snap = await _take_snapshot(new_page, BrowserSession._cdp)
        return f"Opened new tab: {url}\n\n{snap}"

    if action == "switch_tab":
        ctx = BrowserSession._context
        if not ctx:
            return "Error: no browser context"
        pages = ctx.pages
        idx = kw.get("index", 0) or 0
        if idx < 0 or idx >= len(pages):
            return f"Error: tab index {idx} out of range (0–{len(pages)-1})"
        BrowserSession._page = pages[idx]
        BrowserSession._cdp = await ctx.new_cdp_session(pages[idx])
        await BrowserSession._cdp.send("Accessibility.enable")
        snap = await _take_snapshot(pages[idx], BrowserSession._cdp)
        return f"Switched to tab [{idx}]\n\n{snap}"

    if action == "close_tab":
        ctx = BrowserSession._context
        if not ctx:
            return "Error: no browser context"
        await page.close()
        remaining = ctx.pages
        if remaining:
            BrowserSession._page = remaining[-1]
            BrowserSession._cdp = await ctx.new_cdp_session(remaining[-1])
            await BrowserSession._cdp.send("Accessibility.enable")
            snap = await _take_snapshot(remaining[-1], BrowserSession._cdp)
            return f"Tab closed\n\n{snap}"
        return "Tab closed. No remaining tabs."

    return f"Unknown action: '{action}'. Valid: navigate, snapshot, get_text, click, fill, type, press, hover, select_option, upload_file, scroll, wait, wait_for, screenshot, back, forward, new_tab, switch_tab, close_tab, close"
