import asyncio
from typing import Annotated, Literal, TypedDict
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.mcp_bridge import MCPClientManager

# Define the state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Global manager instance (lazy loaded or initialized via function)
_mcp_manager = None

async def get_mcp_manager():
    global _mcp_manager
    if _mcp_manager is None:
        # Assuming server.py is in the same directory as this file or configured path
        # Adjust path as necessary
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        server_path = os.path.join(current_dir, "server.py")
        
        _mcp_manager = MCPClientManager(server_path)
        await _mcp_manager.start()
    return _mcp_manager

async def create_graph():
    """Asynchronously creates and compiles the graph with MCP tools loaded."""
    manager = await get_mcp_manager()
    tools = await manager.get_tools()
    
    # Initialize LLM
    # Ensure GOOGLE_API_KEY is in environment variables
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Define nodes
    async def chatbot(state: AgentState):
        print("Invoking LLM...")
        response = await llm_with_tools.ainvoke(state["messages"])
        print("LLM responded.")
        return {"messages": [response]}
    
    # Define the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("chatbot", chatbot)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "chatbot")
    
    # Conditional edge
    def should_continue(state: AgentState) -> Literal["tools", END]:
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END
    
    workflow.add_conditional_edges("chatbot", should_continue)
    workflow.add_edge("tools", "chatbot")
    
    return workflow.compile()

# Sync wrapper if needed, but for now we provide the async builder.
# To use this in a sync context (like various LangGraph runners), one might need a different setup.
# But for a "professional architecture", async is preferred.
