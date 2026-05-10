from langgraph.graph import StateGraph, START, END

from .nodes import process_with_llm , process_with_agent
from .state import AgentState


def build_graph():
	workflow = StateGraph(AgentState)
	workflow.add_node("analyze_node", process_with_llm)
	workflow.add_node("json_node", process_with_agent)
	workflow.add_edge(START, "analyze_node")
	workflow.add_edge("analyze_node", "json_node")
	workflow.add_edge("json_node", END)
	return workflow.compile()
