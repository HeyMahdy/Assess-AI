from langchain_core.messages import HumanMessage, AIMessage

from .graph import build_ta_graph


async def chat_with_ta(teacher_id: str, message: str, history: list = None):
    """Run a single turn of the TA chatbot using the LangGraph agent."""
    graph = build_ta_graph()

    # Build messages from history
    messages = []
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=message))

    # Invoke the graph
    result = graph.invoke({
        "teacher_id": teacher_id,
        "messages": messages,
    })

    # Extract the final AI response
    final_messages = result.get("messages", [])
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
            return msg.content

    return "I wasn't able to process that request. Could you try rephrasing?"
