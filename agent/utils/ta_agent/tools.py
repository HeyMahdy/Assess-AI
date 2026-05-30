import json
import httpx
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from config.db import get_db_connection


AGENT_BASE_URL = "http://localhost:8000"


class SearchStudentInput(BaseModel):
    name: str = Field(default="", description="Student name to search for")
    provided_id: str = Field(default="", description="Student ID provided by teacher")
    teacher_id: str = Field(..., description="The teacher's UUID")


@tool("search_student", args_schema=SearchStudentInput)
def search_student(name: str, provided_id: str, teacher_id: str) -> str:
    """Searches the database for a student using their name or ID. Returns the student record."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if provided_id:
                    cur.execute(
                        "SELECT id, name FROM public.students WHERE teacher_id = %s AND id = %s",
                        (teacher_id, provided_id),
                    )
                    row = cur.fetchone()
                    if row:
                        return json.dumps({"student_id": row["id"], "name": row["name"]})

                if name:
                    cur.execute(
                        "SELECT id, name FROM public.students WHERE teacher_id = %s AND LOWER(name) LIKE LOWER(%s) LIMIT 5",
                        (teacher_id, f"%{name}%"),
                    )
                    rows = cur.fetchall()
                    if rows:
                        if len(rows) == 1:
                            return json.dumps({"student_id": rows[0]["id"], "name": rows[0]["name"]})
                        return json.dumps({"multiple_matches": [{"id": r["id"], "name": r["name"]} for r in rows]})

                return json.dumps({"error": f"No student found matching name='{name}' or id='{provided_id}'"})
    except Exception as e:
        return json.dumps({"error": str(e)})


class SearchAssignmentInput(BaseModel):
    title: str = Field(..., description="Assignment title or keyword to search for")
    teacher_id: str = Field(..., description="The teacher's UUID")


@tool("search_assignment", args_schema=SearchAssignmentInput)
def search_assignment(title: str, teacher_id: str) -> str:
    """Searches the database for an assignment by title. Returns the assignment record."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, subject, total_marks FROM public.assignments WHERE teacher_id = %s AND LOWER(title) LIKE LOWER(%s) LIMIT 5",
                    (teacher_id, f"%{title}%"),
                )
                rows = cur.fetchall()
                if rows:
                    if len(rows) == 1:
                        return json.dumps({
                            "assignment_id": rows[0]["id"],
                            "title": rows[0]["title"],
                            "subject": rows[0]["subject"],
                            "total_marks": rows[0]["total_marks"],
                        })
                    return json.dumps({"multiple_matches": [{"id": r["id"], "title": r["title"]} for r in rows]})
                return json.dumps({"error": f"No assignment found matching '{title}'"})
    except Exception as e:
        return json.dumps({"error": str(e)})


class GetStudentScoresInput(BaseModel):
    assignment_id: int = Field(..., description="The assignment ID")
    student_id: str = Field(..., description="The student ID")
    teacher_id: str = Field(..., description="The teacher's UUID")


@tool("get_student_scores", args_schema=GetStudentScoresInput)
def get_student_scores(assignment_id: int, student_id: str, teacher_id: str) -> str:
    """Fetches the student's grading results including scores and AI comments about weaknesses."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT question_label, marks, confidence_score, ai_comment
                       FROM public.student_question_scores
                       WHERE assignment_id = %s AND student_id = %s AND teacher_id = %s
                       ORDER BY id ASC""",
                    (assignment_id, student_id, teacher_id),
                )
                rows = cur.fetchall()
                if not rows:
                    return json.dumps({"error": "No scores found for this student on this assignment."})

                total = sum(float(r["marks"]) for r in rows)
                results = [
                    {
                        "question_label": r["question_label"],
                        "marks": float(r["marks"]),
                        "confidence": float(r["confidence_score"]),
                        "ai_comment": r.get("ai_comment", ""),
                    }
                    for r in rows
                ]
                return json.dumps({"total_marks": total, "scores": results})
    except Exception as e:
        return json.dumps({"error": str(e)})


class QuerySyllabusInput(BaseModel):
    search_query: str = Field(..., description="Natural language query about student weaknesses to find related syllabus topics")
    assignment_id: int = Field(..., description="The assignment ID whose syllabus to query")


@tool("query_syllabus", args_schema=QuerySyllabusInput)
def query_syllabus(search_query: str, assignment_id: int) -> str:
    """Queries the syllabus GraphRAG via the internal API to find prerequisites and related topics based on student weaknesses."""
    try:
        response = httpx.post(
            f"{AGENT_BASE_URL}/internal/agent/syllabus/query",
            json={"query": search_query, "assignment_id": assignment_id},
            timeout=30.0,
        )

        if response.status_code == 404:
            return json.dumps({"error": "No syllabus found for this assignment. Please upload a syllabus first."})

        if response.status_code != 200:
            return json.dumps({"error": f"Syllabus query failed with status {response.status_code}"})

        data = response.json()
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": str(e)})


tools = [search_student, search_assignment, get_student_scores, query_syllabus]
