"""Coder Data Access Object for LexiScholar."""

import sqlite3
import logging
from typing import Optional, List
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class CoderDAO:
    """Data Access Object for Coder operations."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def create(self, name: str, color: str = "#3498db", initials: str = "") -> int:
        """Create a new coder and return its ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO coders (name, color, initials) VALUES (?, ?, ?)",
                    (name, color, initials)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create coder: {e}")
            raise DatabaseError(f"Failed to create coder: {str(e)}")
    
    def get_by_id(self, coder_id: int) -> Optional[dict]:
        """Get coder by ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM coders WHERE id = ?", (coder_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get coder {coder_id}: {e}")
            return None
    
    def get_all(self) -> List[dict]:
        """Get all coders."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM coders ORDER BY name")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get coders: {e}")
            return []
    
    def update(self, coder_id: int, name: str, color: str, initials: str) -> bool:
        """Update coder information."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE coders SET name = ?, color = ?, initials = ? WHERE id = ?",
                    (name, color, initials, coder_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update coder {coder_id}: {e}")
            return False
    
    def delete(self, coder_id: int) -> bool:
        """Delete a coder. Segments will be reset to default coder (1)."""
        try:
            if coder_id == 1:
                return False # Cannot delete default coder
                
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM coders WHERE id = ?", (coder_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete coder {coder_id}: {e}")
            return False
