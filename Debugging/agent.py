from typing import Annotated
from typing_extensions import TypedDict
from langchain_groq import ChatGroq
from langgraph.graph import START, END
from langgraph.graph.state import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain.tools import tool 
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

import os 
from dotenv import load_dotenv
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_TRACING"]="true"
os.environ["LANGSMITH_PROJECT"]="TestProject"

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0
)

from langchain_core.messages import BaseMessage
class State(TypedDict):
    messages:Annotated[list[BaseMessage], add_messages]

def make_tool_graph(tools:list):
    ## graph with tool call 
    
    @tool
    def add(a: int, b:int): 
        """Add two numbers """
        return a + b


    tools = [add]
    ##  Node that executes tools
    tool_node = ToolNode(tools)

    # LLM that knows about the tools
    llm_with_tool = llm.bind_tools(tools)


    def call_llm_model(state: State):
        return {"messages":[llm_with_tool.invoke(state["messages"])]}

    builder = StateGraph(State)
    builder.add_node("tool_calling_llm",call_llm_model)
    builder.add_node("tools", ToolNode(tools))

    ## add edges
    builder.add_edge(START, "tool_calling_llm",)
    builder.add_conditional_edges(
    "tool_calling_llm",
    tools_condition
)

    builder.add_edge("tools","tool_calling_llm")

    graph = builder.compile()
    
    return graph

tool_agent = make_tool_graph([])

