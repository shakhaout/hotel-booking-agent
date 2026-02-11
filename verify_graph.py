import asyncio
import os
import sys

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.getcwd())

from src.agent_graph import create_graph, get_mcp_manager

async def main():
    print("Starting verification...")
    try:
        print("Creating graph...")
        graph = await create_graph()
        print("Graph created successfully.")
        
        print("Graph structure:")
        graph.get_graph().print_ascii()
        
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cleaning up...")
        manager = await get_mcp_manager()
        await manager.stop()
        print("Cleanup done.")

if __name__ == "__main__":
    asyncio.run(main())
