"""
Database Connection and Initialization for LexiScholar.
Shared utilities used by all DAO modules.
"""

import sqlite3
import logging
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


# Thread-local connection pooling for SQLite
# SQLite supports concurrent reads but writes should be serialized
# WAL mode allows multiple readers and one writer
_thread_local = threading.local()
_connection_pool = {}


def _pool_key(db_path: str) -> tuple[int, str]:
    """Build a stable pool key using current thread and normalized absolute db path."""
    normalized_path = Path(db_path).expanduser().resolve()
    return threading.get_ident(), str(normalized_path)

def get_connection(db_path: str = "lexischolar.db") -> sqlite3.Connection:
    """Get database connection with thread-local pooling and row factory for dict-like access."""
    key = _pool_key(db_path)
    
    # Check if we already have a connection for this thread+db
    if key in _connection_pool:
        conn = _connection_pool[key]
        try:
            # Test if connection is still alive
            conn.execute("SELECT 1")
            return conn
        except sqlite3.Error:
            # Connection is dead, remove it and create a new one
            del _connection_pool[key]
            try:
                conn.close()
            except:
                pass
    
    # Create new connection
    try:
        normalized_db_path = str(Path(db_path).expanduser().resolve())
        conn = sqlite3.connect(normalized_db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA journal_mode = WAL")  # Enable WAL for better concurrency
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA cache_size = -4000")  # 4MB cache
        conn.execute("PRAGMA temp_store = MEMORY") # Keep temp tables in RAM
        conn.execute("PRAGMA mmap_size = 30000000") # 30MB memory mapping
        
        # Store in thread-local pool
        _connection_pool[key] = conn
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseError(f"Failed to connect to database: {e}")

@contextmanager
def get_db_connection(db_path: str = "lexischolar.db"):
    """
    Context manager for database connections.
    Uses thread-local pooling for better performance.
    
    Usage:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            ...
    """
    conn = None
    try:
        conn = get_connection(db_path)
        yield conn
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"Database operation failed: {e}")
        raise DatabaseError(f"Database error: {e}")
    finally:
        # Don't close connection - it's managed by the pool
        pass

def close_connection(db_path: str = "lexischolar.db"):
    """Close thread-local connection for the current thread."""
    key = _pool_key(db_path)
    if key in _connection_pool:
        conn = _connection_pool.pop(key)
        try:
            conn.close()
        except:
            pass

def close_all_connections():
    """Close all connections in the pool (for cleanup)."""
    for conn in _connection_pool.values():
        try:
            conn.close()
        except:
            pass
    _connection_pool.clear()


