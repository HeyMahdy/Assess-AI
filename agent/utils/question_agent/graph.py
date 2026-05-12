

import json
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from .node import dynamic_extract_node , tool_node ,save_with_agent


def should_continue(state: AgentState):
    """
    Evaluates the last message to decide the next step.
    Routes to 'tools' if the LLM wants to execute a tool, otherwise ends the workflow.
    """
    last_message = state["messages"][-1]
    
    # Check if the LLM requested a tool execution
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools" # <--- FIXED: Changed from "continue" to "tools"
    else:
        return "END"
    
def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("extract_node", dynamic_extract_node)
    workflow.add_node("tool_node", tool_node)
    workflow.add_node("save_agent", save_with_agent)
    workflow.add_edge(START, "extract_node")
    workflow.add_conditional_edges(
        "save_agent",
        should_continue,
        {
            "tools": "tool_node", # Now this matches the return value perfectly!
            "END": END            
        }
    )
    
    # 4. The Loop Back
    workflow.add_edge("tool_node", "save_agent")
    
    return workflow.compile()