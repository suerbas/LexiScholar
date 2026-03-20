"""Document Data Access Object for LexiScholar."""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class DocumentDAO:
    """Data Access Object for Document operations."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def create(self, title: str, file_path: str, file_type: str, 
               extracted_text: str, folder_id: Optional[int] = None) -> int:
        """Create a new document and return its ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO documents (title, file_path, file_type, extracted_text, folder_id, order_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, file_path, file_type, extracted_text, folder_id, 0))
                doc_id = cursor.lastrowid
                conn.commit()
                return doc_id
        except sqlite3.IntegrityError as e:
            if "CHECK constraint failed" in str(e).lower() or "file_type" in str(e).lower():
                logger.warning("Caught legacy CHECK constraint error. Forcing schema update and retrying...")
                try:
                    from .connection import init_db
                    init_db(self.db_path)
                    
                    # Retry insert after migration
                    with get_db_connection(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO documents (title, file_path, file_type, extracted_text, folder_id, order_index)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (title, file_path, file_type, extracted_text, folder_id, 0))
                        doc_id = cursor.lastrowid
                        conn.commit()
                        return doc_id
                except Exception as retry_e:
                    logger.error(f"Retry failed after fixing constraints: {retry_e}")
                    raise DatabaseError(f"Failed to update database schema:\n{e}\n{retry_e}")

            logger.warning(f"Document already exists: {file_path}. Error: {e}")
            raise DatabaseError(f"Database error (document might already exist):\n{e}")
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise DatabaseError(f"Failed to create document: {str(e)}")
    
    def get_by_id(self, doc_id: int) -> Optional[dict]:
        """Get document by ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None
    
    def get_all(self, folder_id: Optional[int] = None) -> List[dict]:
        """
        Get all documents, optionally filtered by folder.
        Optimized to return only metadata and a small snippet for performance.
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                # We only fetch a snippet (first 1000 chars) instead of the whole text to speed up the tree loading
                query = """
                    SELECT id, title, file_path, file_type, folder_id, is_active, order_index,
                           SUBSTR(extracted_text, 1, 1000) as extracted_text
                    FROM documents
                """
                if folder_id is not None:
                    cursor.execute(f"{query} WHERE folder_id = ? ORDER BY order_index, title", (folder_id,))
                else:
                    cursor.execute(f"{query} ORDER BY order_index, title")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []
    
    def delete(self, doc_id: int) -> bool:
        """Delete a document. Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise DatabaseError(f"Failed to delete document (ID: {doc_id}): {str(e)}")

    def move_to_folder(self, doc_id: int, folder_id: Optional[int]) -> bool:
        """Move document to a folder (or root if folder_id is None)."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE documents SET folder_id = ? WHERE id = ?", (folder_id, doc_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to move document {doc_id}: {e}")
            raise DatabaseError(f"Failed to move document: {str(e)}")

    def update_order(self, doc_id: int, new_order: int) -> bool:
        """Update the display order of a document."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE documents SET order_index = ? WHERE id = ?", (new_order, doc_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update document order: {e}")
            return False

    def set_active(self, doc_id: int, is_active: bool) -> bool:
        """Set activation status of a document."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE documents SET is_active = ? WHERE id = ?", (1 if is_active else 0, doc_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to set active status for document {doc_id}: {e}")
            return False

    def set_all_active(self, is_active: bool) -> bool:
        """Set activation status for all documents."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE documents SET is_active = ?", (int(is_active),))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to set all documents active status: {e}")
            return False

    def get_active_ids(self) -> List[int]:
        """Get IDs of all active documents."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM documents WHERE is_active = 1")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get active document IDs: {e}")
            return []

    def reset_activation(self) -> bool:
        """Deactivate all documents."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE documents SET is_active = 0")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to reset document activation: {e}")
            return False

    def update_content(self, doc_id: int, new_content: str) -> bool:
        """Update the content (extracted_text) of a document."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE documents SET extracted_text = ?, modified_at = ? WHERE id = ?",
                    (new_content, datetime.now().isoformat(), doc_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update document content: {e}")
            raise DatabaseError(f"Failed to update document content: {str(e)}")

    def rename(self, doc_id: int, new_title: str) -> bool:
        """Update the title of a document."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE documents SET title = ? WHERE id = ?", (new_title, doc_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to rename document {doc_id}: {e}")
            return False

    def search_fulltext(self, query: str, limit: int = 50) -> List[dict]:
        """Full-text search across document titles and content using FTS5.
        Falls back to LIKE search if FTS5 is unavailable.
        Returns list of dicts with document metadata and a 'snippet' field.
        """
        if not query or not query.strip():
            return []
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                # Try FTS5 first
                try:
                    cursor.execute(
                        """SELECT d.id, d.title, d.file_type, d.folder_id,
                                  snippet(documents_fts, 1, '<b>', '</b>', '…', 20) AS snippet
                           FROM documents_fts
                           JOIN documents d ON documents_fts.rowid = d.id
                           WHERE documents_fts MATCH ?
                           ORDER BY rank
                           LIMIT ?""",
                        (query, limit)
                    )
                except Exception:
                    # FTS5 not available — fall back to LIKE
                    like = f"%{query}%"
                    cursor.execute(
                        """SELECT id, title, file_type, folder_id,
                                  SUBSTR(extracted_text, MAX(1, INSTR(LOWER(extracted_text), LOWER(?)) - 60), 140) AS snippet
                           FROM documents
                           WHERE LOWER(title) LIKE LOWER(?) OR LOWER(extracted_text) LIKE LOWER(?)
                           LIMIT ?""",
                        (query, like, like, limit)
                    )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Full-text search failed: {e}")
            return []
