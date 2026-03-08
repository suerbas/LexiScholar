"""Chat Data Access Object for LexiScholar."""

import logging
from typing import List
from .connection import get_db_connection, DatabaseError

logger = logging.getLogger(__name__)

class ChatDAO:
    """Data Access Object for Document AI Chat history."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
        
    def add_message(self, document_id: int, role: str, content: str) -> bool:
        """Add a message to the document's chat history."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO document_chats (document_id, role, content)
                    VALUES (?, ?, ?)
                """, (document_id, role, content))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add chat message for doc {document_id}: {e}")
            return False

    def get_by_document(self, document_id: int) -> List[dict]:
        """Get the full chat history for a document."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content FROM document_chats 
                    WHERE document_id = ? 
                    ORDER BY id ASC
                """, (document_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get chat history for doc {document_id}: {e}")
            return []

    def clear_document_chat(self, document_id: int) -> bool:
        """Delete all chat history for a document."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM document_chats WHERE document_id = ?", (document_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to clear chat for doc {document_id}: {e}")
            return False
