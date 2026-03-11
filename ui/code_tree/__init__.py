"""
Code Tree Sub-package for LexiScholar.
Assembled from modular base and mixins.
"""

from PyQt6.QtCore import Qt
from .base import CodeTreeBase
from .actions_mixin import CodeTreeActionsMixin
from .model_populator import CodeTreeModelPopulatorMixin
from .menu_builder import CodeTreeMenuMixin

class CodeTree(CodeTreeBase, CodeTreeActionsMixin, CodeTreeModelPopulatorMixin, CodeTreeMenuMixin):
    """
    Hierarchical tree view for qualitative code management.
    Modularized implementation using composite pattern with mixins.
    """
    def __init__(self, parent=None, code_dao=None):
        super().__init__(parent, code_dao)
        self._setup_ui()
        self._connect_signals()

    def set_daos(self, code_dao):
        """Update DAOs and refresh tree."""
        self.code_dao = code_dao
        self._refresh_codes()

    def _connect_signals(self):
        # UI Interactions
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.model.itemChanged.connect(self._on_item_changed)
        self.tree.doubleClicked.connect(self._on_double_clicked)
        
        # Toolbar
        self.search_bar.textChanged.connect(self._filter_codes)
        self.btn_new_code.clicked.connect(lambda: self._create_code(None))
        self.btn_expand.clicked.connect(self.tree.expandAll)
        self.btn_collapse.clicked.connect(self.tree.collapseAll)
        self.btn_select_all.clicked.connect(lambda: self._set_all_active(True))
        self.btn_deselect_all.clicked.connect(lambda: self._set_all_active(False))
        
        # Header
        self.header.minimize_requested.connect(self.minimize_requested.emit)
        self.header.detach_requested.connect(self.detach_requested.emit)

    def _on_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if indexes:
            item = self.model.itemFromIndex(indexes[0])
            code_id = item.data(Qt.ItemDataRole.UserRole + 1)
            if code_id is not None: self.code_selected.emit(code_id)

    def _on_item_changed(self, item):
        code_id = item.data(Qt.ItemDataRole.UserRole + 1)
        if not code_id or getattr(self, 'loading', False): return
        
        is_active = item.checkState() == Qt.CheckState.Checked
        if self.code_dao: self.code_dao.set_active(code_id, is_active)
        self._update_item_display(item)
        self.code_activation_changed.emit(code_id, is_active)
            
        if item.hasChildren():
            self._toggle_subcodes(item, is_active)
            self.code_activation_changed.emit(-1, is_active)

    def _on_double_clicked(self, index):
        item = self.model.itemFromIndex(index)
        if item: self._open_coded_segments(item)

    def _open_coded_segments(self, item):
        code_id = item.data(Qt.ItemDataRole.UserRole + 1)
        name    = item.data(Qt.ItemDataRole.UserRole + 3) or item.text()
        color   = item.data(Qt.ItemDataRole.UserRole + 2) or "#4F46E5"
        if code_id is not None:
            self.coded_segments_requested.emit(code_id, name, color)
