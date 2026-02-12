
import sys
import os
from langchain_core.messages import HumanMessage

sys.path.append(os.getcwd())

try:
    from agent import app as agent_app
    print("Agent imported successfully.")
    
    inputs = {"messages": [HumanMessage(content="Hello, are you working?")]}
    print("Invoking agent...")
    result = agent_app.invoke(inputs)
    print("Agent responded:")
    print(result["messages"][-1].content)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
