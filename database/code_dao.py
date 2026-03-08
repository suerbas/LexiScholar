"""Code Data Access Object for LexiScholar."""

import sqlite3
import logging
from typing import Optional, List
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class CodeDAO:
    """Data Access Object for Code (tag) operations."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def create(self, name: str, color: str = "#3498db", 
               description: str = "", parent_id: Optional[int] = None, force_id: Optional[int] = None) -> int:
        """Create a new code and return its ID."""
        if not name or not name.strip():
            raise ValueError("Kod adı boş olamaz")
        if len(name) > 200:
            raise ValueError("Kod adı 200 karakterden uzun olamaz")
            
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                if force_id is not None:
                    # Insert with specific ID for undo/redo operations
                    cursor.execute("""
                        INSERT INTO codes (id, name, color, description, parent_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (force_id, name, color, description, parent_id))
                    code_id = force_id
                else:
                    # Normal insert with auto-generated ID
                    cursor.execute("""
                        INSERT INTO codes (name, color, description, parent_id)
                        VALUES (?, ?, ?, ?)
                    """, (name, color, description, parent_id))
                    code_id = cursor.lastrowid
                    
                conn.commit()
                return code_id
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to create code: {e}")
            raise DatabaseError(f"Kod oluşturulamadı: {e}")
    
    def get_all(self) -> List[dict]:
        """Get all codes."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM codes ORDER BY parent_id NULLS FIRST, order_index")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get codes: {e}")
            return []
    
    def get_by_id(self, code_id: int) -> Optional[dict]:
        """Get a code by ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM codes WHERE id = ?", (code_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get code {code_id}: {e}")
            return None

    def get_children(self, parent_id: Optional[int] = None) -> List[dict]:
        """Get child codes of a parent (None for root codes)."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                if parent_id is None:
                    cursor.execute("SELECT * FROM codes WHERE parent_id IS NULL ORDER BY order_index")
                else:
                    cursor.execute("SELECT * FROM codes WHERE parent_id = ? ORDER BY order_index", (parent_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get child codes: {e}")
            return []
    
    def update(self, code_id: int, name: str = None, color: str = None, 
               description: str = None) -> bool:
        """Update code properties. Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                updates = []
                values = []
                if name is not None:
                    updates.append("name = ?")
                    values.append(name)
                if color is not None:
                    updates.append("color = ?")
                    values.append(color)
                if description is not None:
                    updates.append("description = ?")
                    values.append(description)
                if updates:
                    values.append(code_id)
                    cursor.execute(f"UPDATE codes SET {', '.join(updates)} WHERE id = ?", values)
                    conn.commit()
                return True
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to update code {code_id}: {e}")
            return False
    
    def delete(self, code_id: int) -> bool:
        """Delete a code (cascades to segments). Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM codes WHERE id = ?", (code_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to delete code {code_id}: {e}")
            return False

    def set_active(self, code_id: int, is_active: bool) -> bool:
        """Set activation status of a code."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE codes SET is_active = ? WHERE id = ?", (1 if is_active else 0, code_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to set active status for code {code_id}: {e}")
            return False

    def set_all_active(self, is_active: bool) -> bool:
        """Set activation status for all codes."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE codes SET is_active = ?", (int(is_active),))
                conn.commit()
                return True
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to set all codes active status: {e}")
            return False

    def get_active_ids(self) -> List[int]:
        """Get IDs of all active codes."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM codes WHERE is_active = 1")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get active code IDs: {e}")
            return []

    def reset_activation(self) -> bool:
        """Deactivate all codes."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE codes SET is_active = 0")
                conn.commit()
                return True
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to reset code activation: {e}")
            return False

    def get_code_frequencies(self, active_only: bool = False) -> List[tuple]:
        """Get code usage frequencies (code_name, count)."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                query = """
                    SELECT c.name, COUNT(cs.id) as count
                    FROM codes c
                    LEFT JOIN coded_segments cs ON c.id = cs.code_id
                """
                if active_only:
                    query += " WHERE c.is_active = 1 "
                
                query += " GROUP BY c.id, c.name HAVING count > 0 ORDER BY count DESC"
                
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get code frequencies: {e}")
            return []
