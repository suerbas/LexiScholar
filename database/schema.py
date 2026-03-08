"""
LexiScholar Database Schema — Backwards-compatible re-exports.

This file has been split into individual modules for maintainability.
All classes and functions are re-exported here so existing
`from database.schema import X` statements continue to work.

Modules:
  - connection.py   → DatabaseError, get_connection, init_db
  - folder_dao.py   → FolderDAO
  - document_dao.py → DocumentDAO
  - code_dao.py     → CodeDAO
  - segment_dao.py  → CodedSegmentDAO
  - memo_dao.py     → MemoDAO
  - variable_dao.py → VariableDAO, VariableValueDAO
  - journal_dao.py  → ProjectJournalDAO
  - summary_dao.py  → CodeSummaryDAO
"""

# Re-export everything for backwards compatibility
from .connection import DatabaseError, get_connection, init_db  # noqa: F401
from .folder_dao import FolderDAO  # noqa: F401
from .document_dao import DocumentDAO  # noqa: F401
from .code_dao import CodeDAO  # noqa: F401
from .segment_dao import CodedSegmentDAO  # noqa: F401
from .memo_dao import MemoDAO  # noqa: F401
from .variable_dao import VariableDAO, VariableValueDAO  # noqa: F401
from .journal_dao import ProjectJournalDAO  # noqa: F401
from .summary_dao import CodeSummaryDAO  # noqa: F401
from .chat_dao import ChatDAO  # noqa: F401
