
import asyncio
from tools.skills.browser.browser import visit_page

async def main():
    print("🌍 Visiting a dynamic website (udaysagar.com)...")
    # This page is simple, but the tool processes it like any complex site
    result = await visit_page.ainvoke({"url": "https://udaysagar.com"})
    
    print("\n✅ Extracted Content:")
    print("-" * 40)
    print(result)
    print("-" * 40)
    
    print("\n🚀 What just happened:")
    print("1. The agent launched a hidden Chrome browser.")
    print("2. It navigated to the URL.")
    print("3. It rendered the JavaScript (if any).")
    print("4. It converted the visual page into this clean Markdown text.")

if __name__ == "__main__":
    asyncio.run(main())
