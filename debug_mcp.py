import asyncio
import os
import sys

sys.path.append(os.getcwd())

from src.mcp_bridge import MCPClientManager

async def main():
    print("Initializing manager...")
    server_path = os.path.join(os.getcwd(), "src", "server.py")
    manager = MCPClientManager(server_path)
    try:
        print("Starting server...")
        await manager.start()
        print("Server started. Listing tools...")
        tools = await manager.get_tools()
        print(f"Found {len(tools)} tools:")
        for t in tools:
            print(f"- {t.name}: {t.description}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
