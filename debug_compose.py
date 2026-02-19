"""Final compose test — all 3 fields."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tools.skills.browser.browser import BrowserSession, _take_snapshot, _fill_element, _ax_snapshot, _build_registry, _REGISTRY, _cdp_key

async def main():
    page, cdp = await BrowserSession.get_page()
    await page.goto("https://mail.google.com/mail/u/0/#inbox?compose=new", wait_until="domcontentloaded")
    await asyncio.sleep(3.0)

    nodes = await _ax_snapshot(cdp)
    reg, rows = _build_registry(nodes)
    _REGISTRY[id(page)] = reg

    print(f"Registered elements: {len(rows)}")
    for r in rows:
        print(f"  [{r['ref']:>3}] {r['role']:<14} {repr(r['name'])[:60]}")

    to_ref   = next((r for r in rows if 'to' in r['name'].lower() and r['role'] in ('combobox','textbox','searchbox')), None)
    subj_ref = next((r for r in rows if 'subject' in r['name'].lower()), None)
    body_ref = next((r for r in rows if 'message body' in r['name'].lower()), None)
    send_ref = next((r for r in rows if 'send' in r['name'].lower() and r['role'] == 'button'), None)

    print(f"\nTo:      {to_ref}")
    print(f"Subject: {subj_ref}")
    print(f"Body:    {body_ref}")
    print(f"Send:    {send_ref}")

    if to_ref:
        st = await _fill_element(page, cdp, to_ref['ref'], "udaysagarm@gmail.com")
        print(f"To fill: {st}")
        await asyncio.sleep(0.4)
        await _cdp_key(cdp, "Tab")
        await asyncio.sleep(0.4)

    if subj_ref:
        st = await _fill_element(page, cdp, subj_ref['ref'], "CDP Test Email")
        print(f"Subject fill: {st}")
        await asyncio.sleep(0.3)

    if body_ref:
        st = await _fill_element(page, cdp, body_ref['ref'], "This works via CDP Input.insertText!")
        print(f"Body fill: {st}")
        await asyncio.sleep(0.3)

    print("\nCheck browser window — all 3 fields should be filled.")
    await asyncio.sleep(5)

asyncio.run(main())
