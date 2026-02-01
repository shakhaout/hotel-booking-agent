import os
import time
import json
from dotenv import load_dotenv
# Load environment variables first
load_dotenv()

from google import genai
from google.genai import types
from src.server import mcp
from src.memory import PreferenceMemory

class HotelAgent:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.memory = PreferenceMemory()
        
        # Build Tool Definitions for GenAI SDK from FastMCP
        # We manually map them here to ensure compatibility with the V2 SDK types
        self.tools = [
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
        
        # Tool mapping for execution
        # FastMCP tools are registered in mcp._tools (internal) or we can access the decorated functions directly if we imported them.
        # But `search_hotels` is defined in src/server.py as a decorated function.
        # We can import the functions directly from src.server in the execution loop or use `mcp.call_tool` if supported?
        # FastMCP's `mcp.call_tool` is not standard public API in all versions.
        # However, the functions `search_hotels` and `book_hotel` are available in `src.server` namespace.
        from src.server import search_hotels, book_hotel
        self.tool_map = {
            "search_hotels": search_hotels,
            "book_hotel": book_hotel
        }

    def run(self):
        print("Welcome to the AI Hotel Booking Agent (FastMCP + GenAI SDK)!")
        print("Type 'quit' to exit.")
        
        # Start a chat session
        chat = self.client.chats.create(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(
                tools=self.tools,
                temperature=0.7,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True) # Manual control
            )
        )
        
        while True:
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
                        
                        print(f"Agent Calling Tool: {fn_name} with {fn_args}")
                        
                        if fn_name in self.tool_map:
                            try:
                                # Call the FastMCP decorated function
                                # Call the FastMCP decorated function via .fn
                                # FastMCP wrappers are not directly callable, but exposes .fn
                                result = self.tool_map[fn_name].fn(**fn_args)
                                print(f"Tool Result: {result}")
                            except Exception as e:
                                result = f"Error: {str(e)}"
                                print(f"Tool Error: {e}")
                            
                            # Send result back
                            response = chat.send_message(
                                types.Part.from_function_response(
                                    name=fn_name,
                                    response={"result": result}
                                )
                            )
                        else:
                            print(f"Unknown tool: {fn_name}")
                            break
                
                if response.text:
                    print(f"Agent: {response.text}")
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error: {e}")

if __name__ == "__main__":
    agent = HotelAgent()
    agent.run()
