import os
import operator
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.memory import RedisMemory
from src.mcp_bridge import MCPClientManager

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    context_str: str 

class ProfessionalHotelAgent:
    def __init__(self):
        self.memory = RedisMemory()
        self.mcp_manager = MCPClientManager(server_script_path="src/server.py")
        self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

    async def build_graph(self):
        tools = await self.mcp_manager.get_langchain_tools()
        self.llm_with_tools = self.llm.bind_tools(tools)
        
        def retrieve(state: AgentState):
            last_msg = state["messages"][-1]
            if isinstance(last_msg, HumanMessage):
                context = self.memory.retrieve_context(last_msg.content)
                return {"context_str": context}
            return {"context_str": ""}

        async def chatbot(state: AgentState):
            context = state.get("context_str", "")
            system_prompt = (
                "You are a Hotel Booking Agent. Always verify availability first using 'search_hotels'.\n"
                "When you find hotels, ALWAYS providing the booking link or a 'View Details' link for the TOP 3 options immediately. "
                "Do NOT ask 'Would you like me to generate a booking link?'. Just provide it.\n"
                "If the user request is vague, ask for Location, Check-in, and Check-out dates.\n"
                f"CONTEXT:\n{context}"
            )
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = await self.llm_with_tools.ainvoke(messages)
            return {"messages": [response]}

        def save_memory(state: AgentState):
            msgs = state["messages"]
            if len(msgs) >= 2:
                last_ai = msgs[-1]
                last_human = msgs[-2]
                if isinstance(last_human, HumanMessage) and isinstance(last_ai, AIMessage):
                    self.memory.save_interaction(last_human.content, last_ai.content)
            return {}

        workflow = StateGraph(AgentState)
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("agent", chatbot)
        workflow.add_node("tools", ToolNode(tools))
        workflow.add_node("save", save_memory)

        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "agent")
        
        def should_continue(state):
            return "tools" if state["messages"][-1].tool_calls else "save"

        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")
        workflow.add_edge("save", END)

        return workflow.compile()

    async def run_interactive(self):
        print("🚀 Redis Agent Running...")
        app = await self.build_graph()
        while True:
            user_input = input("\nUser: ")
            if user_input.lower() in ["quit", "exit"]: break
            inputs = {"messages": [HumanMessage(content=user_input)]}
            async for event in app.astream(inputs, stream_mode="values"):
                msg = event["messages"][-1]
                if msg.type == "ai" and msg.content:
                    content = msg.content
                    if isinstance(content, list):
                        # Extract text from list content
                        text_parts = []
                        for part in content:
                            if isinstance(part, dict) and "text" in part:
                                text_parts.append(part["text"])
                        text = "\n".join(text_parts)
                        print(f"🤖 Agent: {text}")
                    else:
                        print(f"🤖 Agent: {content}")
        await self.mcp_manager.disconnect()

if __name__ == "__main__":
    import asyncio
    agent = ProfessionalHotelAgent()
    asyncio.run(agent.run_interactive())