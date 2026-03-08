"""
Base UI components for Code Tree.
"""

from PyQt6.QtWidgets import (
    QTreeView, QMenu, QInputDialog, QColorDialog,
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QSize
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QDrag, QIcon
import json
from ..common.modern_dialog import ModernBaseDialog
from ..panel_header import PanelHeader
from ..styles import TREE_VIEW_STYLE, CONTEXT_MENU_STYLE

class CodeDialog(ModernBaseDialog):
    """Dialog for creating or editing a code with name, color and description."""
    def __init__(self, parent=None, title="Kod Düzenle", name="", color="#4F46E5", description=""):
        super().__init__(parent, min_width=450, min_height=400)
        self._title_text = title
        self.initial_name = name
        self.current_color = color
        self.initial_desc = description
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header
        header = self.build_ribbon_header("🏷️", self._title_text)
        self.layout.addWidget(header)
        
        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        # Name
        form_layout.addWidget(QLabel("Kod Adı:"))
        self.name_edit = QLineEdit(self.initial_name)
        self.name_edit.setPlaceholderText("Kod adı...")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px; border: 1px solid #CBD5E1; border-radius: 8px;
                background: white; font-size: 13px; color: #0F172A;
            }
            QLineEdit:focus { border: 1px solid #4F46E5; }
        """)
        form_layout.addWidget(self.name_edit)
        
        # Color
        color_label = QHBoxLayout()
        color_label.addWidget(QLabel("Renk:"))
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border-radius: 12px; border: 1px solid #CBD5E1;")
        
        self.color_btn = QPushButton("Renk Seç...")
        self.color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_btn.setStyleSheet("""
            QPushButton {
                background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; font-weight: bold; color: #475569;
            }
            QPushButton:hover { background: #F8FAFC; border-color: #94A3B8; }
        """)
        self.color_btn.clicked.connect(self._choose_color)
        
        color_label.addWidget(self.color_preview)
        color_label.addWidget(self.color_btn)
        color_label.addStretch()
        form_layout.addLayout(color_label)
        
        # Description
        form_layout.addWidget(QLabel("Tanım:"))
        self.desc_edit = QTextEdit(self.initial_desc)
        self.desc_edit.setPlaceholderText("Kod tanımı/açıklaması (Codebook için)...")
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setStyleSheet("""
            QTextEdit {
                padding: 10px; border: 1px solid #CBD5E1; border-radius: 8px;
                background: white; font-size: 13px; color: #0F172A;
            }
            QTextEdit:focus { border: 1px solid #4F46E5; }
        """)
        form_layout.addWidget(self.desc_edit)
        
        self.layout.addLayout(form_layout)
        self.layout.addStretch()
        
        # Footer buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #64748B; border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 10px 20px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        
        ok_btn = QPushButton("Tamam")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5; color: white; border: none;
                border-radius: 8px; padding: 10px 30px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background: #4338CA; }
        """)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        
        btn_layout.addStretch()
        self.layout.addLayout(btn_layout)

    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self.current_color), self, "Kod Rengi Seç")
        if color.isValid():
            self.current_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border-radius: 12px; border: 1px solid #CBD5E1;")

    def get_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'color': self.current_color,
            'description': self.desc_edit.toPlainText().strip()
        }


