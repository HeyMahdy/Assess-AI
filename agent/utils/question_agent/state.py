
import operator
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from typing import TypedDict
class AgentState(TypedDict):
    file_content: str  
    file_type: str     
    document_type: str # NEW: "student_answer", "teacher_solve", or "rubric"
    final_output: str
    teacher_id: str
    assignment_id: int
    final_output: str # Where your JSON extraction is saved
    messages: Annotated[Sequence[BaseMessage], operator.add]