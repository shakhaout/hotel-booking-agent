import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from src.agent_graph import create_graph, get_mcp_manager
from langchain_core.messages import HumanMessage

async def main():
    print("Initializing agent...")
    graph = await create_graph()
    
    # Initialize chat history
    messages = []
    
    print("\n--- Hotel Agent Ready ---\nType 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            query = input("User: ")
            if query.lower() in ["quit", "exit"]:
                break
                
            messages.append(HumanMessage(content=query))
            inputs = {"messages": messages}
            
            print("Agent working...")
            # Stream the updates from the graph
            async for output in graph.astream(inputs, stream_mode="values"):
                for key, value in output.items():
                    # The graph state has 'messages', we print the last one
                    if key == "messages":
                        last_msg = value[-1]
                        # Only print if it's a new message or from AI/Tool
                        if last_msg not in messages:
                             # In a real app we'd be more careful with deduping, but for this script:
                             # The graph returns the FULL state, so 'value' is list of messages.
                             # We just want to see the new ones. 
                             # Actually, graph.astream(mode="values") yields the state at each node.
                             pass

            # After graph execution, let's look at the FINAL state to print the response
            # But astream is streaming intermediate states.
            # A better way for interactive chat is to use 'invoke' or carefully parse stream.
            # Let's use invoke for simplicity in this loop, or just print the last message from the last chunk.
            
            # Re-invoking graph with full history?
            # StateGraph is functional. If we pass "messages": messages, it uses them.
            # The output of graph.invoke will contain the updated history.
            
            result = await graph.ainvoke(inputs)
            messages = result["messages"] # Update history with new messages
            
            # Print the last message from AI
            last_msg = messages[-1]
            if isinstance(last_msg.content, list):
                # Handle multi-part content (text + tool use) if any
                for part in last_msg.content:
                     if isinstance(part, dict) and "text" in part:
                         print(f"Agent: {part['text']}")
            else:
                print(f"Agent: {last_msg.content}")

        except Exception as e:
            print(f"Error running agent: {e}")
            import traceback
            traceback.print_exc()
            break
            
    print("\nCleaning up...")
    manager = await get_mcp_manager()
    await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
