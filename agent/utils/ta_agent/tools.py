import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from config.db import get_db_connection


MAX_RESULT_ROWS = 50
DEFAULT_RESULT_ROWS = MAX_RESULT_ROWS
REDACTED = "[REDACTED]"

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


def set_ta_auth_context(access_token: str = "") -> None:
    """Compatibility no-op; TA SQL tools use DATABASE_URL, not backend auth."""
    return None


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


class SchemaInput(BaseModel):
    table_names: str = Field(
        ...,
        description="Comma-separated table names, optionally schema-qualified, for example: students, assignments",
    )


class QueryInput(BaseModel):
    query: str = Field(..., description="A single read-only PostgreSQL SELECT query.")


@tool("sql_db_list_tables")
def sql_db_list_tables() -> str:
    """Return a comma-separated list of known public tables in the Assess-AI database."""
    _log("sql_db_list_tables called")
    return ", ".join(f"public.{name}" for name in SCHEMA.keys())


@tool("sql_db_schema", args_schema=SchemaInput)
def sql_db_schema(table_names: str) -> str:
    """Return schema details and relationship hints for comma-separated Assess-AI table names."""
    requested_tables = _split_requested_tables(table_names)
    _log(f"sql_db_schema requested_tables={requested_tables}")
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
        _log(f"sql_db_query rejected error={e}")
        return json.dumps({"error": str(e)})

    try:
        row_cap = _query_row_cap(cleaned_query)
        _log(f"sql_db_query executing row_cap={row_cap} query={_preview_query(cleaned_query)}")
        with get_db_connection() as conn:
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = 10000")
                cur.execute(_limited_query(cleaned_query))
                fetched_rows = cur.fetchall()
                result_limited = len(fetched_rows) > row_cap
                rows = [_redact_row(dict(row)) for row in fetched_rows[:row_cap]]
                columns = [description[0] for description in cur.description] if cur.description else []
                _log(
                    "sql_db_query completed "
                    f"returned_rows={len(rows)} result_limited={result_limited} columns={columns}"
                )
                return json.dumps({
                    "columns": columns,
                    "row_count": len(rows),
                    "max_rows": MAX_RESULT_ROWS,
                    "result_limited": result_limited,
                    "warning": (
                        "Result was capped by sql_db_query; do not compute totals from this partial result."
                        if result_limited
                        else ""
                    ),
                    "rows": rows,
                })
    except Exception as e:
        _log(f"sql_db_query error={e}")
        return json.dumps({"error": str(e)})


tools = [sql_db_list_tables, sql_db_schema, sql_db_query]
