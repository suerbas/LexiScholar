"""Coded Segment Data Access Object for LexiScholar."""

import sqlite3
import logging
from typing import List, Optional
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class CodedSegmentDAO:
    """Data Access Object for Coded Segment operations."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def create(self, document_id: int, code_id: int, 
               start_pos: int, end_pos: int, segment_text: str, weight: int = 3, 
               coder_id: int = 1, force_id: Optional[int] = None) -> int:
        """Create a new coded segment and return its ID."""
        try:
            # Validate weight
            weight = max(1, min(5, weight))
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                if force_id is not None:
                    # Insert with specific ID for undo/redo operations
                    cursor.execute("""
                        INSERT INTO coded_segments (id, document_id, code_id, coder_id, start_pos, end_pos, segment_text, weight)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (force_id, document_id, code_id, coder_id, start_pos, end_pos, segment_text, weight))
                    segment_id = force_id
                else:
                    # Normal insert with auto-generated ID
                    cursor.execute("""
                        INSERT INTO coded_segments (document_id, code_id, coder_id, start_pos, end_pos, segment_text, weight)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (document_id, code_id, coder_id, start_pos, end_pos, segment_text, weight))
                    segment_id = cursor.lastrowid
                    
                conn.commit()
                return segment_id
        except sqlite3.Error as e:
            logger.error(f"Failed to create segment: {e}")
            raise DatabaseError(f"Failed to create segment: {e}")
    
    def update_weight(self, segment_id: int, weight: int) -> bool:
        """Update the weight of a segment. Returns True on success."""
        try:
            weight = max(1, min(5, weight))
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE coded_segments SET weight = ? WHERE id = ?", (weight, segment_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to update segment weight: {e}")
            return False

    def update_paraphrase(self, segment_id: int, paraphrase: str) -> bool:
        """Update (or clear) the paraphrase for a segment. Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE coded_segments SET paraphrase = ? WHERE id = ?",
                    (paraphrase.strip() if paraphrase else None, segment_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to update segment paraphrase: {e}")
            return False

    def update_comment(self, segment_id: int, comment: str) -> bool:
        """Update (or clear) the comment/note for a segment. Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE coded_segments SET comment = ? WHERE id = ?",
                    (comment.strip() if comment else None, segment_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to update segment comment: {e}")
            return False

    
    def get_by_document(self, document_id: int, coder_id: int = None) -> List[dict]:
        """Get all coded segments for a document, optionally filtered by coder."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                sql = """
                    SELECT cs.*, c.name as code_name, c.color as code_color, f.name as folder_name
                    FROM coded_segments cs
                    JOIN codes c ON cs.code_id = c.id
                    JOIN documents d ON cs.document_id = d.id
                    LEFT JOIN folders f ON d.folder_id = f.id
                    WHERE cs.document_id = ?
                """
                params = [document_id]
                
                if coder_id is not None:
                    sql += " AND cs.coder_id = ?"
                    params.append(coder_id)
                    
                sql += " ORDER BY cs.start_pos"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get segments for document {document_id}: {e}")
            return []

    def get_by_documents_bulk(self, doc_ids: List[int], coder_id: int = None) -> dict:
        """Fetch segments for multiple documents in a single query."""
        if not doc_ids:
            return {}
        
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ','.join(['?'] * len(doc_ids))
                sql = f"""
                    SELECT cs.*, c.name as code_name, c.color as code_color, f.name as folder_name
                    FROM coded_segments cs
                    JOIN codes c ON cs.code_id = c.id
                    JOIN documents d ON cs.document_id = d.id
                    LEFT JOIN folders f ON d.folder_id = f.id
                    WHERE cs.document_id IN ({placeholders})
                """
                params = list(doc_ids)
                
                if coder_id is not None:
                    sql += " AND cs.coder_id = ?"
                    params.append(coder_id)
                
                cursor.execute(sql, params)
                
                # Group by document_id
                from collections import defaultdict
                result = defaultdict(list)
                for row in cursor.fetchall():
                    result[row['document_id']].append(dict(row))
                return result
        except sqlite3.Error as e:
            logger.error(f"Bulk fetch segments failed: {e}")
            return {}
    
    def get_by_code(self, code_id: int, coder_id: int = None) -> List[dict]:
        """Get all segments tagged with a specific code, optionally filtered by coder."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                sql = """
                    SELECT cs.*, d.title as document_title, c.name as code_name, c.color as code_color, f.name as folder_name
                    FROM coded_segments cs
                    JOIN documents d ON cs.document_id = d.id
                    JOIN codes c ON cs.code_id = c.id
                    LEFT JOIN folders f ON d.folder_id = f.id
                    WHERE cs.code_id = ?
                """
                params = [code_id]
                
                if coder_id is not None:
                    sql += " AND cs.coder_id = ?"
                    params.append(coder_id)
                
                sql += " ORDER BY d.title, cs.start_pos"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get segments for code {code_id}: {e}")
            return []

    def get_by_active_criteria(self, doc_ids: List[int], code_ids: List[int]) -> List[dict]:
        """
        Get segments that match BOTH active documents and active codes.
        If doc_ids is empty, returns nothing (must have active docs).
        If code_ids is empty, returns nothing (must have active codes).
        """
        if not doc_ids or not code_ids:
            return []
            
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create placeholders
                doc_placeholders = ','.join(['?'] * len(doc_ids))
                code_placeholders = ','.join(['?'] * len(code_ids))
                
                sql = f"""
                    SELECT cs.*, d.title as document_title, c.name as code_name, c.color as code_color, f.name as folder_name
                    FROM coded_segments cs
                    JOIN documents d ON cs.document_id = d.id
                    JOIN codes c ON cs.code_id = c.id
                    LEFT JOIN folders f ON d.folder_id = f.id
                    WHERE cs.document_id IN ({doc_placeholders})
                    AND cs.code_id IN ({code_placeholders})
                    ORDER BY d.title, cs.start_pos
                """
                
                # Combine params
                params = doc_ids + code_ids
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get segments by criteria: {e}")
            return []
    
    def delete(self, segment_id: int) -> bool:
        """Delete a coded segment. Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM coded_segments WHERE id = ?", (segment_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to delete segment {segment_id}: {e}")
            return False
    
    def update_code(self, segment_id: int, new_code_id: int) -> bool:
        """Update the code assigned to a segment (for code merge). Returns True on success."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE coded_segments SET code_id = ? WHERE id = ?", (new_code_id, segment_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to update segment code: {e}")
            return False
    
    def get_by_id(self, segment_id: int):
        """Get a coded segment by its ID."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cs.*, d.title as document_title, c.name as code_name, c.color as code_color, f.name as folder_name
                    FROM coded_segments cs
                    JOIN documents d ON cs.document_id = d.id
                    JOIN codes c ON cs.code_id = c.id
                    LEFT JOIN folders f ON d.folder_id = f.id
                    WHERE cs.id = ?
                """, (segment_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get segment {segment_id}: {e}")
            return None

    def delete_batch(self, segment_ids: list) -> bool:
        """
        Delete multiple segments by their IDs.
        
        Args:
            segment_ids: List of segment IDs to delete
            
        Returns:
            True if successful (even if some IDs were not found), False on error
        """
        if not segment_ids:
            return True
            
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Use param substitution for safety
                placeholders = ','.join(['?'] * len(segment_ids))
                sql = f"DELETE FROM coded_segments WHERE id IN ({placeholders})"
                
                cursor.execute(sql, segment_ids)
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to delete segments in batch: {e}")
            return False
    def get_by_boolean_query(self, and_ids: list, or_ids: list, not_ids: list, doc_scope: bool = True) -> List[dict]:
        """
        Perform a complex Boolean query across segments.
        
        doc_scope=True: Finds segments in DOCUMENTS that satisfy the boolean condition.
        (e.g., Doc must have Code A AND Code B)
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                # We start by finding valid document IDs that satisfy the condition
                doc_sql = "SELECT id FROM documents WHERE 1=1"
                params = []
                
                # AND condition: Document must have ALL of these codes
                if and_ids:
                    for cid in and_ids:
                        doc_sql += " AND id IN (SELECT document_id FROM coded_segments WHERE code_id = ?)"
                        params.append(cid)
                
                # OR condition: Document must have ANY of these codes
                if or_ids:
                    placeholders = ','.join(['?'] * len(or_ids))
                    doc_sql += f" AND id IN (SELECT document_id FROM coded_segments WHERE code_id IN ({placeholders}))"
                    params.extend(or_ids)
                
                # NOT condition: Document must NOT have any of these codes
                if not_ids:
                    placeholders = ','.join(['?'] * len(not_ids))
                    doc_sql += f" AND id NOT IN (SELECT document_id FROM coded_segments WHERE code_id IN ({placeholders}))"
                    params.extend(not_ids)
                
                # Execute to get valid docs
                cursor.execute(doc_sql, params)
                valid_doc_ids = [row[0] for row in cursor.fetchall()]
                
                if not valid_doc_ids:
                    return []
                
                # Now fetch the actual segments for these documents that match ANY of the requested codes (AND + OR)
                # Usually users want to SEE the segments that triggered the match
                target_codes = list(set(and_ids + or_ids))
                if not target_codes:
                    # If only NOT was used, we return all segments in those docs
                    code_filter = ""
                    fetch_params = valid_doc_ids
                else:
                    placeholders = ','.join(['?'] * len(target_codes))
                    code_filter = f"AND cs.code_id IN ({placeholders})"
                    fetch_params = valid_doc_ids + target_codes
                
                doc_placeholders = ','.join(['?'] * len(valid_doc_ids))
                
                final_sql = f"""
                    SELECT cs.*, d.title as document_title, c.name as code_name, c.color as code_color, f.name as folder_name
                    FROM coded_segments cs
                    JOIN documents d ON cs.document_id = d.id
                    JOIN codes c ON cs.code_id = c.id
                    LEFT JOIN folders f ON d.folder_id = f.id
                    WHERE cs.document_id IN ({doc_placeholders})
                    {code_filter}
                    ORDER BY d.title, cs.start_pos
                """
                
                cursor.execute(final_sql, fetch_params)
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Boolean query failed: {e}")
            return []
    def get_all(self) -> List[dict]:
        """Get all coded segments in the project."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cs.*, d.title as document_title, c.name as code_name, c.color as code_color, f.name as folder_name
                    FROM coded_segments cs
                    JOIN documents d ON cs.document_id = d.id
                    JOIN codes c ON cs.code_id = c.id
                    LEFT JOIN folders f ON d.folder_id = f.id
                    ORDER BY d.title, cs.start_pos
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get all segments: {e}")
            return []
