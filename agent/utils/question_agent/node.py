import json
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .prompts import RUBRIC_PROMPT,TEACHER_SOLVE_PROMPT ,system_prompt
from .state import AgentState
from .tools import tools
from dotenv import load_dotenv
load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)


def dynamic_extract_node(state: AgentState):
    """
    A single node that acts as Scribe, Oracle, or Architect depending on the input.
    """
    content = state["file_content"]
    doc_type = state["document_type"]
    
    # Select the right persona/prompt dynamically
    if doc_type == "rubric":
        system_prompt = RUBRIC_PROMPT
    else:
        system_prompt = TEACHER_SOLVE_PROMPT
    
        
    messages = [SystemMessage(content=system_prompt)]
    
    # Handle Vision vs Text
    if state["file_type"] == "image":
        messages.append(
            HumanMessage(
                content=[
                    {"type": "text", "text": "Please transcribe and structure this document."},
                    {"type": "image_url", "image_url": {"url": content}}
                ]
            )
        )
    else:
        messages.append(
            HumanMessage(content=f"Here is the raw text to structure:\n\n{content}")
        )

    # Force strict JSON output
    json_llm = llm.bind(response_format={"type": "json_object"})
    response = json_llm.invoke(messages)
    
    return {"final_output": response.content}


def save_with_agent(state: AgentState):
    content = state["final_output"]

    message = HumanMessage(
        content=system_prompt.format(
            teacher_id=state["teacher_id"],
            assignment_id=state["assignment_id"],
        )
        + content
    )

    response = llm.invoke([message])
    return {"final_output": response.content}


from langgraph.prebuilt import ToolNode

tool_node = ToolNode(tools)