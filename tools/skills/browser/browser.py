
import asyncio
from langchain_core.tools import tool
from playwright.async_api import async_playwright
import html2text
from bs4 import BeautifulSoup

@tool
async def visit_page(url: str):
    """
    Visits a specific URL using a headless browser (Chromium) and returns its actual page content.
    
    CRITICAL: Use this tool WHENEVER the user provides a specific URL (e.g. "http://...", "https://...", "example.com") 
    or asks to "visit", "read", "check", "lookup", or "go to" a specific link.
    Do NOT use `web_search` for direct URLs.
    """
    try:
        async with async_playwright() as p:
            # Launch browser (headless=True is default, but making it explicit)
            browser = await p.chromium.launch(headless=True)
            
            # Create a new context with a realistic user agent to avoid basic bot blocks
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            page = await context.new_page()
            
            try:
                # Go to the page and wait for it to load
                # wait_until="domcontentloaded" is faster, "networkidle" is safer for SPAs
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                
                # Get the HTML content
                html_content = await page.content()
                
            except Exception as e:
                await browser.close()
                return f"Error visiting page: {str(e)}"
            
            await browser.close()
            
            # Parse HTML to clean it up before converting to Text
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove scripts, styles, and other non-content elements
            for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                script.extract()
            
            # Convert to Markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0  # No wrapping
            
            markdown_content = h.handle(str(soup))
            
            # Truncate if too long (to save tokens)
            if len(markdown_content) > 8000:
                markdown_content = markdown_content[:8000] + "\n\n[...Content Truncated...]"
                
            return markdown_content

    except Exception as e:
        return f"Browser Error: {str(e)}\nMake sure 'playwright install chromium' has been run."
