import os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
DB_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_db_connection():
    """
    Creates a new database connection. 
    Using RealDictCursor means your SQL results come back as Python dictionaries 
    (e.g., row['extracted_text']) instead of confusing tuples!
    """
    if not DB_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()
