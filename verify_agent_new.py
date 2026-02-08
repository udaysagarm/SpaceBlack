
import os
import time
from langchain_core.messages import HumanMessage
# Updated import
from agent import app, SOUL_FILE, AGENTS_FILE, IDENTITY_FILE

def test_agent_memory():
    print("Starting Memory Verificaton...")
    
    # Check files exist
    files = [SOUL_FILE, AGENTS_FILE, IDENTITY_FILE]
    for f in files:
        if not os.path.exists(f):
            print(f"[FAIL] Missing file: {f}")
            return
    print("[PASS] Brain files exist.")

    # Helper to run
    def run_turn(user_input):
        print(f"\nUser: {user_input}")
        inputs = {"messages": [HumanMessage(content=user_input)]}
        result = app.invoke(inputs)
        response = result["messages"][-1].content
        print(f"Agent: {response}")
        return response

    if "OPENAI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
         print("Skipping LLM test: No API keys.")
         return

    # 1. Ask identity (should come from IDENTITY.md)
    # response = run_turn("Who are you and what is your version?")
    # if "1.0.0" in response or "Ghost" in response:
    #     print("[PASS] Identity confirmed.")
    # else:
    #     print("[WARNING] Identity not clearly retrieved.")

if __name__ == "__main__":
    test_agent_memory()
