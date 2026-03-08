"""
Manager classes to support MainWindow refactoring.
Separates DAOs, UI construction, and Signal routing.
"""

from typing import TYPE_CHECKING
from database import (
    DocumentDAO, CodeDAO, CodedSegmentDAO, 
    MemoDAO, VariableDAO, VariableValueDAO, FolderDAO, 
    ProjectJournalDAO, CodeSummaryDAO, CoderDAO, ChatDAO
)

if TYPE_CHECKING:
    from .main_window import MainWindow

class DAOManager:
    """Centralized container for all Data Access Objects."""
    def __init__(self, db_path: str):
        self.documents = DocumentDAO(db_path)
        self.codes = CodeDAO(db_path)
        self.segments = CodedSegmentDAO(db_path)
        self.memos = MemoDAO(db_path)
        self.variables = VariableDAO(db_path)
        self.variable_values = VariableValueDAO(db_path)
        self.folders = FolderDAO(db_path)
        self.journals = ProjectJournalDAO(db_path)
        self.summaries = CodeSummaryDAO(db_path)
        self.coders = CoderDAO(db_path)
        self.chats = ChatDAO(db_path)

class UIBuilder:
    """Handles the complex UI assembly for the main window."""
    def __init__(self, window: 'MainWindow'):
        self.window = window

    def setup_ui(self):
        """Main UI assembly entry point."""
        self.window._setup_window()
        self.window._setup_ui()
        self.window._setup_statusbar()
        self.window._update_project_label()

class SignalRouter:
    """Centralizes and connects all signals for the main window components."""
    def __init__(self, window: 'MainWindow'):
        self.window = window

    def connect_all(self):
        """Connects all internal and component signals."""
        w = self.window
        
        # Document Tree signals
        w.document_tree.document_selected.connect(w._on_document_selected)
        w.document_tree.document_deleted.connect(w._on_document_deleted)
        w.document_tree.document_imported.connect(w._on_document_imported)
        w.document_tree.document_imported_with_folder.connect(w._on_document_imported)
        w.document_tree.document_variables_requested.connect(w._on_document_variables_requested)
        w.document_tree.document_activation_changed.connect(w._on_document_activation_changed)
        w.document_tree.document_memo_requested.connect(w._on_document_memo_requested)
        w.document_tree.chat_requested.connect(w._on_chat_requested)
        w.document_tree.code_cloud_requested.connect(w._on_code_cloud_requested)
        w.document_tree.export_requested.connect(w._on_export_requested)
        w.document_tree.survey_import_requested.connect(w._show_survey_import_dialog)
        w.document_tree.project_modified.connect(w.set_dirty)
        w.document_tree.minimize_requested.connect(lambda: w._minimize_panel('documents'))
        w.document_tree.detach_requested.connect(lambda: w._detach_panel('documents'))

        # Code Tree signals
        w.code_tree.code_selected.connect(w._on_code_selected)
        w.code_tree.code_created.connect(w._on_code_created)
        w.code_tree.code_deleted.connect(w._on_code_deleted)
        w.code_tree.code_activation_changed.connect(w._on_code_activation_changed)
        w.code_tree.code_memo_requested.connect(w._on_code_memo_requested)
        w.code_tree.coded_segments_requested.connect(w._on_coded_segments_requested)
        w.code_tree.ai_action_requested.connect(w._on_ai_action_requested)
        w.code_tree.quick_code_requested.connect(w._on_quick_code_requested)
        w.code_tree.project_modified.connect(w.set_dirty)
        w.code_tree.minimize_requested.connect(lambda: w._minimize_panel('codes'))
        w.code_tree.detach_requested.connect(lambda: w._detach_panel('codes'))

        # Browser signals
        w.document_browser.code_assigned.connect(w._on_code_assigned)
        w.document_browser.in_vivo_code_requested.connect(w._on_in_vivo_code_requested)
        w.document_browser.memo_requested.connect(w._on_memo_requested)
        w.document_browser.memo_edit_requested.connect(w._on_memo_edit_requested)
        w.document_browser.memo_delete_requested.connect(w._on_memo_delete_requested)
        w.document_browser.remove_code_requested.connect(w._on_remove_code_requested)
        w.document_browser.playback_requested.connect(w.audio_player.play_at)
        w.document_browser.minimize_requested.connect(lambda: w._minimize_panel('browser'))
        w.document_browser.detach_requested.connect(lambda: w._detach_panel('browser'))
        w.document_browser.chat_requested.connect(w._on_chat_requested)
        w.document_browser.document_content_changed.connect(w.document_tree._refresh_data)

        # Retrieved Segments signals
        w.retrieved_segments.segment_clicked.connect(w._on_segment_clicked)
        w.retrieved_segments.segment_delete_requested.connect(w._on_segment_delete_requested)
        w.retrieved_segments.query_requested.connect(w._on_query_requested)
        w.retrieved_segments.minimize_requested.connect(lambda: w._minimize_panel('segments'))
        w.retrieved_segments.detach_requested.connect(lambda: w._detach_panel('segments'))
