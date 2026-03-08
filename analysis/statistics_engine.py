"""
Statistics Engine for LexiScholar
Aggregates data from database for visualization (Charts, Tables).
"""

import sqlite3
import logging
from typing import Dict, List, Any
from database.connection import get_db_connection

logger = logging.getLogger(__name__)

class StatisticsEngine:
    """Methods for aggregating QDA data into chart-ready formats."""
    
    def __init__(self, db_path: str = "lexischolar.db"):
        self.db_path = db_path

    def get_code_frequencies(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get project-wide frequency for each code.
        Returns: list of {'name': str, 'count': int, 'color': str}
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                query = """
                    SELECT c.name, COUNT(cs.id) as count, c.color
                    FROM codes c
                    LEFT JOIN coded_segments cs ON c.id = cs.code_id
                """
                if active_only:
                    query += " WHERE c.is_active = 1 "
                
                query += " GROUP BY c.id, c.name, c.color HAVING count > 0 ORDER BY count DESC"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get code frequencies: {e}")
            return []

    def get_variable_distribution(self, variable_id: int) -> List[Dict[str, Any]]:
        """
        Get distribution of values for a specific variable (e.g., Gender, Age).
        Returns: list of {'value': str, 'count': int}
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dvv.value, COUNT(dvv.document_id) as count
                    FROM document_variable_values dvv
                    WHERE dvv.variable_id = ?
                    GROUP BY dvv.value
                    ORDER BY count DESC
                """, (variable_id,))
                rows = cursor.fetchall()
                # If values are empty/null, label them as 'Undefined'
                result = []
                for row in rows:
                    val = row['value']
                    if not val or val.lower() == 'none' or val.strip() == '':
                        val = "Tanımsız"
                    result.append({'value': val, 'count': row['count']})
                return result
        except Exception as e:
            logger.error(f"Failed to get variable distribution: {e}")
            return []

    def get_code_cooccurrence(self) -> Dict[str, Any]:
        """
        Calculates how many times codes appear in the same document.
        Returns: {'nodes': [{'id': n, 'name': n}], 'links': [{'source': a, 'target': b, 'value': v}]}
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                # Find overlapping segments or segments in same document
                # For simplicity, we start with 'segments in same document'
                cursor.execute("""
                    SELECT c1.name as code1, c2.name as code2, COUNT(DISTINCT cs1.document_id) as weight
                    FROM coded_segments cs1
                    JOIN coded_segments cs2 ON cs1.document_id = cs2.document_id AND cs1.code_id < cs2.code_id
                    JOIN codes c1 ON cs1.code_id = c1.id
                    JOIN codes c2 ON cs2.code_id = c2.id
                    GROUP BY c1.id, c2.id
                    ORDER BY weight DESC
                """)
                rows = cursor.fetchall()
                
                nodes = set()
                links = []
                for row in rows:
                    nodes.add(row['code1'])
                    nodes.add(row['code2'])
                    links.append({
                        'source': row['code1'],
                        'target': row['code2'],
                        'weight': row['weight']
                    })
                
                return {
                    'nodes': [{'id': n} for n in sorted(list(nodes))],
                    'links': links
                }
        except Exception as e:
            logger.error(f"Failed to get co-occurrence data: {e}")
            return {'nodes': [], 'links': []}

    def get_document_code_matrix(self) -> Dict[str, Any]:
        """
        Data for Heatmap: Documents vs Codes frequency.
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all docs
                cursor.execute("SELECT id, title FROM documents ORDER BY id")
                docs = {row['id']: row['title'] or f"Doc {row['id']}" for row in cursor.fetchall()}
                
                # Get all codes
                cursor.execute("SELECT id, name FROM codes ORDER BY name")
                codes = {row['id']: row['name'] for row in cursor.fetchall()}
                
                # Get counts
                cursor.execute("""
                    SELECT document_id, code_id, COUNT(*) as count
                    FROM coded_segments
                    GROUP BY document_id, code_id
                """)
                matrix_data = cursor.fetchall()
                
                return {
                    'documents': list(docs.values()),
                    'codes': list(codes.values()),
                    'matrix': [dict(row) for row in matrix_data],
                    'doc_ids': list(docs.keys()),
                    'code_ids': list(codes.keys())
                }
        except Exception as e:
            logger.error(f"Failed to get document-code matrix: {e}")
            return {}
