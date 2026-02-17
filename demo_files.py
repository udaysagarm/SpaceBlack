
import asyncio
from langchain_core.messages import HumanMessage
from agent import app

async def main():
    print("🤖 Testing Direct File Tools...")
    
    # 1. Test Write
    print("\n--- Testing write_file ---")
    write_msg = "Create a file named 'hello_world.txt' in the current directory with the content 'Hello from Python tools!' using the write_file tool."
    print(f"User: {write_msg}")
    result = await app.ainvoke({"messages": [HumanMessage(content=write_msg)]})
    print(f"Agent: {result['messages'][-1].content}")

    # 2. Test Read
    print("\n--- Testing read_file ---")
    read_msg = "Read the content of 'hello_world.txt' using the read_file tool."
    print(f"User: {read_msg}")
    result = await app.ainvoke({"messages": [HumanMessage(content=read_msg)]})
    print(f"Agent: {result['messages'][-1].content}")

    # 3. Test List
    print("\n--- Testing list_directory ---")
    list_msg = "List the files in the current directory using the list_directory tool."
    print(f"User: {list_msg}")
    result = await app.ainvoke({"messages": [HumanMessage(content=list_msg)]})
    print(f"Agent: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
