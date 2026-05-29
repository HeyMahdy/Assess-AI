import json
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from config.db import get_db_connection
from langchain_openai import OpenAIEmbeddings

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")


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
                # Try by ID first (exact match)
                if provided_id:
                    cur.execute(
                        "SELECT id, name FROM public.students WHERE teacher_id = %s AND id = %s",
                        (teacher_id, provided_id)
                    )
                    row = cur.fetchone()
                    if row:
                        return json.dumps({"student_id": row["id"], "name": row["name"]})

                # Try by name (case-insensitive partial match)
                if name:
                    cur.execute(
                        "SELECT id, name FROM public.students WHERE teacher_id = %s AND LOWER(name) LIKE LOWER(%s) LIMIT 5",
                        (teacher_id, f"%{name}%")
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
                    (teacher_id, f"%{title}%")
                )
                rows = cur.fetchall()
                if rows:
                    if len(rows) == 1:
                        return json.dumps({"assignment_id": rows[0]["id"], "title": rows[0]["title"], "subject": rows[0]["subject"], "total_marks": rows[0]["total_marks"]})
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
    sql = """
        SELECT question_label, marks, confidence_score, ai_comment
        FROM public.student_question_scores
        WHERE assignment_id = %s AND student_id = %s AND teacher_id = %s
        ORDER BY id ASC;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (assignment_id, student_id, teacher_id))
                rows = cur.fetchall()
                if not rows:
                    return json.dumps({"error": "No scores found for this student on this assignment."})

                total = sum(float(r["marks"]) for r in rows)
                results = []
                for r in rows:
                    results.append({
                        "question_label": r["question_label"],
                        "marks": float(r["marks"]),
                        "confidence": float(r["confidence_score"]),
                        "ai_comment": r.get("ai_comment", ""),
                    })
                return json.dumps({"total_marks": total, "scores": results})
    except Exception as e:
        return json.dumps({"error": str(e)})


class QuerySyllabusInput(BaseModel):
    search_query: str = Field(..., description="Natural language query about student weaknesses to find related syllabus topics")
    teacher_id: str = Field(..., description="The teacher's UUID")

@tool("query_syllabus", args_schema=QuerySyllabusInput)
def query_syllabus(search_query: str, teacher_id: str) -> str:
    """Queries the syllabus GraphRAG to find prerequisites and related topics based on student weaknesses."""
    try:
        # Find the teacher's most recent syllabus
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM public.syllabi WHERE teacher_id = %s ORDER BY created_at DESC LIMIT 1",
                    (teacher_id,)
                )
                row = cur.fetchone()
                if not row:
                    return json.dumps({"error": "No syllabus found. Please upload a syllabus first."})
                syllabus_id = row["id"]

        # Vector search for matching entities
        query_embedding = embeddings_model.embed_query(search_query)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, entity_type, description, difficulty_level
                    FROM public.syllabus_entities
                    WHERE syllabus_id = %s AND embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT 5;
                """, (syllabus_id, str(query_embedding)))
                matched = [dict(r) for r in cur.fetchall()]

                if not matched:
                    return json.dumps({"matched_topics": [], "prerequisites": [], "related_topics": []})

                entity_ids = [m["id"] for m in matched]

                # Get prerequisites
                cur.execute("""
                    SELECT DISTINCT e.name, e.difficulty_level
                    FROM public.syllabus_relationships r
                    JOIN public.syllabus_entities e ON e.id = r.source_entity_id
                    WHERE r.target_entity_id = ANY(%s) AND r.relationship_type = 'PREREQUISITE_OF'
                    AND r.syllabus_id = %s;
                """, (entity_ids, syllabus_id))
                prerequisites = [dict(r) for r in cur.fetchall()]

                # Get related topics
                cur.execute("""
                    SELECT DISTINCT e.name, e.difficulty_level, r.relationship_type
                    FROM public.syllabus_relationships r
                    JOIN public.syllabus_entities e ON (
                        (e.id = r.source_entity_id AND r.target_entity_id = ANY(%s))
                        OR (e.id = r.target_entity_id AND r.source_entity_id = ANY(%s))
                    )
                    WHERE r.syllabus_id = %s AND r.relationship_type != 'PREREQUISITE_OF';
                """, (entity_ids, entity_ids, syllabus_id))
                related = [dict(r) for r in cur.fetchall()]

        return json.dumps({
            "matched_topics": [{"name": m["name"], "type": m["entity_type"], "level": m["difficulty_level"]} for m in matched],
            "prerequisites": [{"name": p["name"], "level": p["difficulty_level"]} for p in prerequisites],
            "related_topics": [{"name": r["name"], "level": r["difficulty_level"], "relationship": r["relationship_type"]} for r in related],
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


tools = [search_student, search_assignment, get_student_scores, query_syllabus]
