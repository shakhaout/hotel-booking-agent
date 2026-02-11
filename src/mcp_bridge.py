import asyncio
import os
import sys
from contextlib import AsyncExitStack
from typing import List, Optional, Any, Dict

from langchain_core.tools import StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import create_model, Field

class MCPClientManager:
    """
    Manages the lifecycle of the MCP Client connection and dynamically 
    converts MCP tools into LangChain/GenAI compatible tools.
    """
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Establishes the stdio connection to the MCP server."""
        # 1. Setup Environment
        # Get the absolute path to the 'src' directory
        server_dir = os.path.dirname(os.path.abspath(self.server_script_path))
        # Get the Project Root (one level up from src)
        project_root = os.path.dirname(server_dir)
        
        env = os.environ.copy()
        # Add Project Root to PYTHONPATH so 'from src.tools...' works
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = project_root + os.pathsep + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = project_root

        # 2. Define Server Parameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script_path],
            env=env
        )

        # 3. Connect via Standard IO
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        
        await self.session.initialize()
        print(f"✅ Connected to MCP Server")

    async def disconnect(self):
        """Clean shutdown."""
        try:
            await self.exit_stack.aclose()
        except RuntimeError:
            # Ignore RuntimeError: Attempted to exit cancel scope... during shutdown
            pass
        print("🛑 Disconnected from MCP Server")

    async def get_langchain_tools(self) -> List[StructuredTool]:
        """
        Dynamically fetches MCP tools and converts them to LangChain StructuredTools.
        """
        if not self.session:
            await self.connect()

        mcp_list = await self.session.list_tools()
        langchain_tools = []

        for mcp_tool in mcp_list.tools:
            # --- 1. Build Pydantic Model for Arguments ---
            input_schema = mcp_tool.inputSchema
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            fields = {}
            for name, prop in properties.items():
                py_type = str 
                t = prop.get("type")
                if t == "integer": py_type = int
                elif t == "number": py_type = float
                elif t == "boolean": py_type = bool
                elif t == "array": py_type = list
                elif t == "object": py_type = dict
                
                desc = prop.get("description", "")
                
                if name in required:
                    fields[name] = (py_type, Field(description=desc))
                else:
                    fields[name] = (Optional[py_type], Field(default=None, description=desc))

            # Create the dynamic Pydantic model
            ArgsModel = create_model(f"{mcp_tool.name}_args", **fields)

            # --- 2. Define Execution Logic ---
            async def _executor(tool_name=mcp_tool.name, **kwargs):
                if not self.session:
                    raise RuntimeError("MCP Session disconnected")
                
                result = await self.session.call_tool(tool_name, arguments=kwargs)
                text_content = [c.text for c in result.content if c.type == 'text']
                return "\n".join(text_content)

            # --- 3. Create LangChain Tool ---
            tool = StructuredTool.from_function(
                func=None,
                coroutine=_executor,
                name=mcp_tool.name,
                description=mcp_tool.description,
                args_schema=ArgsModel
            )
            langchain_tools.append(tool)

        return langchain_tools