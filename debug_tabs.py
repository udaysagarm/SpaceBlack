import asyncio
from tools.skills.browser.interactive_browser import BrowserSession, browser_go_to, browser_get_state

async def debug_tabs():
    print("--- 1. Initialization ---")
    page = await BrowserSession.get_page()
    
    print("--- 2. Simulating 'Junk' Tabs ---")
    # Manually open a new page (simulating a popup or previous session)
    page2 = await page.context.new_page()
    await page2.goto("https://www.google.com")
    print("Opened Google (Background Tab)")
    
    # Back to main page
    await page.bring_to_front()
    
    print("--- 3. Checking State BEFORE Navigation ---")
    # This should show Google as a background tab
    state = await browser_get_state.ainvoke({})
    print(state.split("--- Interactive Elements")[0]) # Just print top part
    
    print("--- 4. Navigating to Mail.com (Triggering Cleanup) ---")
    await browser_go_to.ainvoke("https://www.mail.com")
    
    print("--- 5. Checking State AFTER Navigation ---")
    # This should show ONLY Mail.com
    state = await browser_get_state.ainvoke({})
    print(state.split("--- Interactive Elements")[0])

if __name__ == "__main__":
    asyncio.run(debug_tabs())
