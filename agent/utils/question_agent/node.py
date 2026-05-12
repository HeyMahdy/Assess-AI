import json
from typing import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode

from .prompts import RUBRIC_PROMPT, TEACHER_SOLVE_PROMPT, system_prompt
from .state import AgentState
from .tools import tools

load_dotenv()

# 1. Initialize LLMs
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# CRITICAL FIX: The saving agent MUST have tools bound to it!
agent_llm = llm.bind_tools(tools)

# 2. Tool Node
tool_node = ToolNode(tools)  

# ---------------------------------------------------------
# NODE 1: The Extractor
# ---------------------------------------------------------
def dynamic_extract_node(state: AgentState):
    """Acts as Scribe or Architect depending on document_type."""
    content = state["file_content"]
    doc_type = state["document_type"]
    
    if doc_type == "rubric":
        active_prompt = RUBRIC_PROMPT
    else:
        active_prompt = TEACHER_SOLVE_PROMPT
        
    messages = [SystemMessage(content=active_prompt)]
    
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

    json_llm = llm.bind(response_format={"type": "json_object"})
    response = json_llm.invoke(messages)
    
    return {"final_output": response.content}

# ---------------------------------------------------------
# NODE 2: The Agent Brain
# ---------------------------------------------------------
def save_with_agent(state: AgentState):
    """Decides which tools to call based on the extracted JSON."""
    
    # CRITICAL FIX: Check if we are looping. 
    # If there are no messages yet, format the initial prompt.
    if not state.get("messages"):
        extracted_json = state["final_output"]
        initial_instruction = system_prompt.format(
            teacher_id=state["teacher_id"],
            assignment_id=state["assignment_id"],
        ) + f"\n\nJSON TO PROCESS:\n{extracted_json}"
        
        messages_to_process = [HumanMessage(content=initial_instruction)]
    else:
        # If we are looping back from a tool call, just pass the message history
        messages_to_process = state["messages"]

    # Use the LLM that actually has tools bound to it!
    response = agent_llm.invoke(messages_to_process)
    
    # CRITICAL FIX: Must return to the "messages" array so the router can read it
    return {"messages": [response]}