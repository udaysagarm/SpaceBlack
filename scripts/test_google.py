from googlesearch import search
import sys

print("Python executable:", sys.executable)

try:
    print("Testing googlesearch...")
    # num_results argument depends on the exact package installed (googlesearch-python vs google)
    # googlesearch-python uses 'num_results', google uses 'num' or 'stop'
    # Let's try flexible call
    results = search("python programming", advanced=True, num_results=5)
    for result in results:
        print(result.title)
        print(result.description)
        print(result.url)
        print("-" * 10)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
