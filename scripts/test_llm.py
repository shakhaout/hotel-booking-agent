import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

async def main():
    print("Initializing LLM...")
    try:
        # Try without tools first
        llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
        print("Invoking LLM with 'Hello'...")
        response = await llm.ainvoke([HumanMessage(content="Hello")])
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Tool Binding Test ---")
    try:
        from langchain_core.tools import tool
        @tool
        def add(a: int, b: int) -> int:
            """Adds a and b."""
            return a + b

        llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
        llm_with_tools = llm.bind_tools([add])
        print("Invoking LLM with tools...")
        response = await llm_with_tools.ainvoke([HumanMessage(content="What is 5 + 5?")])
        print(f"Response: {response.content}")
        print(f"Tool Calls: {response.tool_calls}")
    except Exception as e:
        print(f"Tool Test Error: {e}")

    print("\n--- Direct SDK Test ---")
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        print("Model: gemini-2.0-flash")
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents="Hello"
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Direct SDK Error: {e}")

import logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    asyncio.run(main())
