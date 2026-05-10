

import json
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from .node import dynamic_extract_node
def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("extract_node", dynamic_extract_node)
    workflow.add_edge(START, "extract_node")
    workflow.add_edge("extract_node", END)
    
    return workflow.compile()