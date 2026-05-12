from typing import TypedDict
class AgentState(TypedDict):
    file_content: str  
    file_type: str     
    document_type: str # NEW: "student_answer", "teacher_solve", or "rubric"
    final_output: str
    teacher_id: str
    assignment_id: int