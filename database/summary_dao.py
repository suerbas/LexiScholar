"""Code Summary Data Access Object for LexiScholar."""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class CodeSummaryDAO:
    """Data Access Object for Code Summaries (Grid)."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def upsert(self, document_id: int, code_id: int, content: str) -> bool:
        """Insert or update a summary."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO code_summaries (document_id, code_id, content, modified_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(document_id, code_id) DO UPDATE SET 
                        content = EXCLUDED.content,
                        modified_at = EXCLUDED.modified_at
                """, (document_id, code_id, content, datetime.now()))
                conn.commit()
                return True
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to upsert summary: {e}")
            return False
    
    def get_summary(self, document_id: int, code_id: int) -> Optional[str]:
        """Get summary content for a specific cell."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content FROM code_summaries 
                    WHERE document_id = ? AND code_id = ?
                """, (document_id, code_id))
                row = cursor.fetchone()
                return row['content'] if row else None
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get summary: {e}")
            return None

    def get_all_summaries(self) -> List[dict]:
        """Get all summaries as a list of dicts."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM code_summaries")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get all summaries: {e}")
            return []
