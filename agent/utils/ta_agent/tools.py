import json
import re
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from config.db import get_db_connection


MAX_RESULT_ROWS = 50
DEFAULT_RESULT_ROWS = MAX_RESULT_ROWS
REDACTED = "[REDACTED]"
_ta_teacher_id: ContextVar[str] = ContextVar("ta_teacher_id", default="")

SENSITIVE_COLUMN_PATTERNS = (
    "password",
    "password_hash",
    "token",
    "secret",
    "credential",
    "api_key",
    "apikey",
    "private_key",
    "hash",
)

FORBIDDEN_SQL_RE = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|truncate|create|replace|grant|revoke|"
    r"copy|execute|call|do|merge|vacuum|analyze|reindex|refresh|set|reset|"
    r"begin|start|commit|rollback|savepoint|lock|listen|notify"
    r")\b",
    re.IGNORECASE,
)


SCHEMA: dict[str, list[dict[str, str]]] = {
    "ai_evaluations": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "student_answer_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "final_score", "type": "numeric", "nullable": "YES", "default": ""},
        {"column": "final_feedback", "type": "text", "nullable": "YES", "default": ""},
        {"column": "detailed_marks", "type": "jsonb", "nullable": "NO", "default": ""},
        {"column": "confidence_score", "type": "numeric", "nullable": "YES", "default": ""},
        {"column": "evaluation_metadata", "type": "jsonb", "nullable": "YES", "default": ""},
        {"column": "evaluated_at", "type": "timestamp with time zone", "nullable": "NO", "default": "now()"},
    ],
    "assignments": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "title", "type": "text", "nullable": "NO", "default": ""},
        {"column": "subject", "type": "text", "nullable": "YES", "default": ""},
        {"column": "total_marks", "type": "integer", "nullable": "YES", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "NO", "default": "now()"},
    ],
    "concept_dependencies": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "concept_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "prerequisite_concept_id", "type": "integer", "nullable": "NO", "default": ""},
    ],
    "concepts": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "subject", "type": "text", "nullable": "NO", "default": ""},
        {"column": "name", "type": "text", "nullable": "NO", "default": ""},
        {"column": "description", "type": "text", "nullable": "YES", "default": ""},
    ],
    "grading_jobs": [
        {"column": "id", "type": "uuid", "nullable": "NO", "default": "gen_random_uuid()"},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "assignment_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "student_id", "type": "text", "nullable": "NO", "default": ""},
        {"column": "status", "type": "text", "nullable": "NO", "default": "'queued'::text"},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
        {"column": "completed_at", "type": "timestamp with time zone", "nullable": "YES", "default": ""},
    ],
    "knowledge_documents": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "subject", "type": "text", "nullable": "NO", "default": ""},
        {"column": "topic", "type": "text", "nullable": "NO", "default": ""},
        {"column": "document_type", "type": "text", "nullable": "NO", "default": ""},
        {"column": "file_name", "type": "text", "nullable": "YES", "default": ""},
        {"column": "content", "type": "text", "nullable": "NO", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "knowledge_embeddings": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "document_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "chunk_text", "type": "text", "nullable": "NO", "default": ""},
        {"column": "embedding", "type": "USER-DEFINED", "nullable": "YES", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "questions": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "assignment_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "question_label", "type": "text", "nullable": "NO", "default": ""},
        {"column": "question_description", "type": "text", "nullable": "NO", "default": ""},
        {"column": "marks", "type": "integer", "nullable": "YES", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "remediation_exercises": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "concept_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "generated_question", "type": "text", "nullable": "NO", "default": ""},
        {"column": "difficulty", "type": "text", "nullable": "YES", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
        {"column": "student_id", "type": "uuid", "nullable": "NO", "default": ""},
    ],
    "rubrics": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "assignment_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "question_label", "type": "text", "nullable": "NO", "default": ""},
        {"column": "rubric_description", "type": "jsonb", "nullable": "NO", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "student_answers": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "student_id", "type": "text", "nullable": "NO", "default": ""},
        {"column": "assignment_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "question_label", "type": "text", "nullable": "NO", "default": ""},
        {"column": "answer", "type": "text", "nullable": "NO", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "student_question_scores": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "student_id", "type": "text", "nullable": "NO", "default": ""},
        {"column": "assignment_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "question_label", "type": "text", "nullable": "NO", "default": ""},
        {"column": "question_text", "type": "text", "nullable": "YES", "default": ""},
        {"column": "student_solution", "type": "text", "nullable": "YES", "default": ""},
        {"column": "marks", "type": "numeric", "nullable": "NO", "default": "0.0"},
        {"column": "confidence_score", "type": "numeric", "nullable": "NO", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
        {"column": "updated_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
        {"column": "teacher_comment", "type": "text", "nullable": "YES", "default": ""},
        {"column": "ai_comment", "type": "text", "nullable": "YES", "default": ""},
    ],
    "student_weak_concepts": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "student_id", "type": "text", "nullable": "NO", "default": ""},
        {"column": "concept_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "weakness_score", "type": "numeric", "nullable": "YES", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "students": [
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "student_id", "type": "text", "nullable": "NO", "default": ""},
        {"column": "name", "type": "text", "nullable": "NO", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "NO", "default": "now()"},
        {"column": "id", "type": "uuid", "nullable": "NO", "default": "gen_random_uuid()"},
    ],
    "syllabi": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "filename", "type": "text", "nullable": "NO", "default": ""},
        {"column": "raw_text", "type": "text", "nullable": "YES", "default": ""},
        {"column": "status", "type": "text", "nullable": "NO", "default": "'processing'::text"},
        {"column": "entity_count", "type": "integer", "nullable": "YES", "default": "0"},
        {"column": "relationship_count", "type": "integer", "nullable": "YES", "default": "0"},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
        {"column": "assignment_id", "type": "integer", "nullable": "YES", "default": ""},
    ],
    "syllabus_entities": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "syllabus_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "name", "type": "text", "nullable": "NO", "default": ""},
        {"column": "entity_type", "type": "text", "nullable": "NO", "default": ""},
        {"column": "description", "type": "text", "nullable": "YES", "default": ""},
        {"column": "difficulty_level", "type": "text", "nullable": "YES", "default": ""},
        {"column": "week_or_unit", "type": "text", "nullable": "YES", "default": ""},
        {"column": "embedding", "type": "USER-DEFINED", "nullable": "YES", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "syllabus_relationships": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "syllabus_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "source_entity_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "target_entity_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "relationship_type", "type": "text", "nullable": "NO", "default": ""},
        {"column": "strength", "type": "integer", "nullable": "YES", "default": "3"},
        {"column": "reason", "type": "text", "nullable": "YES", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "teacher_reviews": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "evaluation_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_score", "type": "numeric", "nullable": "YES", "default": ""},
        {"column": "teacher_feedback", "type": "text", "nullable": "YES", "default": ""},
        {"column": "approved", "type": "boolean", "nullable": "YES", "default": "false"},
        {"column": "reviewed_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "teacher_solutions": [
        {"column": "id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "teacher_id", "type": "uuid", "nullable": "NO", "default": ""},
        {"column": "assignment_id", "type": "integer", "nullable": "NO", "default": ""},
        {"column": "question_label", "type": "text", "nullable": "NO", "default": ""},
        {"column": "solution_text", "type": "text", "nullable": "NO", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "YES", "default": "now()"},
    ],
    "users": [
        {"column": "id", "type": "uuid", "nullable": "NO", "default": "gen_random_uuid()"},
        {"column": "email", "type": "text", "nullable": "NO", "default": ""},
        {"column": "password_hash", "type": "text", "nullable": "NO", "default": ""},
        {"column": "display_name", "type": "text", "nullable": "YES", "default": ""},
        {"column": "created_at", "type": "timestamp with time zone", "nullable": "NO", "default": "now()"},
    ],
}

RELATIONSHIP_HINTS = [
    "assignments.teacher_id = users.id",
    "students.teacher_id = users.id",
    "questions.assignment_id = assignments.id",
    "rubrics.assignment_id = assignments.id",
    "teacher_solutions.assignment_id = assignments.id",
    "student_answers.assignment_id = assignments.id",
    "student_question_scores.assignment_id = assignments.id",
    "ai_evaluations.student_answer_id = student_answers.id",
    "teacher_reviews.evaluation_id = ai_evaluations.id",
    "syllabi.assignment_id = assignments.id",
    "syllabus_entities.syllabus_id = syllabi.id",
    "syllabus_relationships.source_entity_id = syllabus_entities.id",
    "syllabus_relationships.target_entity_id = syllabus_entities.id",
    "student_weak_concepts.concept_id = concepts.id",
    "concept_dependencies.concept_id = concepts.id",
    "concept_dependencies.prerequisite_concept_id = concepts.id",
    "remediation_exercises.concept_id = concepts.id",
    "students.student_id is the teacher-facing student ID.",
    "students.id is the internal UUID; some historical score/submission rows store this UUID as text in student_id.",
    "For student_question_scores, join students with: student_question_scores.student_id = students.id::text OR student_question_scores.student_id = students.student_id.",
    "For student_answers, join students with: student_answers.student_id = students.id::text OR student_answers.student_id = students.student_id.",
    "For student_weak_concepts, join students with: student_weak_concepts.student_id = students.id::text OR student_weak_concepts.student_id = students.student_id.",
    "For grading_jobs, join students with: grading_jobs.student_id = students.id::text OR grading_jobs.student_id = students.student_id.",
    "remediation_exercises.student_id is UUID and joins to students.id.",
]

PRIMARY_KEYS = {
    "ai_evaluations": ["id"],
    "assignments": ["id"],
    "concept_dependencies": ["id"],
    "concepts": ["id"],
    "grading_jobs": ["id"],
    "knowledge_documents": ["id"],
    "knowledge_embeddings": ["id"],
    "questions": ["id"],
    "remediation_exercises": ["id"],
    "rubrics": ["id"],
    "student_answers": ["id"],
    "student_question_scores": ["id"],
    "student_weak_concepts": ["id"],
    "students": ["id"],
    "syllabi": ["id"],
    "syllabus_entities": ["id"],
    "syllabus_relationships": ["id"],
    "teacher_reviews": ["id"],
    "teacher_solutions": ["id"],
    "users": ["id"],
}


def _log(message: str) -> None:
    print(f"[ta_agent.sql] {message}", flush=True)


def set_ta_auth_context(access_token: str = "", teacher_id: str = "") -> None:
    """Keep compatibility with the old auth hook while storing teacher scope."""
    _ta_teacher_id.set(teacher_id or "")


def _is_sensitive_column(column_name: str) -> bool:
    normalized = column_name.lower()
    return any(pattern in normalized for pattern in SENSITIVE_COLUMN_PATTERNS)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return REDACTED
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


def _redact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: REDACTED if _is_sensitive_column(key) else _json_safe(value)
        for key, value in row.items()
    }


def _numeric_column_summaries(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    summaries: dict[str, dict[str, float | int]] = {}
    for row in rows:
        for key, value in row.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                column_summary = summaries.setdefault(key, {"sum": 0.0, "count": 0})
                column_summary["sum"] = float(column_summary["sum"]) + float(value)
                column_summary["count"] = int(column_summary["count"]) + 1

    return summaries


def _split_requested_tables(table_names: str) -> list[str]:
    return [
        table.strip().removeprefix("public.")
        for table in table_names.split(",")
        if table.strip()
    ]


def _has_unquoted_semicolon(sql: str) -> bool:
    in_single = False
    in_double = False
    index = 0

    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if char == "'" and not in_double:
            if in_single and next_char == "'":
                index += 2
                continue
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == ";" and not in_single and not in_double:
            return True

        index += 1

    return False


def _strip_single_trailing_semicolon(sql: str) -> str:
    stripped = sql.strip()
    if stripped.endswith(";"):
        without_last = stripped[:-1]
        if _has_unquoted_semicolon(without_last):
            raise ValueError("Only a single read-only statement is allowed.")
        return without_last.strip()
    if _has_unquoted_semicolon(stripped):
        raise ValueError("Only a single read-only statement is allowed.")
    return stripped


def _validate_read_only_query(query: str) -> str:
    if not query or not query.strip():
        raise ValueError("Query is required.")

    if "--" in query or "/*" in query or "*/" in query:
        raise ValueError("SQL comments are not allowed in TA queries.")

    cleaned = _strip_single_trailing_semicolon(query)
    lowered = cleaned.lstrip().lower()

    if not lowered.startswith("select ") and not lowered.startswith("with "):
        raise ValueError("Only read-only SELECT queries are allowed.")

    if FORBIDDEN_SQL_RE.search(cleaned):
        raise ValueError("Query contains a forbidden non-read-only SQL command.")

    if re.search(r"\bfor\s+(update|share|no\s+key\s+update|key\s+share)\b", cleaned, re.IGNORECASE):
        raise ValueError("Row-locking clauses are not allowed.")

    return cleaned


def _limited_query(query: str) -> str:
    row_cap = MAX_RESULT_ROWS if re.search(r"\blimit\s+\d+\b", query, re.IGNORECASE) else DEFAULT_RESULT_ROWS
    return f"SELECT * FROM ({query}) AS ta_readonly_result LIMIT {row_cap + 1}"


def _query_row_cap(query: str) -> int:
    return MAX_RESULT_ROWS if re.search(r"\blimit\s+\d+\b", query, re.IGNORECASE) else DEFAULT_RESULT_ROWS


def _preview_query(query: str) -> str:
    compact = " ".join(query.split())
    return compact[:500] + ("..." if len(compact) > 500 else "")


def _preview_params(params: tuple[Any, ...]) -> str:
    safe_params = [_json_safe(param) for param in params]
    return json.dumps(safe_params)


def _current_teacher_id() -> str:
    return _ta_teacher_id.get("")


def _require_teacher_id() -> Optional[str]:
    teacher_id = _current_teacher_id()
    return teacher_id or None


def _execute_readonly_query(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    _log(f"query: {_preview_query(query)} params={_preview_params(params)}")
    with get_db_connection() as conn:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 10000")
            cur.execute(query, params)
            rows = [_redact_row(dict(row)) for row in cur.fetchall()]
            _log(f"result: {json.dumps({'row_count': len(rows), 'rows': rows})}")
            return rows


def _extract_teacher_facing_student_id(student_ref: str) -> str:
    match = re.search(r"\b\d{4,}\b", student_ref or "")
    return match.group(0) if match else ""


def _resolve_student(student_ref: str) -> dict[str, Any]:
    teacher_id = _require_teacher_id()
    if not teacher_id:
        return {"error": "teacher_id is not available in TA context"}

    ref = (student_ref or "").strip()
    if not ref:
        return {"error": "student_ref is required"}

    extracted_student_id = _extract_teacher_facing_student_id(ref)
    exact_ref = extracted_student_id or ref

    exact_rows = _execute_readonly_query(
        """
        SELECT id::text AS internal_student_uuid, student_id, name, created_at
        FROM public.students
        WHERE teacher_id = %s
          AND (student_id = %s OR id::text = %s OR LOWER(name) = LOWER(%s))
        ORDER BY
          CASE
            WHEN student_id = %s THEN 0
            WHEN id::text = %s THEN 1
            WHEN LOWER(name) = LOWER(%s) THEN 2
            ELSE 3
          END,
          created_at DESC
        LIMIT 5
        """,
        (teacher_id, exact_ref, exact_ref, ref, exact_ref, exact_ref, ref),
    )

    if len(exact_rows) == 1:
        return {"student": exact_rows[0]}
    if len(exact_rows) > 1:
        return {"multiple_matches": exact_rows}

    partial_rows = _execute_readonly_query(
        """
        SELECT id::text AS internal_student_uuid, student_id, name, created_at
        FROM public.students
        WHERE teacher_id = %s
          AND (name ILIKE %s OR student_id ILIKE %s)
        ORDER BY
          CASE WHEN student_id = %s THEN 0 WHEN name ILIKE %s THEN 1 ELSE 2 END,
          name ASC,
          student_id ASC
        LIMIT 5
        """,
        (teacher_id, f"%{ref}%", f"%{ref}%", exact_ref, f"{ref}%"),
    )

    if len(partial_rows) == 1:
        return {"student": partial_rows[0]}
    if len(partial_rows) > 1:
        return {"multiple_matches": partial_rows}

    return {"error": f"No student found for reference: {student_ref}"}


def _resolve_assignment(assignment_id: Optional[int] = None, assignment_ref: str = "") -> dict[str, Any]:
    teacher_id = _require_teacher_id()
    if not teacher_id:
        return {"error": "teacher_id is not available in TA context"}

    if assignment_id:
        rows = _execute_readonly_query(
            """
            SELECT id, title, subject, total_marks, created_at
            FROM public.assignments
            WHERE teacher_id = %s AND id = %s
            LIMIT 1
            """,
            (teacher_id, assignment_id),
        )
    else:
        ref = (assignment_ref or "").strip()
        if not ref:
            return {"assignment": None}
        rows = _execute_readonly_query(
            """
            SELECT id, title, subject, total_marks, created_at
            FROM public.assignments
            WHERE teacher_id = %s
              AND (LOWER(title) = LOWER(%s) OR title ILIKE %s OR subject ILIKE %s)
            ORDER BY
              CASE WHEN LOWER(title) = LOWER(%s) THEN 0 WHEN title ILIKE %s THEN 1 ELSE 2 END,
              created_at DESC,
              id DESC
            LIMIT 5
            """,
            (teacher_id, ref, f"%{ref}%", f"%{ref}%", ref, f"{ref}%"),
        )

    if len(rows) == 1:
        return {"assignment": rows[0]}
    if len(rows) > 1:
        return {"multiple_matches": rows}
    return {"error": "Assignment not found"}


class SchemaInput(BaseModel):
    table_names: str = Field(
        ...,
        description="Comma-separated table names, optionally schema-qualified, for example: students, assignments",
    )


class QueryInput(BaseModel):
    query: str = Field(..., description="A single read-only PostgreSQL SELECT query.")


class StudentResultInput(BaseModel):
    student_ref: str = Field(..., description="Student name, teacher-facing student ID, or internal UUID if already known.")
    assignment_id: Optional[int] = Field(default=None, description="Optional assignment primary key.")
    assignment_ref: str = Field(default="", description="Optional assignment title/subject reference if assignment_id is unknown.")


class StudentQuestionBreakdownInput(BaseModel):
    student_ref: str = Field(..., description="Student name, teacher-facing student ID, or internal UUID if already known.")
    assignment_id: Optional[int] = Field(default=None, description="Optional assignment primary key.")
    assignment_ref: str = Field(default="", description="Optional assignment title/subject reference if assignment_id is unknown.")


class CommonMistakesInput(BaseModel):
    assignment_id: Optional[int] = Field(default=None, description="Optional assignment primary key.")
    assignment_ref: str = Field(default="", description="Optional assignment title/subject reference if assignment_id is unknown.")
    student_ref: str = Field(default="", description="Optional student filter for one student's mistakes.")
    limit: int = Field(default=10, ge=1, le=25, description="Maximum grouped mistakes to return.")


def _friendly_student(student: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": student.get("name"),
        "student_id": student.get("student_id"),
        "created_at": student.get("created_at"),
    }


def _friendly_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_friendly_student(candidate) for candidate in candidates]


def _student_resolution_response(resolution: dict[str, Any]) -> Optional[str]:
    if "student" in resolution:
        return None
    if "multiple_matches" in resolution:
        return json.dumps({
            "status": "multiple_student_matches",
            "message": "Multiple students matched. Ask the teacher to choose by student_id.",
            "candidates": _friendly_candidates(resolution["multiple_matches"]),
        })
    return json.dumps({"status": "not_found", "error": resolution.get("error", "Student not found")})


def _assignment_resolution_response(resolution: dict[str, Any]) -> Optional[str]:
    if "assignment" in resolution:
        return None
    if "multiple_matches" in resolution:
        return json.dumps({
            "status": "multiple_assignment_matches",
            "message": "Multiple assignments matched. Ask the teacher to choose by assignment title or id.",
            "candidates": resolution["multiple_matches"],
        })
    return json.dumps({"status": "not_found", "error": resolution.get("error", "Assignment not found")})


@tool("get_student_result", args_schema=StudentResultInput)
def get_student_result(student_ref: str, assignment_id: Optional[int] = None, assignment_ref: str = "") -> str:
    """Resolve a student and return assignment-level result totals computed by SQL aggregates."""
    teacher_id = _require_teacher_id()
    if not teacher_id:
        return json.dumps({"status": "error", "error": "teacher_id is not available in TA context"})

    student_resolution = _resolve_student(student_ref)
    early_response = _student_resolution_response(student_resolution)
    if early_response:
        return early_response

    student = student_resolution["student"]
    assignment = None
    if assignment_id or assignment_ref.strip():
        assignment_resolution = _resolve_assignment(assignment_id, assignment_ref)
        early_response = _assignment_resolution_response(assignment_resolution)
        if early_response:
            return early_response
        assignment = assignment_resolution["assignment"]

    assignment_filter = "AND a.id = %s" if assignment else ""
    params: tuple[Any, ...] = (
        teacher_id,
        student["internal_student_uuid"],
        student["student_id"],
        *(((assignment or {}).get("id"),) if assignment else ()),
    )
    rows = _execute_readonly_query(
        f"""
        SELECT
          a.id AS assignment_id,
          a.title AS assignment_title,
          a.subject,
          a.total_marks AS assignment_total_marks,
          SUM(sqs.marks)::float AS marks_obtained,
          COUNT(*)::int AS graded_question_count,
          MAX(sqs.updated_at) AS latest_score_update
        FROM public.student_question_scores sqs
        INNER JOIN public.assignments a
          ON a.id = sqs.assignment_id
          AND a.teacher_id = %s
        WHERE (sqs.student_id = %s OR sqs.student_id = %s)
          {assignment_filter}
        GROUP BY a.id, a.title, a.subject, a.total_marks
        ORDER BY a.id DESC
        """,
        params,
    )

    return json.dumps({
        "status": "ok",
        "evidence_query_used": True,
        "student": _friendly_student(student),
        "assignment_filter": assignment,
        "result_count": len(rows),
        "results": rows,
        "instructions": "Use marks_obtained and graded_question_count exactly as returned; do not recalculate marks.",
    })


@tool("get_student_question_breakdown", args_schema=StudentQuestionBreakdownInput)
def get_student_question_breakdown(
    student_ref: str,
    assignment_id: Optional[int] = None,
    assignment_ref: str = "",
) -> str:
    """Return per-question score rows for one resolved student assignment, with SQL-computed marks summary."""
    teacher_id = _require_teacher_id()
    if not teacher_id:
        return json.dumps({"status": "error", "error": "teacher_id is not available in TA context"})

    student_resolution = _resolve_student(student_ref)
    early_response = _student_resolution_response(student_resolution)
    if early_response:
        return early_response
    student = student_resolution["student"]

    if assignment_id or assignment_ref.strip():
        assignment_resolution = _resolve_assignment(assignment_id, assignment_ref)
        early_response = _assignment_resolution_response(assignment_resolution)
        if early_response:
            return early_response
        assignment = assignment_resolution["assignment"]
    else:
        result_payload = json.loads(get_student_result.invoke({"student_ref": student_ref}))
        results = result_payload.get("results", [])
        if len(results) != 1:
            return json.dumps({
                "status": "needs_assignment",
                "student": _friendly_student(student),
                "message": "Student has multiple or zero graded assignments. Ask which assignment to break down.",
                "available_results": results,
            })
        assignment = {"id": results[0]["assignment_id"], "title": results[0]["assignment_title"]}

    rows = _execute_readonly_query(
        """
        SELECT
          sqs.question_label,
          sqs.question_text,
          sqs.student_solution,
          sqs.marks::float AS marks,
          sqs.confidence_score::float AS confidence_score,
          sqs.ai_comment,
          sqs.teacher_comment,
          sqs.created_at,
          sqs.updated_at
        FROM public.student_question_scores sqs
        WHERE sqs.teacher_id = %s
          AND sqs.assignment_id = %s
          AND (sqs.student_id = %s OR sqs.student_id = %s)
        ORDER BY sqs.id ASC
        """,
        (teacher_id, assignment["id"], student["internal_student_uuid"], student["student_id"]),
    )

    marks_sum = sum(float(row.get("marks") or 0) for row in rows)
    return json.dumps({
        "status": "ok",
        "evidence_query_used": True,
        "student": _friendly_student(student),
        "assignment": assignment,
        "marks_obtained": marks_sum,
        "graded_question_count": len(rows),
        "question_breakdown": rows,
        "instructions": "Use marks_obtained and graded_question_count exactly as returned; do not recalculate marks.",
    })


@tool("get_common_mistakes", args_schema=CommonMistakesInput)
def get_common_mistakes(
    assignment_id: Optional[int] = None,
    assignment_ref: str = "",
    student_ref: str = "",
    limit: int = 10,
) -> str:
    """Return grouped AI-comment mistake patterns, optionally scoped to one assignment or student."""
    teacher_id = _require_teacher_id()
    if not teacher_id:
        return json.dumps({"status": "error", "error": "teacher_id is not available in TA context"})

    assignment = None
    if assignment_id or assignment_ref.strip():
        assignment_resolution = _resolve_assignment(assignment_id, assignment_ref)
        early_response = _assignment_resolution_response(assignment_resolution)
        if early_response:
            return early_response
        assignment = assignment_resolution["assignment"]

    student = None
    if student_ref.strip():
        student_resolution = _resolve_student(student_ref)
        early_response = _student_resolution_response(student_resolution)
        if early_response:
            return early_response
        student = student_resolution["student"]

    filters = ["sqs.teacher_id = %s", "sqs.ai_comment IS NOT NULL", "btrim(sqs.ai_comment) <> ''"]
    params: list[Any] = [teacher_id]
    if assignment:
        filters.append("sqs.assignment_id = %s")
        params.append(assignment["id"])
    if student:
        filters.append("(sqs.student_id = %s OR sqs.student_id = %s)")
        params.extend([student["internal_student_uuid"], student["student_id"]])
    params.append(limit)

    rows = _execute_readonly_query(
        f"""
        SELECT
          sqs.question_label,
          sqs.ai_comment,
          COUNT(*)::int AS affected_count,
          AVG(sqs.marks)::float AS average_marks,
          json_agg(
            json_build_object(
              'student_id', students.student_id,
              'name', students.name,
              'marks', sqs.marks
            )
            ORDER BY students.name ASC
          ) AS affected_students
        FROM public.student_question_scores sqs
        LEFT JOIN public.students
          ON students.teacher_id = sqs.teacher_id
          AND (sqs.student_id = students.id::text OR sqs.student_id = students.student_id)
        WHERE {' AND '.join(filters)}
        GROUP BY sqs.question_label, sqs.ai_comment
        ORDER BY affected_count DESC, sqs.question_label ASC
        LIMIT %s
        """,
        tuple(params),
    )

    return json.dumps({
        "status": "ok",
        "evidence_query_used": True,
        "assignment_filter": assignment,
        "student_filter": _friendly_student(student) if student else None,
        "mistake_count": len(rows),
        "mistakes": rows,
    })


@tool("sql_db_list_tables")
def sql_db_list_tables() -> str:
    """Return a comma-separated list of known public tables in the Assess-AI database."""
    return ", ".join(f"public.{name}" for name in SCHEMA.keys())


@tool("sql_db_schema", args_schema=SchemaInput)
def sql_db_schema(table_names: str) -> str:
    """Return schema details and relationship hints for comma-separated Assess-AI table names."""
    requested_tables = _split_requested_tables(table_names)
    if not requested_tables:
        return json.dumps({"error": "At least one table name is required."})

    results: list[dict[str, Any]] = []
    for table in requested_tables:
        columns = SCHEMA.get(table)
        if columns is None:
            results.append({
                "table": table,
                "error": f"Table not found. Known tables: {', '.join(SCHEMA.keys())}",
            })
            continue

        sample_rows: list[dict[str, Any]] = []
        try:
            with get_db_connection() as conn:
                conn.set_session(readonly=True, autocommit=True)
                with conn.cursor() as cur:
                    cur.execute("SET statement_timeout = 5000")
                    quoted_table = '"' + table.replace('"', '""') + '"'
                    cur.execute(f'SELECT * FROM public.{quoted_table} LIMIT 3')
                    sample_rows = [_redact_row(dict(row)) for row in cur.fetchall()]
        except Exception as e:
            sample_rows = [{"error": f"Could not fetch sample rows: {e}"}]

        results.append({
            "table": f"public.{table}",
            "primary_key": PRIMARY_KEYS.get(table, []),
            "columns": columns,
            "sample_rows": sample_rows,
        })

    return json.dumps({
        "tables": results,
        "relationship_hints": RELATIONSHIP_HINTS,
    })


@tool("sql_db_query", args_schema=QueryInput)
def sql_db_query(query: str) -> str:
    """Execute one single read-only PostgreSQL SELECT query and return capped, redacted rows."""
    try:
        cleaned_query = _validate_read_only_query(query)
    except ValueError as e:
        _log(f"query rejected error={e}")
        return json.dumps({"error": str(e)})

    try:
        row_cap = _query_row_cap(cleaned_query)
        _log(f"query: {_preview_query(cleaned_query)}")
        with get_db_connection() as conn:
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = 10000")
                cur.execute(_limited_query(cleaned_query))
                fetched_rows = cur.fetchall()
                result_limited = len(fetched_rows) > row_cap
                rows = [_redact_row(dict(row)) for row in fetched_rows[:row_cap]]
                columns = [description[0] for description in cur.description] if cur.description else []
                result = {
                    "columns": columns,
                    "row_count": len(rows),
                    "max_rows": MAX_RESULT_ROWS,
                    "result_limited": result_limited,
                    "numeric_column_summaries": _numeric_column_summaries(rows),
                    "warning": (
                        "Result was capped by sql_db_query; do not compute totals from this partial result."
                        if result_limited
                        else ""
                    ),
                    "rows": rows,
                }
                result_json = json.dumps(result)
                _log(f"result: {result_json}")
                return result_json
    except Exception as e:
        _log(f"query error: {e}")
        return json.dumps({"error": str(e)})


tools = [
    get_student_result,
    get_student_question_breakdown,
    get_common_mistakes,
    sql_db_list_tables,
    sql_db_schema,
    sql_db_query,
]
