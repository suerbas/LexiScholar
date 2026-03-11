"""
Base Document Tree Components
Defines DraggableTreeView and DocumentTree Base.
"""

from PyQt6.QtWidgets import (
    QTreeView, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex, QTimer
from PyQt6.QtGui import QStandardItemModel, QColor
from ..panel_header import PanelHeader
from ..styles import TREE_VIEW_STYLE
from ..icons import IconProvider

class DraggableTreeView(QTreeView):
    """Custom QTreeView to handle Drag & Drop moves properly with DB persistence."""
    
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget # DocumentTree instance
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Delete:
             self.parent_widget._delete_selected()
        else:
             super().keyPressEvent(event)
        
    def dropEvent(self, event):
        """Handle drop event to update Database hierarchy and ordering."""
        # Perform the UI move
        super().dropEvent(event)
        
        # Synchronize EVERYTHING safely after Model updates natively
        QTimer.singleShot(100, self._delayed_sync)

    def _delayed_sync(self):
        self._sync_tree_to_db()
        self.parent_widget.project_modified.emit()

    def _sync_tree_to_db(self, parent_item=None):
        """Recursively synchronize the tree model state with the database."""
        model = self.model()
        parent_idx = parent_item.index() if parent_item else QModelIndex()
        
        # Determine current folder_id
        folder_id = None
        if parent_item:
            try:
                stored_id = parent_item.data(Qt.ItemDataRole.UserRole + 1)
                folder_id = int(stored_id) if stored_id is not None else None
            except (ValueError, TypeError):
                folder_id = None
        
        # Iterate over all children at this level
        for row in range(model.rowCount(parent_idx)):
            child_idx = model.index(row, 0, parent_idx)
            item = model.itemFromIndex(child_idx)
            if not item: continue
            
            item_type = item.data(Qt.ItemDataRole.UserRole)
            item_id = item.data(Qt.ItemDataRole.UserRole + 1)
            
            if item_type == "document" and self.parent_widget.doc_dao:
                self.parent_widget.doc_dao.move_to_folder(item_id, folder_id)
                self.parent_widget.doc_dao.update_order(item_id, row)
            elif item_type == "folder" and self.parent_widget.folder_dao:
                self.parent_widget.folder_dao.move_to_folder(item_id, folder_id)
                self.parent_widget.folder_dao.update_order(item_id, row)
                # Recurse into the folder
                self._sync_tree_to_db(item)

class DocumentTreeBase(QWidget):
    """Base DocumentTree widget with signals and UI setup."""
    
    # Signals
    document_selected = pyqtSignal(int)
    document_imported = pyqtSignal(str, str)
    document_imported_with_folder = pyqtSignal(str, str, int)
    document_deleted = pyqtSignal(int)
    document_variables_requested = pyqtSignal(int, str)
    document_activation_changed = pyqtSignal(int, bool)
    document_memo_requested = pyqtSignal(int, str)
    chat_requested = pyqtSignal(int, str)
    code_cloud_requested = pyqtSignal(int, str)
    export_requested = pyqtSignal(int, str)
    survey_import_requested = pyqtSignal()
    project_modified = pyqtSignal()
    minimize_requested = pyqtSignal()
    detach_requested = pyqtSignal()
    
    def __init__(self, parent=None, doc_dao=None, folder_dao=None):
        super().__init__(parent)
        self.doc_dao = doc_dao
        self.folder_dao = folder_dao
        self._doc_items = {}  # Maps document_id to QStandardItem
        self._folder_items = {} # Maps folder_id to QStandardItem
        self._is_updating = False 
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header (Not closable as it's a main panel)
        self.header = PanelHeader("BELGELER", has_close=False)
        self.header.minimize_requested.connect(self.minimize_requested.emit)
        self.header.detach_requested.connect(self.detach_requested.emit)
        layout.addWidget(self.header)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(4, 2, 4, 2)
        
        btn_new_folder = QPushButton("📁+")
        btn_new_folder.setToolTip("Yeni Klasör Ekle")
        btn_new_folder.setFixedSize(28, 24)
        btn_new_folder.clicked.connect(self._create_folder)
        
        btn_select_all = QPushButton("Tümünü Seç")
        btn_select_all.setToolTip("Tüm belgeleri etkinleştir")
        btn_select_all.clicked.connect(lambda: self._set_all_active(True))
        
        btn_deselect_all = QPushButton("Seçimi Kaldır")
        btn_deselect_all.setToolTip("Tüm belgelerin etkinliğini kaldır")
        btn_deselect_all.clicked.connect(lambda: self._set_all_active(False))
        
        btn_style = """
            QPushButton {
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                background-color: white;
                color: #374151;
                font-size: 10px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
                border-color: #D1D5DB;
            }
        """
        btn_new_folder.setStyleSheet("""
             QPushButton {
                border: 1px solid transparent;
                border-radius: 4px;
                background-color: transparent;
                color: #F59E0B;
                font-size: 12px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #FEF3C7;
                border: 1px solid #FCD34D;
            }
        """)
        btn_select_all.setStyleSheet(btn_style)
        btn_deselect_all.setStyleSheet(btn_style)
        
        toolbar_layout.addWidget(btn_new_folder)
        toolbar_layout.addSpacing(4)
        toolbar_layout.addWidget(btn_select_all)
        toolbar_layout.addWidget(btn_deselect_all)
        layout.addLayout(toolbar_layout)
        
        # Tree view
        self.tree = DraggableTreeView(self)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([""])
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(TREE_VIEW_STYLE)
        
        self.tree.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.tree.setEditTriggers(QTreeView.EditTrigger.SelectedClicked | QTreeView.EditTrigger.EditKeyPressed)
        
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu, Qt.ConnectionType.UniqueConnection)
        self.tree.selectionModel().selectionChanged.connect(self._on_selection_changed, Qt.ConnectionType.UniqueConnection)
        self.model.itemChanged.connect(self._on_item_changed, Qt.ConnectionType.UniqueConnection)
        
        layout.addWidget(self.tree)