class DraggableCodeTree(QTreeView):
    """Tree view with drag support for codes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeView.DragDropMode.DragOnly)
    
    def startDrag(self, supportedActions):
        """Start dragging a code."""
        indexes = self.selectedIndexes()
        if not indexes:
            return
        
        item = self.model().itemFromIndex(indexes[0])
        code_data = {
            'id': item.data(Qt.ItemDataRole.UserRole + 1),
            'name': item.data(Qt.ItemDataRole.UserRole + 3),
            'color': item.data(Qt.ItemDataRole.UserRole + 2)
        }
        
        if code_data['id'] is None:
            return
        
        mime_data = QMimeData()
        mime_data.setText(json.dumps(code_data))
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)

    def keyPressEvent(self, event):
        """Handle keyboard events like Delete."""
        if event.key() == Qt.Key.Key_Delete:
            # We assume the parent (CodeTree) has _delete_selected
            # This is slightly coupled but matches original logic
            code_tree = self.window() # Or use signals
            if hasattr(self.parent(), '_delete_selected'):
                self.parent()._delete_selected()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


class CodeTreeBase(QWidget):
    """Base class providing the layout and visual structure."""
    
    # Signals (Moved from original)
    code_selected = pyqtSignal(int)
    code_created = pyqtSignal(str, str, object, str)
    code_deleted = pyqtSignal(int)
    code_activation_changed = pyqtSignal(int, bool)
    code_memo_requested = pyqtSignal(int, str)
    coded_segments_requested = pyqtSignal(int, str, str)
    project_modified = pyqtSignal()
    minimize_requested = pyqtSignal()
    detach_requested = pyqtSignal()
    ai_action_requested = pyqtSignal(int, str, str)
    quick_code_requested = pyqtSignal(int, str, str)

    def __init__(self, parent=None, code_dao=None):
        super().__init__(parent)
        self.code_dao = code_dao
        self._code_items = {} # Maps code_id to QStandardItem
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Tree & Model
        self.tree = DraggableCodeTree(self)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([""])
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(TREE_VIEW_STYLE)
        
        # 2. Header (Not closable as it's a main panel)
        self.header = PanelHeader("KODLAR", has_close=False)
        layout.addWidget(self.header)
        
        # 3. Toolbar
        toolbar_layout = QVBoxLayout()
        toolbar_layout.setContentsMargins(4, 2, 4, 2)
        toolbar_layout.setSpacing(4)
        
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Kodlarda ara...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E2E8F0; border-radius: 6px; padding: 4px 8px;
                background: white; font-size: 11px;
            }
            QLineEdit:focus { border-color: #4F46E5; }
        """)
        search_layout.addWidget(self.search_bar)
        toolbar_layout.addLayout(search_layout)

        actions_layout = QHBoxLayout()
        self.btn_new_code = QPushButton("＋")
        self.btn_new_code.setToolTip("Yeni Kod Ekle")
        self.btn_new_code.setFixedSize(24, 24)
        
        self.btn_expand = QPushButton("⭳")
        self.btn_expand.setToolTip("Tüm kod hiyerarşisini aç")
        self.btn_expand.setFixedSize(24, 24)
        
        self.btn_collapse = QPushButton("⭱")
        self.btn_collapse.setToolTip("Tüm kod hiyerarşisini kapat")
        self.btn_collapse.setFixedSize(24, 24)
        
        self.btn_select_all = QPushButton("☑")
        self.btn_select_all.setToolTip("Tüm kodları etkinleştir")
        self.btn_select_all.setFixedSize(24, 24)
        
        self.btn_deselect_all = QPushButton("☐")
        self.btn_deselect_all.setToolTip("Tüm kodların etkinliğini kaldır")
        self.btn_deselect_all.setFixedSize(24, 24)
        
        # Apply styles (omitting for brevity in template, will use same as original)
        self._apply_styles()
        
        actions_layout.addWidget(self.btn_new_code)
        actions_layout.addSpacing(8)
        actions_layout.addWidget(self.btn_expand)
        actions_layout.addWidget(self.btn_collapse)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_select_all)
        actions_layout.addWidget(self.btn_deselect_all)
        
        toolbar_layout.addLayout(actions_layout)
        layout.addLayout(toolbar_layout)
        
        # 4. Hint
        hint = QLabel("💡 Sürükle-Bırak ile kodlayın")
        hint.setStyleSheet("""
            QLabel { background-color: #FEF3C7; color: #92400E; font-size: 10px;
                     padding: 4px 8px; border-bottom: 1px solid #FDE68A; }
        """)
        layout.addWidget(hint)
        layout.addWidget(self.tree)

    def _apply_styles(self):
        # Original btn_style logic
        btn_style = """
            QPushButton { border: 1px solid #E5E7EB; border-radius: 4px;
                          background-color: white; color: #4B5563; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: #F3F4F6; border-color: #D1D5DB; color: #111827; }
        """
        btn_primary_style = """
            QPushButton { border: 1px solid transparent; border-radius: 4px;
                          background-color: #EEF2FF; color: #4F46E5; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #E0E7FF; border: 1px solid #C7D2FE; }
        """
        self.btn_new_code.setStyleSheet(btn_primary_style)
        for b in [self.btn_expand, self.btn_collapse, self.btn_select_all, self.btn_deselect_all]:
            b.setStyleSheet(btn_style)
