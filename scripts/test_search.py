from duckduckgo_search import DDGS
import sys

print("Python executable:", sys.executable)

try:
    print("Testing DDGS directly...")
    with DDGS() as ddgs:
        results = [r for r in ddgs.text("python programming", max_results=2)]
        print(f"Direct Search Success! Found {len(results)} results.")
        print(f"First result: {results[0]}")
except Exception as e:
    print(f"Direct DDGS error: {e}")
    import traceback
    traceback.print_exc()

print("-" * 20)

try:
    from langchain_community.tools import DuckDuckGoSearchRun
    print("Testing LangChain Wrapper...")
    search = DuckDuckGoSearchRun()
    res = search.invoke("test")
    print(f"LangChain Wrapper Success! Result: {res[:50]}...")
except Exception as e:
    print(f"LangChain Wrapper error: {e}")
