from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .prompt import SYSTEM_PROMPT
from .tools import tools

# Tool node for LangGraph
tool_node = ToolNode(tools)


def _log(message: str) -> None:
    print(f"[ta_agent.node] {message}", flush=True)


def _get_agent_llm():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return llm.bind_tools(tools)


def agent_node(state: AgentState):
    """The main TA agent reasoning node. Processes messages and decides tool calls."""
    teacher_id = state["teacher_id"]
    system_message = SystemMessage(content=SYSTEM_PROMPT.format(teacher_id=teacher_id))

    messages = [system_message] + state["messages"]
    _log(f"invoke teacher_id={teacher_id} message_count={len(state['messages'])}")
    response = _get_agent_llm().invoke(messages)
    tool_calls = getattr(response, "tool_calls", None) or []
    if tool_calls:
        tool_names = [tool_call.get("name", "unknown") for tool_call in tool_calls]
        _log(f"model requested tool_calls={tool_names}")
    else:
        preview = response.content[:300] if isinstance(response.content, str) else str(response.content)[:300]
        _log(f"model returned final content_preview={preview!r}")

    return {"messages": [response]}
