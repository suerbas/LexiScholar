"""Folder Data Access Object for LexiScholar."""

import sqlite3
import logging
from typing import Optional, List
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class FolderDAO:
    """Data Access Object for Folder operations."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def create(self, name: str, parent_id: Optional[int] = None) -> int:
        """Create a new folder."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO folders (name, parent_id, order_index) VALUES (?, ?, ?)", (name, parent_id, 0))
                folder_id = cursor.lastrowid
                conn.commit()
                return folder_id
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to create folder: {e}")
            raise DatabaseError(f"Failed to create folder: {e}")

    def get_by_id(self, folder_id: int) -> Optional[dict]:
        """Get folder by ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get folder {folder_id}: {e}")
            return None

    def get_all(self) -> List[dict]:
        """Get all folders."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM folders ORDER BY order_index, name")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get folders: {e}")
            return []
    
    def update(self, folder_id: int, name: str) -> bool:
        """Update folder name."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE folders SET name = ? WHERE id = ?", (name, folder_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to update folder {folder_id}: {e}")
            return False

    def delete(self, folder_id: int) -> bool:
        """Delete a folder (documents are moved to root/null)."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to delete folder {folder_id}: {e}")
            return False

    def move_to_folder(self, folder_id: int, parent_id: Optional[int]) -> bool:
        """Move folder to a parent folder or root."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE folders SET parent_id = ? WHERE id = ?", (parent_id, folder_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to move folder {folder_id}: {e}")
            return False

    def update_order(self, folder_id: int, new_order: int) -> bool:
        """Update folder display order."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE folders SET order_index = ? WHERE id = ?", (new_order, folder_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to update folder order: {e}")
            return False
