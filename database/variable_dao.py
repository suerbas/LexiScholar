"""Variable Data Access Objects for LexiScholar."""

import sqlite3
import logging
from typing import Dict, List
from .connection import get_connection, get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


class VariableDAO:
    """Data Access Object for Variable definitions."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def create(self, name: str, data_type: str = 'text', parent_id: int = None) -> int:
        """Create a new variable definition."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO variables (name, data_type, parent_id)
                    VALUES (?, ?, ?)
                """, (name, data_type, parent_id))
                var_id = cursor.lastrowid
                conn.commit()
                return var_id
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to create variable: {e}")
            raise DatabaseError(f"Değişken oluşturulamadı: {e}")
    
    def get_all(self) -> List[dict]:
        """Get all defined variables."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM variables ORDER BY parent_id, name")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get variables: {e}")
            return []
            
    def get_hierarchy(self) -> List[dict]:
        """Get variables organized as a hierarchy (parents with children)."""
        all_vars = self.get_all()
        # Create map and identify top-level parents
        var_map = {v['id']: {**v, 'children': []} for v in all_vars}
        hierarchy = []
        
        for v in var_map.values():
            parent_id = v['parent_id']
            if parent_id and parent_id in var_map:
                var_map[parent_id]['children'].append(v)
            else:
                hierarchy.append(v)
        return hierarchy
    
    def delete(self, var_id: int) -> bool:
        """Delete a variable definition."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM variables WHERE id = ?", (var_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to delete variable {var_id}: {e}")
            return False


class VariableValueDAO:
    """Data Access Object for Document Variable values."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path
    
    def set_value(self, document_id: int, variable_id: int, value: str) -> bool:
        """Set or update a variable value for a document."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO document_variable_values (document_id, variable_id, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(document_id, variable_id) DO UPDATE SET value = EXCLUDED.value
                """, (document_id, variable_id, str(value)))
                conn.commit()
                return True
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to set variable value: {e}")
            return False
    
    def get_values_by_document(self, document_id: int) -> Dict[int, str]:
        """Get all variable values for a specific document."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT variable_id, value FROM document_variable_values
                    WHERE document_id = ?
                """, (document_id,))
                rows = cursor.fetchall()
                return {row['variable_id']: row['value'] for row in rows}
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get values for document {document_id}: {e}")
            return {}

    def get_all_document_values(self) -> List[dict]:
        """Get all variable values for all documents."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT document_id, variable_id, value FROM document_variable_values
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to get all document values: {e}")
            return []
