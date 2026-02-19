import asyncio
from tools.skills.browser.interactive_browser import BrowserSession, browser_go_to, browser_get_state, browser_screenshot

async def debug_mail():
    print("--- 1. Navigating to Mail.com ---")
    await browser_go_to.ainvoke("https://www.mail.com")
    
    print("--- 2. Waiting for potential overlays (5s) ---")
    await asyncio.sleep(5)
    
    print("--- 3. Getting Initial State ---")
    state = await browser_get_state.ainvoke({})
    print(state[:2000]) # Print top part to see interactive elements
    
    print("--- 4. Clicking 'Log in' ---")
    # We look for the button in the state, or guess the selector based on standard mail.com layout
    # Usually it's an anchor with text "Log in" or id="login-button"
    
    try:
        page = await BrowserSession.get_page()
        # Try specific ID first (common on mail.com)
        # Or try the anchor tag specifically
        login_btn = page.locator("a#login-button").or_(page.locator("a.login-button")).or_(page.locator("a[data-tracking='login']"))
        
        # If that fails, try the generic text but ensure it's visible
        if await login_btn.count() == 0:
             print("Specific ID not found, trying generic text...")
             login_btn = page.get_by_text("Log in", exact=True)
        
        if await login_btn.count() > 0:
            print(f"Found 'Log in' button: {await login_btn.first.inner_html()}")
            # Use force=True to bypass visibility check
            await login_btn.first.click(force=True)
            await asyncio.sleep(2) # Wait for animation/modal
            
            print("--- 5. Getting State AFTER Click ---")
            state_after = await browser_get_state.ainvoke({})
            print(state_after[:2000])
            
            print("--- 6. Taking Screenshot (After Click) ---")
            await browser_screenshot.ainvoke({})
            print("Screenshot saved.")
        else:
            print("Could not find 'Log in' button via Locators.")
            
    except Exception as e:
        print(f"Error interacting: {e}")

if __name__ == "__main__":
    asyncio.run(debug_mail())
