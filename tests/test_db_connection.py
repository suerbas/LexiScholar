import pytest
from database.connection import get_db_connection, DatabaseError

def test_get_db_connection_rollback(initialized_db):
    """Test that context manager calls rollback on exception."""
    try:
        with get_db_connection(initialized_db) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO coders (name) VALUES ('Test Coder 1')")
            raise ValueError("Test Error")
    except DatabaseError:
        pass
    
    with get_db_connection(initialized_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM coders WHERE name='Test Coder 1'")
        count = cursor.fetchone()[0]
        assert count == 0

def test_fts_insert_trigger(initialized_db, dao_document):
    doc_id = dao_document.create("Trigger Test", "/t.txt", "txt", "merhaba dünya")
    with get_db_connection(initialized_db) as conn:
        row = conn.execute("SELECT rowid FROM documents_fts WHERE documents_fts MATCH 'merhaba'").fetchone()
    assert row is not None

def test_fts_update_trigger(initialized_db, dao_document):
    doc_id = dao_document.create("Trigger Update Test", "/u.txt", "txt", "eski metin")
    dao_document.update_content(doc_id, "yeni metin")
    with get_db_connection(initialized_db) as conn:
        row = conn.execute("SELECT rowid FROM documents_fts WHERE documents_fts MATCH 'yeni'").fetchone()
    assert row is not None

def test_fts_delete_trigger(initialized_db, dao_document):
    doc_id = dao_document.create("Trigger Delete Test", "/d.txt", "txt", "silinecek metin")
    dao_document.delete(doc_id)
    with get_db_connection(initialized_db) as conn:
        row = conn.execute("SELECT rowid FROM documents_fts WHERE documents_fts MATCH 'silinecek'").fetchone()
    assert row is None
