from langgraph.graph import StateGraph, START, END

from .nodes import process_with_llm, process_with_agent, tool_node
from .state import AgentState

def should_continue(state: AgentState):
    """
    Evaluates the last message to decide the next step.
    Routes to 'tools' if the LLM wants to execute a tool, otherwise ends the workflow.
    """
    messages = state.get("messages")
    if messages:
        last_message = messages[-1]
        # Check if the LLM requested a tool execution
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
    return "END"

def build_graph():
    workflow = StateGraph(AgentState)
    
    # 1. Add all your nodes
    workflow.add_node("analyze_node", process_with_llm)
    workflow.add_node("save_agent", process_with_agent) 
    workflow.add_node("tool_node", tool_node)           
    
    # 2. Linear sequence at the start
    workflow.add_edge(START, "analyze_node")
    workflow.add_edge("analyze_node", "save_agent")
    
    # 3. The Conditional Edge
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