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
    
    print("\n" + "="*50)
    print(f"[save_with_agent] 🚀 Entering node.")
    print(f"[save_with_agent] 🔍 State -> teacher_id: {state.get('teacher_id')}, assignment_id: {state.get('assignment_id')}")
    print(f"[save_with_agent] 🔍 Current message count in state: {len(state.get('messages', []))}")
    
    if not state.get("messages"):
        print("[save_with_agent] 🛤️ Branch: FIRST PASS (No previous messages).")
        
        extracted_json = state.get("final_output", "{}")
        
        # 🚨 NEW FULL LOGGING HERE 🚨
        print("\n" + "-"*20 + " FULL JSON PAYLOAD " + "-"*20)
        print(extracted_json)
        print("-" * 59 + "\n")
        
        initial_instruction = system_prompt.format(
            teacher_id=state["teacher_id"],
            assignment_id=state["assignment_id"],
        ) + f"\n\nJSON TO PROCESS:\n{extracted_json}"
        
        # Optional: Uncomment the next two lines if you want to see the ENTIRE prompt sent to the LLM
        # print("\n[save_with_agent] 📝 FULL PROMPT SENT TO LLM:\n")
        # print(initial_instruction)
        
        messages_to_process = [HumanMessage(content=initial_instruction)]
    else:
        print("[save_with_agent] 🛤️ Branch: LOOPING BACK. Using existing message history.")
        messages_to_process = state["messages"]

    print(f"[save_with_agent] 🧠 Invoking LLM with {len(messages_to_process)} messages...")
    
    response = agent_llm.invoke(messages_to_process)

    print(f"[save_with_agent] ✅ LLM Responded.")
    
    if response.content:
         print(f"[save_with_agent] 💬 LLM Text Content: '{response.content}'")

    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f"[save_with_agent] 🛠️ LLM requested {len(response.tool_calls)} tool calls:")
        for i, call in enumerate(response.tool_calls):
            print(f"    {i+1}. Tool Name: {call.get('name')}")
            print(f"       Args: {call.get('args')}")
    else:
        print("[save_with_agent] 🛑 No tool calls requested by LLM. It is finished.")
    
    print("="*50 + "\n")
    
    return {"messages": [response]}