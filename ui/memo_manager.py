"""
Memo Manager Dialog for LexiScholar
Lists all memos, allows filtering, searching, and editing.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QTextEdit, QPushButton, QLineEdit, QComboBox, QMessageBox, 
    QWidget, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QColor, QFont

from .styles import DIALOG_STYLE, PANEL_HEADER_STYLE
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class MemoManagerWidget(QWidget):
    """Widget to manage all memos (Free, Document, Code, etc.) for tab integration."""
    
    memo_updated = pyqtSignal()  # Emitted when a memo is changed/deleted
    
    def __init__(self, parent=None, memo_dao=None, focus_search=False):
        super().__init__(parent)
        self.memo_dao = memo_dao
        self.memos = []
        self.current_memo_id = None
        
        self._setup_ui()
        self._load_memos()
        
        if focus_search:
            self.search_input.setFocus()
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Content Wrapper to add margins back for the body
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Toolbar (Search & Filter)
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Memolarda ara...")
        self.search_input.textChanged.connect(self._filter_list)
        toolbar.addWidget(self.search_input)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tümü", "Serbest Memolar", "Belge Memoları"])
        self.filter_combo.currentTextChanged.connect(self._filter_list)
        toolbar.addWidget(self.filter_combo)
        
        btn_refresh = QPushButton("Yenile")
        btn_refresh.clicked.connect(self._load_memos)
        toolbar.addWidget(btn_refresh)
        
        content_layout.addLayout(toolbar)
        
        # Main Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Memo List
        self.memo_list = QListWidget()
        self.memo_list.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.memo_list)
        
        # Right: Memo Details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(10, 0, 0, 0)
        
        # Title Edit
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Başlık (Opsiyonel)")
        details_layout.addWidget(QLabel("Başlık:"))
        details_layout.addWidget(self.title_edit)
        
        # Content Edit
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Memo içeriği...")
        details_layout.addWidget(QLabel("İçerik:"))
        details_layout.addWidget(self.content_edit)
        
        # Meta Info
        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("color: #64748B; font-size: 11px;")
        details_layout.addWidget(self.meta_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("Kaydet")
        self.btn_save.setStyleSheet("background-color: #10B981; color: white; padding: 6px;")
        self.btn_save.clicked.connect(self._save_changes)
        
        self.btn_delete = QPushButton("Sil")
        self.btn_delete.setStyleSheet("background-color: #EF4444; color: white; padding: 6px;")
        self.btn_delete.clicked.connect(self._delete_memo)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_save)
        details_layout.addLayout(btn_layout)
        
        details_wrapper = QWidget()
        details_wrapper.setLayout(details_layout)
        splitter.addWidget(details_wrapper)
        
        # Set splitter proportions (30% list, 70% details)
        splitter.setSizes([270, 630])
        
        content_layout.addWidget(splitter)
        layout.addWidget(content_widget)
        
    def _load_memos(self):
        """Load memos from database."""
        if not self.memo_dao:
            return
            
        self.memos = self.memo_dao.get_all()
        self._filter_list()
        
    def _filter_list(self):
        """Filter and display memos in the list."""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        
        self.memo_list.clear() 
        self.current_memo_id = None
        self.title_edit.clear()
        self.content_edit.clear()
        self.meta_label.clear()
        
        for memo in self.memos:
            # Filter out AI Error Memos (Temporary Fix for Old Data)
            content = memo.get('content', '')
            if "**ai özeti:**" in content.lower() or "resource_exhausted" in content.lower():
                continue
                
            # Type Filter
            is_doc_memo = memo.get('document_id') is not None
            
            if filter_type == "Serbest Memolar" and is_doc_memo:
                continue
            if filter_type == "Belge Memoları" and not is_doc_memo:
                continue
                
            # Search Filter
            content_lower = content.lower()
            title = memo.get('title', '')
            title_lower = title.lower() if title else ''
            
            if search_text and (search_text not in content_lower and search_text not in title_lower):
                continue
                
            # Create Item
            display_title = title if title else "Başlıksız Memo"
            
            # Format display text
            if is_doc_memo:
                doc_title = memo.get('doc_title', 'Bilinmeyen Belge')
                display_text = f"{display_title}\n📄 {doc_title}"
                color = QColor("#1E293B") 
                bg_color = QColor("#EFF6FF") # Light Blue
            else:
                display_text = f"{display_title}\n📝 Serbest Memo"
                color = QColor("#B45309") # Dark Amber
                bg_color = QColor("#FFFBEB") # Light Amber
            
            # Create truncated content preview
            preview = content[:50].replace('\n', ' ') + "..." if content and len(content) > 50 else content
            full_text = f"{display_text}\n---\n{preview}"
                
            item = QListWidgetItem(full_text)
            item.setData(Qt.ItemDataRole.UserRole, memo)
            item.setForeground(color)
            item.setBackground(bg_color)
            item.setToolTip(content)
            
            self.memo_list.addItem(item)

    def _on_selection_changed(self):
        """Handle list selection."""
        items = self.memo_list.selectedItems()
        if not items:
            self.current_memo_id = None
            self.title_edit.clear()
            self.content_edit.clear()
            self.meta_label.clear()
            self.btn_save.setEnabled(False)
            self.btn_delete.setEnabled(False)
            return
            
        memo = items[0].data(Qt.ItemDataRole.UserRole)
        self.current_memo_id = memo['id']
        self.title_edit.setText(memo.get('title', ''))
        self.content_edit.setPlainText(memo.get('content', ''))
        
        created = memo.get('created_at', '?')
        modified = memo.get('modified_at', '?')
        self.meta_label.setText(f"Oluşturuldu: {created}\nDeğiştirildi: {modified}")
        
        self.btn_save.setEnabled(True)
        self.btn_delete.setEnabled(True)
        
    def _save_changes(self):
        """Save updated memo."""
        if not self.current_memo_id:
            return
            
        new_title = self.title_edit.text().strip()
        new_content = self.content_edit.toPlainText().strip()
        
        if not new_content:
            show_warning(self, "Hata", "Memo içeriği boş olamaz.")
            return
            
        if self.memo_dao.update(self.current_memo_id, content=new_content, title=new_title):
            self.memo_updated.emit()
            self._load_memos() # Refresh list but try to keep selection?
            # For now just reload
            show_info(self, "Başarılı", "Memo güncellendi.")
        else:
            show_error(self, "Hata", "Memo güncellenemedi.")
            
    def _delete_memo(self):
        """Delete selected memo."""
        if not self.current_memo_id:
            return
            
        reply = ask_confirmation(
            self, "Sil", "Bu memoyu silmek istediğinizden emin misiniz?"
        )
        
        if reply :
            if self.memo_dao.delete(self.current_memo_id):
                self.memo_updated.emit()
                self._load_memos()
            else:
                show_error(self, "Hata", "Memo silinemedi.")


class MemoManagerDialog(QDialog):
    """Standalone dialog wrapper for MemoManagerWidget."""
    def __init__(self, parent=None, memo_dao=None, focus_search=False):
        super().__init__(parent)
        self.setWindowTitle("Memo Yöneticisi")
        self.resize(900, 600)
        self.setStyleSheet(DIALOG_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.widget = MemoManagerWidget(self, memo_dao, focus_search)
        layout.addWidget(self.widget)
        
        # Connect signal expansion
        self.memo_updated = self.widget.memo_updated
