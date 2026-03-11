"""
Core Document Browser Components
Contains the main class definition and signals.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from ..ai_assistant_mixin import AIAssistantMixin
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class DocumentBrowserBase(AIAssistantMixin, QWidget):
    """Signals and basic state for DocumentBrowser."""
    
    text_selected = pyqtSignal(int, int, str)
    code_assigned = pyqtSignal(int, int, str, int)
    in_vivo_code_requested = pyqtSignal(int, int, str, str)
    memo_requested = pyqtSignal(int, int, str)
    memo_edit_requested = pyqtSignal(int, str)
    memo_delete_requested = pyqtSignal(int)
    remove_code_requested = pyqtSignal(int, int)
    playback_requested = pyqtSignal(float)
    minimize_requested = pyqtSignal()
    detach_requested = pyqtSignal()
    maximize_requested = pyqtSignal()
    document_content_changed = pyqtSignal(int, str)
    chat_requested = pyqtSignal(int, str)

    def __init__(self, parent=None, db_path="lexischolar.db"):
        super().__init__(parent)
        self._db_path = db_path
        self._current_doc_id = None
        self._current_doc_title = None
        self._coded_segments = []
        self._memos = []
        self._pending_code = None
        self._active_segment_range = None
        self._last_tooltip_memo_id = None

    def set_db_path(self, db_path: str):
        """Update the database path."""
        self._db_path = db_path

    def _chat_with_document(self):
        """Request AI chat as a tab via signal."""
        if not self._current_doc_id:
            from PyQt6.QtWidgets import QMessageBox
            show_warning(self, "Uyarı", "Lütfen önce bir belge açın.")
            return

        title = self._current_doc_title or f"Belge {self._current_doc_id}"
        self.chat_requested.emit(self._current_doc_id, title)

    def clear(self):
        """Clear document content and reset state."""
        self._current_doc_id = None
        self._coded_segments = []
        self._memos = []
        self._active_segment_range = None
        self.text_edit.setPlainText("")
        # self.header.set_title("BELGE GÖRÜNTÜLEYICI")
        self.coding_stripes.set_segments([], self.text_edit)
        self.code_indicator.setText("")
        self.code_indicator.hide()
        self.text_edit.setExtraSelections([])
