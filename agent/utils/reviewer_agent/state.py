from typing import TypedDict, Optional , List

class AssignmentState(TypedDict):
    # Inputs we give the graph
    teacher_id: str
    student_id: str
    assignment_id: int
    pending_labels: List[str]          # The queue of questions left to grade
    current_label: Optional[str]       # The specific question being graded right now
    
    # Fetched from DB
    student_answer_id: Optional[int]
    question_description: Optional[str]
    rubric_description: Optional[str]
    student_answer: Optional[str]
    
    # AI Outputs
    grader_1_score: Optional[float]
    grader_1_feedback: Optional[str]
    grader_2_score: Optional[float]
    grader_2_feedback: Optional[str]
    
    # Final Result
    final_score: Optional[float]
    final_feedback: Optional[str]
    detailed_marks: Optional[dict]