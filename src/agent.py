import os
import asyncio
import sys
import json
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from google import genai
from google.genai import types
from src.memory import PreferenceMemory

# MCP Client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class HotelAgent:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.memory = PreferenceMemory()
        self.conversation_history = []

    async def run(self):
        print("Welcome to the AI Hotel Booking Agent (MCP Client + GenAI SDK)!")
        print("Type 'quit' to exit.")


        # server parameters
        # We assume src/server.py is executable via python
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.server"], # Run as module to fix imports
            env=os.environ.copy()
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()
                
                # List tools to build GenAI definitions
                mcp_tools = await session.list_tools()
                
                # Convert MCP tools to GenAI tools
                # This basic mapping handles the current tools. 
                # For a generic implementation, a more robust mapper is needed.
                genai_tools = []
                for tool in mcp_tools.tools:
                    # Generic Schema mapping (simplified for this task)
                    # We accept the schema as is if it follows JSON schema
                    
                    # Convert MCP inputSchema to GenAI Schema
                    # This is a bit complex as GenAI SDK has its own types.Schema
                    # For now, we manually map known tools or try to convert.
                    # Since we know the tools (search_hotels, book_hotel), we can keep the manual definitions 
                    # OR we can try to dynamically build them.
                    # Let's keep manual definitions for reliability in this specific task, 
                    # but we use the session to CALL them.
                    pass 

                # Hardcoded tool definitions for GenAI (matching server.py)
                # In a full dynamic system, we would convert `mcp_tools` to `types.Tool`.
                # For this specific refactor, we keep definitions but change execution.
                defined_tools = [
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name="search_hotels",
                                description="Searches for hotels using Google Hotels.",
                                parameters=types.Schema(
                                    type="OBJECT",
                                    properties={
                                        "query": types.Schema(type="STRING", description="Location or hotel name"),
                                        "check_in": types.Schema(type="STRING", description="Check-in date (YYYY-MM-DD)"),
                                        "check_out": types.Schema(type="STRING", description="Check-out date (YYYY-MM-DD)"),
                                    },
                                    required=["query"]
                                )
                            ),
                            types.FunctionDeclaration(
                                name="book_hotel",
                                description="Generates a booking link for a hotel.",
                                parameters=types.Schema(
                                    type="OBJECT",
                                    properties={
                                        "hotel_name": types.Schema(type="STRING", description="Name of the hotel"),
                                        "check_in": types.Schema(type="STRING", description="Check-in date (YYYY-MM-DD)"),
                                        "check_out": types.Schema(type="STRING", description="Check-out date (YYYY-MM-DD)"),
                                    },
                                    required=["hotel_name", "check_in", "check_out"]
                                )
                            )
                        ]
                    )
                ]

                chat = self.client.chats.create(
                    model="gemini-flash-latest",
                    config=types.GenerateContentConfig(
                        tools=defined_tools,
                        temperature=0.7,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                    )
                )

                while True:
                    # Use asyncio.to_thread for blocking input if needed, 
                    # but raw input() is fine for simple CLI
                    user_input = input("\nYou: ")
                    if user_input.lower() in ['quit', 'exit']:
                        break
                    
                    # 1. Retrieve Preferences
                    try:
                        relevant_prefs = self.memory.get_preferences(user_input)
                        preferences_context = "\n".join(relevant_prefs) if relevant_prefs else "No specific preferences found."
                    except Exception as e:
                        preferences_context = "Memory unavailable."

                    # 2. Construct Prompt
                    prompt = f"""
                    User Input: {user_input}
                    User Preferences: {preferences_context}
                    Task: Help the user book a hotel. Verify availability first.
                    """
                    
                    try:
                        # 3. Generate Response
                        response = chat.send_message(prompt)
                        
                        # 4. Handle Tool Calls Loop
                        while response.function_calls:
                            for fc in response.function_calls:
                                fn_name = fc.name
                                fn_args = fc.args
                                
                                print(f"Agent Calling Tool (via MCP): {fn_name} with {fn_args}")
                                
                                try:
                                    # Call tool via MCP Session
                                    result_mcp = await session.call_tool(fn_name, arguments=fn_args)
                                    # result_mcp.content is a list of TextContent or ImageContent
                                    # We combine text content
                                    result_text = ""
                                    if result_mcp.content:
                                        for content in result_mcp.content:
                                            if content.type == 'text':
                                                result_text += content.text
                                    
                                    print(f"Tool Result: {result_text}")
                                    
                                except Exception as e:
                                    result_text = f"Error: {str(e)}"
                                    print(f"Tool Error: {e}")
                                
                                # Send result back (GenAI expects simple dict or string)
                                response = chat.send_message(
                                    types.Part.from_function_response(
                                        name=fn_name,
                                        response={"result": result_text}
                                    )
                                )
                        
                        if response.text:
                            print(f"Agent: {response.text}")
                            
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        print(f"Error: {e}")

if __name__ == "__main__":
    agent = HotelAgent()
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\nGoodbye!")
