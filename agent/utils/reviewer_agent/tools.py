import json
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from config.db import get_db_connection

class FetchContextInput(BaseModel):
    teacher_id: str = Field(...)
    student_id: str = Field(...)
    assignment_id: int = Field(...)
    question_label: str = Field(...)

@tool("fetch_evaluation_context", args_schema=FetchContextInput)
def fetch_evaluation_context(teacher_id: str, student_id: str, assignment_id: int, question_label: str) -> str:
    """Fetches the question description, rubric rules, and student answer from the database."""
    sql = """
        SELECT sa.id AS ans_id, sa.answer, q.question_description, r.rubric_description
        FROM public.student_answers sa
        JOIN public.questions q ON sa.assignment_id = q.assignment_id AND sa.question_label = q.question_label
        JOIN public.rubrics r ON sa.assignment_id = r.assignment_id AND sa.question_label = r.question_label
        WHERE sa.teacher_id = %s AND sa.student_id = %s AND sa.assignment_id = %s AND sa.question_label = %s;
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (teacher_id, student_id, assignment_id, question_label))
                row = cur.fetchone()
                
                # Handle cases where the data doesn't exist yet
                if not row:
                    return json.dumps({"error": "No matching data found in the database."})
                    
                # Return the data as a clean JSON string
                return json.dumps({
                    "student_answer_id": row['ans_id'],
                    "question_description": row['question_description'],
                    "rubric_description": row['rubric_description'],
                    "student_answer": row['answer'],
                })
                
    except Exception as e:
        return json.dumps({"error": f"Database error: {str(e)}"})
    




class GetAssignmentLabelsInput(BaseModel):
    teacher_id: str = Field(..., description="The UUID of the teacher.")
    assignment_id: int = Field(..., description="The integer ID of the assignment.")

@tool("get_assignment_labels", args_schema=GetAssignmentLabelsInput)
def get_assignment_labels(teacher_id: str, assignment_id: int) -> str:
    """
    Fetches a list of all question labels (e.g., '1a', 'Q2') associated with a specific assignment.
    Useful for knowing exactly which questions need to be graded.
    """
    sql = """
        SELECT question_label 
        FROM public.questions 
        WHERE teacher_id = %s AND assignment_id = %s
        ORDER BY id ASC;
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (teacher_id, assignment_id))
                rows = cur.fetchall()
                
                # Extract the labels into a clean Python list
                labels = [row['question_label'] for row in rows]
                
                # If the assignment is empty, tell the agent
                if not labels:
                    return json.dumps({"message": "No questions found for this assignment."})
                
                print("tool got called")
                    
                # Return as a JSON string so the LLM can parse it easily
                return json.dumps({"labels": labels})
                
    except Exception as e:
        return json.dumps({"error": f"Database error fetching labels: {str(e)}"})
    

tools = [fetch_evaluation_context,get_assignment_labels]
tools_by_name = {tool_item.name: tool_item for tool_item in tools}