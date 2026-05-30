import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .prompt import SYSTEM_PROMPT
from .tools import tools

# Tool node for LangGraph
tool_node = ToolNode(tools)


def _log(message: str) -> None:
    return None


def _get_agent_llm():
    model_name = os.getenv("TA_AGENT_MODEL", "gpt-5.1")
    llm_kwargs = {"model": model_name}
    if not model_name.startswith("gpt-5"):
        llm_kwargs["temperature"] = 0.1
    llm = ChatOpenAI(**llm_kwargs)
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
