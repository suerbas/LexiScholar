"""Memo Data Access Object for LexiScholar."""

import sqlite3
import logging
from typing import Optional, List
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class MemoDAO:
    """Data Access Object for Memo operations."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def create(self, content: str, title: str = None, document_id: Optional[int] = None,
               segment_id: Optional[int] = None, code_id: Optional[int] = None,
               start_pos: Optional[int] = None, end_pos: Optional[int] = None,
               coder_id: int = 1, force_id: Optional[int] = None) -> int:
        """Create a new memo attached to a document, segment, code, or text position."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                if force_id is not None:
                    # Insert with specific ID for undo/redo operations
                    cursor.execute("""
                        INSERT INTO memos (id, title, content, document_id, segment_id, code_id, coder_id, start_pos, end_pos)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (force_id, title, content, document_id, segment_id, code_id, coder_id, start_pos, end_pos))
                    memo_id = force_id
                else:
                    # Normal insert with auto-generated ID
                    cursor.execute("""
                        INSERT INTO memos (title, content, document_id, segment_id, code_id, coder_id, start_pos, end_pos)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (title, content, document_id, segment_id, code_id, coder_id, start_pos, end_pos))
                    memo_id = cursor.lastrowid
                    
                conn.commit()
                return memo_id
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to create memo: {e}")
            raise DatabaseError(f"Failed to create memo: {e}")

    def get_by_document(self, document_id: int, coder_id: int = None) -> List[dict]:
        """Get all memos for a document, optionally filtered by coder."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                sql = "SELECT * FROM memos WHERE document_id = ?"
                params = [document_id]
                
                if coder_id is not None:
                    sql += " AND coder_id = ?"
                    params.append(coder_id)
                    
                sql += " ORDER BY start_pos ASC, created_at DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get memos for document {document_id}: {e}")
            return []

    def get_general_document_memo(self, document_id: int) -> Optional[dict]:
        """Get the general memo for a document (one where start_pos is NULL)."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM memos 
                    WHERE document_id = ? AND start_pos IS NULL 
                    LIMIT 1
                """, (document_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get general memo for document {document_id}: {e}")
            return None

    def get_by_id(self, memo_id: int) -> Optional[dict]:
        """Get a memo by its ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get memo {memo_id}: {e}")
            return None

    def get_by_code(self, code_id: int) -> Optional[dict]:
        """Get the memo for a code."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memos WHERE code_id = ? LIMIT 1", (code_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get memo for code {code_id}: {e}")
            return None
    
    def get_all(self) -> List[dict]:
        """Get all memos (sorted by modification time)."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.*, d.title as doc_title
                    FROM memos m
                    LEFT JOIN documents d ON m.document_id = d.id
                    ORDER BY m.modified_at DESC
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get all memos: {e}")
            return []

    def update(self, memo_id: int, content: str = None, title: str = None) -> bool:
        """Update memo content and/or title. Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates = []
                params = []
                
                if content is not None:
                    updates.append("content = ?")
                    params.append(content)
                    
                if title is not None:
                    updates.append("title = ?")
                    params.append(title)
                    
                if not updates:
                    return False
                    
                updates.append("modified_at = CURRENT_TIMESTAMP")
                params.append(memo_id)
                
                sql = f"UPDATE memos SET {', '.join(updates)} WHERE id = ?"
                
                cursor.execute(sql, params)
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to update memo {memo_id}: {e}")
            return False
    
    def delete(self, memo_id: int) -> bool:
        """Delete a memo. Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to delete memo {memo_id}: {e}")
            return False
