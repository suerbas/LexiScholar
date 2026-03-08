"""Database module for LexiScholar."""
from .connection import init_db, get_connection, DatabaseError
from .folder_dao import FolderDAO
from .document_dao import DocumentDAO
from .code_dao import CodeDAO
from .segment_dao import CodedSegmentDAO
from .memo_dao import MemoDAO
from .variable_dao import VariableDAO, VariableValueDAO
from .journal_dao import ProjectJournalDAO
from .summary_dao import CodeSummaryDAO
from .coder_dao import CoderDAO
from .chat_dao import ChatDAO

__all__ = [
    'init_db',
    'get_connection',
    'DatabaseError',
    'DocumentDAO',
    'CodeDAO',
    'CodedSegmentDAO',
    'MemoDAO',
    'VariableDAO',
    'VariableValueDAO',
    'ProjectJournalDAO',
    'FolderDAO',
    'CodeSummaryDAO',
    'CoderDAO',
    'ChatDAO'
]