def init_db(db_path: str = "lexischolar.db") -> bool:
    """Initialize the database with all required tables. Returns True on success."""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Coders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    color TEXT DEFAULT '#3498db',
                    initials TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ensure at least one default coder exists
            cursor.execute("SELECT COUNT(*) FROM coders")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO coders (name, color, initials) VALUES (?, ?, ?)", 
                               ("Varsayılan Kodlayıcı", "#3498db", "VK"))
            
            # Folders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    order_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES folders(id) ON DELETE CASCADE
                )
            """)
            
            # Documents table (Relaxed CHECK constraint to allow media and transcriptions)
            # Since SQLite doesn't allow ALTER TABLE DROP CONSTRAINT easily, we use a more permissive CREATE.
            # To fix existing DBs we must recreate the table if the old constraint is present.
            cursor.execute("PRAGMA foreign_keys=off")
            try:
                # Check if old strict constraint exists by inspecting sqlite_master
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='documents'")
                row = cursor.fetchone()
                if row and "CHECK(file_type IN ('pdf', 'docx', 'txt', 'rtf', 'xls', 'xlsx', 'csv'))" in row['sql']:
                    logger.info("Updating existing 'documents' table schema to remove CHECK constraint...")
                    cursor.execute("DROP TABLE IF EXISTS new_documents")
                    cursor.execute("""
                        CREATE TABLE new_documents (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            file_path TEXT NOT NULL UNIQUE,
                            file_type TEXT NOT NULL,
                            extracted_text TEXT,
                            folder_id INTEGER,
                            is_active BOOLEAN DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            order_index INTEGER DEFAULT 0,
                            FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL
                        )
                    """)
                    cursor.execute("INSERT INTO new_documents SELECT * FROM documents")
                    cursor.execute("DROP TABLE documents")
                    cursor.execute("ALTER TABLE new_documents RENAME TO documents")
            finally:
                cursor.execute("PRAGMA foreign_keys=on")
            
            # Create if not exists (for new databases)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    file_type TEXT NOT NULL, -- Removed strict CHECK constraint to support transcriptions
                    extracted_text TEXT,
                    folder_id INTEGER,
                    order_index INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL
                )
            """)
            
            # (Legacy 'rtf' migration block removed to prevent conflict with open file_type design)
            # Order index migrations for folders and documents
            try:
                # Folders migration
                cursor.execute("SELECT sql FROM sqlite_master WHERE name='folders' AND type='table'")
                schema = cursor.fetchone()[0]
                if "order_index" not in schema:
                    logger.info("Migrating folders table to add order_index column...")
                    cursor.execute("ALTER TABLE folders ADD COLUMN order_index INTEGER DEFAULT 0")
                
                # Documents migration
                cursor.execute("SELECT sql FROM sqlite_master WHERE name='documents' AND type='table'")
                schema = cursor.fetchone()[0]
                if "order_index" not in schema:
                    logger.info("Migrating documents table to add order_index column...")
                    cursor.execute("ALTER TABLE documents ADD COLUMN order_index INTEGER DEFAULT 0")
            except Exception as e:
                logger.warning(f"Order index migration skip: {e}")
            
            # Codes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    color TEXT DEFAULT '#3498db',
                    description TEXT,
                    parent_id INTEGER,
                    order_index INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES codes(id) ON DELETE CASCADE
                )
            """)
            
            # Coded segments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coded_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    code_id INTEGER NOT NULL,
                    coder_id INTEGER DEFAULT 1,
                    start_pos INTEGER NOT NULL,
                    end_pos INTEGER NOT NULL,
                    segment_text TEXT NOT NULL,
                    weight INTEGER DEFAULT 3 CHECK(weight >= 1 AND weight <= 5),
                    comment TEXT,
                    paraphrase TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (code_id) REFERENCES codes(id) ON DELETE CASCADE,
                    FOREIGN KEY (coder_id) REFERENCES coders(id) ON DELETE SET DEFAULT
                )
            """)
            
            # Migration check: coder_id in coded_segments
            try:
                cursor.execute("SELECT sql FROM sqlite_master WHERE name='coded_segments' AND type='table'")
                schema = cursor.fetchone()[0]
                if "coder_id" not in schema:
                    logger.info("Migrating coded_segments table to add coder_id column...")
                    cursor.execute("ALTER TABLE coded_segments ADD COLUMN coder_id INTEGER DEFAULT 1")
                if "paraphrase" not in schema:
                    logger.info("Migrating coded_segments table to add paraphrase column...")
                    cursor.execute("ALTER TABLE coded_segments ADD COLUMN paraphrase TEXT")
                if "comment" not in schema:
                    logger.info("Migrating coded_segments table to add comment column...")
                    cursor.execute("ALTER TABLE coded_segments ADD COLUMN comment TEXT")
                if "embedding" not in schema:
                    logger.info("Migrating coded_segments table to add embedding column for semantic search...")
                    cursor.execute("ALTER TABLE coded_segments ADD COLUMN embedding BLOB")
            except Exception as e:
                logger.warning(f"Coded segments migration skip: {e}")

            # Memos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT NOT NULL,
                    document_id INTEGER,
                    segment_id INTEGER,
                    code_id INTEGER,
                    coder_id INTEGER DEFAULT 1,
                    start_pos INTEGER,
                    end_pos INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (segment_id) REFERENCES coded_segments(id) ON DELETE CASCADE,
                    FOREIGN KEY (code_id) REFERENCES codes(id) ON DELETE CASCADE,
                    FOREIGN KEY (coder_id) REFERENCES coders(id) ON DELETE SET DEFAULT
                )
            """)

            # Migration check: coder_id in memos
            try:
                cursor.execute("SELECT sql FROM sqlite_master WHERE name='memos' AND type='table'")
                schema = cursor.fetchone()[0]
                if "coder_id" not in schema:
                    logger.info("Migrating memos table to add coder_id column...")
                    cursor.execute("ALTER TABLE memos ADD COLUMN coder_id INTEGER DEFAULT 1")
            except Exception as e:
                logger.warning(f"Memos migration skip: {e}")
            
            # Variables table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS variables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    data_type TEXT NOT NULL CHECK(data_type IN ('text', 'integer', 'boolean')),
                    parent_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES variables(id) ON DELETE CASCADE
                )
            """)
            
            # Migration check: If variables table lacks parent_id
            try:
                cursor.execute("SELECT sql FROM sqlite_master WHERE name='variables' AND type='table'")
                schema = cursor.fetchone()[0]
                if "parent_id" not in schema:
                    logger.info("Migrating variables table to add parent_id column...")
                    cursor.execute("ALTER TABLE variables ADD COLUMN parent_id INTEGER REFERENCES variables(id) ON DELETE CASCADE")
            except Exception as e:
                logger.warning(f"Variables migration skip: {e}")
            
            # Document Variable Values table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_variable_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    variable_id INTEGER NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (variable_id) REFERENCES variables(id) ON DELETE CASCADE,
                    UNIQUE(document_id, variable_id)
                )
            """)
            
            # Project Journal table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Code Summaries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS code_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    code_id INTEGER NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (code_id) REFERENCES codes(id) ON DELETE CASCADE,
                    UNIQUE(document_id, code_id)
                )
            """)
            
            # Document Chats table for AI chat history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            
            # ============================================================================
            # INDEX OPTIMIZATION
            # ============================================================================
            
            # 1. Basic Foreign Keys (Existing)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_coded_segments_document ON coded_segments(document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_coded_segments_code ON coded_segments(code_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_folder ON documents(folder_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_codes_parent ON codes(parent_id)")

            # 2. Tree Rendering & Sorting (New)
            # Speeds up loading the document and code trees in correct order
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_folders_parent_order ON folders(parent_id, order_index)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_folder_order ON documents(folder_id, order_index)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_codes_parent_order ON codes(parent_id, order_index)")

            # 3. Document Browser Rendering (New)
            # Critical for loading segments quickly when opening a document (sorted by position)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_coded_segments_doc_pos ON coded_segments(document_id, start_pos)")
            
            # 4. Filtering & Analysis (New)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_coded_segments_coder ON coded_segments(coder_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_vars_lookup ON document_variable_values(variable_id, value)")

            # 5. Memo Lookups (New)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memos_document ON memos(document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memos_code ON memos(code_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memos_segment ON memos(segment_id)")

            # FTS5 full-text search virtual table
            # Allows fast MATCH queries across all document text
            try:
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
                    USING fts5(title, extracted_text, content='documents', content_rowid='id')
                """)
                # Populate if empty (first run or after migration)
                cursor.execute("SELECT COUNT(*) FROM documents_fts")
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO documents_fts(rowid, title, extracted_text) "
                        "SELECT id, title, COALESCE(extracted_text,'') FROM documents"
                    )

                # Create triggers to maintain FTS index sync
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS documents_fts_ai
                    AFTER INSERT ON documents BEGIN
                        INSERT INTO documents_fts(rowid, title, extracted_text)
                        VALUES (new.id, new.title, COALESCE(new.extracted_text, ''));
                    END
                """)
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS documents_fts_ad
                    AFTER DELETE ON documents BEGIN
                        INSERT INTO documents_fts(documents_fts, rowid, title, extracted_text)
                        VALUES ('delete', old.id, old.title, COALESCE(old.extracted_text, ''));
                    END
                """)
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS documents_fts_au
                    AFTER UPDATE ON documents BEGIN
                        INSERT INTO documents_fts(documents_fts, rowid, title, extracted_text)
                        VALUES ('delete', old.id, old.title, COALESCE(old.extracted_text, ''));
                        INSERT INTO documents_fts(rowid, title, extracted_text)
                        VALUES (new.id, new.title, COALESCE(new.extracted_text, ''));
                    END
                """)
            except Exception as e:
                logger.warning(f"FTS5 table setup skip (SQLite may lack FTS5): {e}")

            conn.commit()
            logger.info("Database initialized successfully")
            return True
            
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise DatabaseError(f"Failed to initialize database: {e}")
