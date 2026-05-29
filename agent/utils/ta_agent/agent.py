from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from .tools import tools

SYSTEM_PROMPT = """You are an AI Teaching Assistant designed to help teachers analyze student performance and build personalized improvement plans.

RUNTIME CONTEXT:
- Teacher ID: {teacher_id}

IMPORTANT: When calling any tool, you MUST always include teacher_id="{teacher_id}" as a parameter.

When a teacher asks about a student's performance on a specific assignment:

1. ENTITY EXTRACTION: Parse the teacher's message to identify the student name/ID and assignment title.
2. DATABASE RESOLUTION: Use search_student and search_assignment tools to find the exact database IDs.
3. SCORE RETRIEVAL: Use get_student_scores to fetch the student's grading breakdown and ai_comments.
4. SYLLABUS MAPPING: Use query_syllabus with the student's weaknesses (from ai_comments) to find prerequisites and related topics.
5. PLAN CURATION: Synthesize everything into a clear, actionable study plan.

RESPONSE FORMAT:
- Start with a brief summary of what you found
- List the student's key weaknesses (from ai_comments)
- Present a structured study plan with:
  - "Review Prerequisites" section
  - "Targeted Study" section with related topics
  - "Practice Recommendations" section
- End by inviting the teacher to review or refine the plan

TONE: Conversational, professional, concise. Use bullet points for clarity.

If you can't find a student or assignment, ask the teacher for clarification.
If no syllabus is uploaded, still provide the weakness analysis and suggest the teacher upload a syllabus for better recommendations.
"""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


def build_ta_agent(teacher_id: str):
    """Creates a ReAct agent with the TA system prompt and tools."""
    system_message = SYSTEM_PROMPT.format(teacher_id=teacher_id)
    agent = create_react_agent(llm, tools, prompt=system_message)
    return agent


async def chat_with_ta(teacher_id: str, message: str, history: list = None):
    """Run a single turn of the TA chatbot."""
    agent = build_ta_agent(teacher_id)

    # Build messages
    messages = []
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=message))

    # Invoke the agent
    result = agent.invoke({"messages": messages})

    # Extract the final AI response
    final_messages = result.get("messages", [])
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            return msg.content

    return "I wasn't able to process that request. Could you try rephrasing?"
