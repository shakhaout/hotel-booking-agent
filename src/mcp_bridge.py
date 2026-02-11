import asyncio
import os
import sys
from contextlib import AsyncExitStack
from typing import List, Optional, Any, Dict, Type

from langchain_core.tools import StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import create_model, Field

class MCPClientManager:
    """
    Manages the connection to a local MCP server and exposes its tools to LangChain.
    """
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def start(self):
        """Starts the MCP server subprocess and initializes the client session."""
        env = os.environ.copy()
        # Add the directory containing 'src' to PYTHONPATH to ensure imports work
        # Assuming server.py is inside 'src/', so we need the parent of 'src/'
        src_parent = os.path.dirname(os.path.dirname(os.path.abspath(self.server_script_path)))
        python_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{src_parent}{os.pathsep}{python_path}" if python_path else src_parent

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script_path],
            env=env,
        )

        # Start the stdio client
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        
        # Initialize the session
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        
        await self.session.initialize()

    async def stop(self):
        """Stops the client session and the server subprocess."""
        await self.exit_stack.aclose()
        self.session = None

    async def get_tools(self) -> List[StructuredTool]:
        """Discovers tools from the MCP server and converts them to LangChain tools."""
        if not self.session:
            raise RuntimeError("MCP Client not started. Call start() first.")

        result = await self.session.list_tools()
        tools = []

        for tool in result.tools:
            tools.append(self._create_langchain_tool(tool))
            
        return tools

    def _create_langchain_tool(self, mcp_tool) -> StructuredTool:
        """Converts an MCP tool definition to a LangChain StructuredTool."""
        # Create Pydantic model from inputSchema
        schema = mcp_tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        fields = {}
        for name, prop in properties.items():
            prop_type = Any
            if prop.get("type") == "string":
                prop_type = str
            elif prop.get("type") == "integer":
                prop_type = int
            elif prop.get("type") == "boolean":
                prop_type = bool
            elif prop.get("type") == "number":
                prop_type = float
            
            # Simple handling of defaults and required
            if name in required:
                fields[name] = (prop_type, Field(description=prop.get("description", "")))
            else:
                default_val = prop.get("default", None)
                # If default is not None, use it. If it is None, make it Optional.
                # However, for Pydantic v2, we should be careful.
                # Let's use Optional for everything not required.
                fields[name] = (Optional[prop_type], Field(default=default_val, description=prop.get("description", "")))

        # Create the Pydantic model
        args_schema = create_model(f"{mcp_tool.name}Schema", **fields)

        async def _tool_func(**kwargs):
            if not self.session:
                raise RuntimeError("MCP Client is not connected.")
            # Call the tool via MCP session
            result = await self.session.call_tool(mcp_tool.name, arguments=kwargs)
            
            # Extract text content from the result
            text_content = []
            if result.content:
                for item in result.content:
                    if item.type == "text":
                        text_content.append(item.text)
            
            return "\n".join(text_content)

        return StructuredTool.from_function(
            func=None,
            coroutine=_tool_func,
            name=mcp_tool.name,
            description=mcp_tool.description,
            args_schema=args_schema,
        )
