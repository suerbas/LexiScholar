"""
Event Handlers for LexiScholar Main Window
Composite mixin combining specialized handler modules.
"""

from .document_handlers import DocumentHandlersMixin
from .code_handlers import CodeHandlersMixin
from .memo_handlers import MemoHandlersMixin
from .data_handlers import DataHandlersMixin

class EventHandlers(
    DocumentHandlersMixin,
    CodeHandlersMixin,
    MemoHandlersMixin,
    DataHandlersMixin
):
    """
    Composite mixin class providing all event handler methods for MainWindow.
    This class is maintained for backwards compatibility with imports in main_window.py.
    """
    pass
