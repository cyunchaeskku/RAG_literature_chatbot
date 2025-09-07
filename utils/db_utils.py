"""
데이터베이스 관련 유틸리티 함수를 모아놓은 파일입니다.

SQLite 데이터베이스에 연결하고, 작품 목록을 가져오거나 특정 작품의
상세 정보를 조회하는 등의 기능을 수행하는 함수들을 포함합니다.
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from contextlib import contextmanager

# Define the path to the database relative to the project root
DB_PATH = Path(__file__).parent.parent / "data" / "literature.db"

@contextmanager
def get_db_connection():
    """Provides a database connection using a context manager."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_all_literatures() -> List[Dict[str, Any]]:
    """
    Retrieves a list of all literature metadata (id, title, author, etc.)
    from the database.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, publish_year, language FROM literature ORDER BY title")
        literatures = [dict(row) for row in cursor.fetchall()]
    return literatures

def get_literature_details_by_titles(titles: List[str]) -> List[Dict[str, str]]:
    """
    Retrieves the body and language for a given list of literature titles.
    
    Args:
        titles: A list of literature titles to fetch.
        
    Returns:
        A list of dictionaries, each containing 'body' and 'language'.
    """
    if not titles:
        return []
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        placeholders = ', '.join('?' for _ in titles)
        query = f"SELECT body, language FROM literature WHERE title IN ({placeholders})"
        cursor.execute(query, titles)
        details = [dict(row) for row in cursor.fetchall()]
    
    return details
