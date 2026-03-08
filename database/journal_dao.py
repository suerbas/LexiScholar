"""Project Journal Data Access Object for LexiScholar."""

import sqlite3
import logging
from datetime import datetime
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class ProjectJournalDAO:
    """Data Access Object for Project Journal."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
        self._ensure_exists()
    
    def _ensure_exists(self):
        """Ensure the journal row exists."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS project_journal (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, created_at TIMESTAMP, updated_at TIMESTAMP)")
                cursor.execute("SELECT id FROM project_journal WHERE id = 1")
                if not cursor.fetchone():
                    now = datetime.now()
                    cursor.execute("INSERT INTO project_journal (id, content, created_at, updated_at) VALUES (1, '', ?, ?)", (now, now))
                    conn.commit()
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to ensure journal existence: {e}")
            # This is critical, maybe we should raise? But logging is safe for init.
    
    def get_content(self) -> str:
        """Get the journal content."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT content FROM project_journal WHERE id = 1")
                row = cursor.fetchone()
                return row['content'] if row else ""
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get journal content: {e}")
            return ""
    
    def save_content(self, content: str) -> bool:
        """Save the journal content."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE project_journal SET content = ?, updated_at = ? WHERE id = 1",
                    (content, datetime.now())
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to save journal content: {e}")
            return False
