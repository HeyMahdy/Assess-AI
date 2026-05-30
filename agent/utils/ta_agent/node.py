from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .prompt import SYSTEM_PROMPT
from .tools import tools

# Tool node for LangGraph
tool_node = ToolNode(tools)


def _get_agent_llm():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return llm.bind_tools(tools)


def agent_node(state: AgentState):
    """The main TA agent reasoning node. Processes messages and decides tool calls."""
    teacher_id = state["teacher_id"]
    system_message = SystemMessage(content=SYSTEM_PROMPT.format(teacher_id=teacher_id))

    messages = [system_message] + state["messages"]
    response = _get_agent_llm().invoke(messages)

    return {"messages": [response]}
