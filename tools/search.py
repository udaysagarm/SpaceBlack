
import os
import json
from langchain_community.tools import BraveSearch, DuckDuckGoSearchRun
from langchain_core.tools import tool

@tool
def web_search(query: str):
    """
    Performs a web search using Brave Search or DuckDuckGo.
    Useful for finding general information, news, or documentation.
    
    IMPORTANT: Do NOT use this tool if the user provides a specific URL (e.g., "http://..." or "example.com"). 
    For specific URLs, use the `visit_page` tool instead.
    """
    try:
        # Determine provider from config
        provider = "brave" # Default
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    data = json.load(f)
                    provider = data.get("search_provider", "brave")
            except: pass
            
        if provider == "duckduckgo":
            search = DuckDuckGoSearchRun()
            return search.run(query)
            
        # Default to Brave
        api_key = os.environ.get("BRAVE_API_KEY")
        if not api_key:
             # Fallback if key missing but brave selected
             return "Error: BRAVE_API_KEY not found. Please set it in /config or switch to DuckDuckGo."
             
        search = BraveSearch.from_api_key(api_key=api_key, search_kwargs={"count": 3})
        return search.run(query)
    except Exception as e:
        return f"Search failed: {str(e)}"
