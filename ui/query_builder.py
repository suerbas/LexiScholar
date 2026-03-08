"""
Advanced Query Builder for LexiScholar.
Allows Boolean logic (AND, OR, NOT) for precise segment retrieval.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem,
    QFrame, QSplitter, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt
from .common.modern_dialog import ModernBaseDialog

class QueryBuilderDialog(ModernBaseDialog):
    """Dialog for constructing logical queries on codes."""
    
    def __init__(self, codes: list, parent=None):
        super().__init__(parent, min_width=700, min_height=520)
        self.codes = codes
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        self.layout.setContentsMargins(0, 0, 0, 20)
        self.layout.setSpacing(15)
        
        header = self.build_ribbon_header("🔍", "Boolean Sorgu Sihirbazı", on_close=self.reject)
        self.layout.addWidget(header)
        
        # Content Container
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(20, 10, 20, 0)
        content_layout.setSpacing(15)
        
        info = QLabel("Kodlar arası mantıksal (AND, OR, NOT) ilişkiler kurarak özelleştirilmiş verileri listeleyin.")
        info.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500;")
        content_layout.addWidget(info)
        
        # Splitter for categorization
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle { background-color: transparent; width: 10px; }
        """)
        
        list_style = """
            QListWidget {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item { padding: 6px; border-radius: 4px; }
            QListWidget::item:hover { background-color: #EEF2FF; }
        """
        
        def create_group(title_text):
            group = QFrame()
            group.setStyleSheet("QFrame { background: white; border: 1px solid #CBD5E1; border-radius: 8px; }")
            glayout = QVBoxLayout(group)
            glayout.setContentsMargins(10, 10, 10, 10)
            lbl = QLabel(title_text)
            lbl.setStyleSheet("font-weight: 700; color: #334155; font-size: 12px; border: none;")
            glayout.addWidget(lbl)
            
            lst = QListWidget()
            lst.setStyleSheet(list_style)
            self._populate_list(lst)
            glayout.addWidget(lst)
            return group, lst
            
        and_group, self.and_list = create_group("VE (Kesişim - AND)")
        or_group, self.or_list = create_group("VEYA (Birleşim - OR)")
        not_group, self.not_list = create_group("DEĞİL (Dışlama - NOT)")
        
        splitter.addWidget(and_group)
        splitter.addWidget(or_group)
        splitter.addWidget(not_group)
        content_layout.addWidget(splitter)
        
        # Options
        self.cb_doc_scope = QCheckBox("Belge Seviyesinde Sorgula (Aynı belgede geçmeleri yeterli)")
        self.cb_doc_scope.setChecked(True)
        self.cb_doc_scope.setStyleSheet("""
            QCheckBox { font-weight: 600; color: #334155; font-size: 13px; spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #CBD5E1; border-radius: 4px; background: white; }
            QCheckBox::indicator:checked { background: #4F46E5; border-color: #4F46E5; }
        """)
        content_layout.addWidget(self.cb_doc_scope)
        self.layout.addWidget(content_wrapper)
        
        self.layout.addStretch()
        
        # Actions Footer
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 10, 20, 0)
        
        btn_clear = QPushButton("Temizle")
        btn_clear.clicked.connect(self._clear_selections)
        btn_clear.setFixedWidth(100)
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.setStyleSheet("""
            QPushButton { background: transparent; color: #EF4444; border: 1px solid #FCA5A5; border-radius: 8px; padding: 10px; font-weight: 600; }
            QPushButton:hover { background: #FEF2F2; }
        """)
        
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setFixedWidth(100)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #475569; border: 1px solid #CBD5E1; border-radius: 8px; padding: 10px; font-weight: 600; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        
        self.btn_run = QPushButton("Sorguyu Başlat")
        self.btn_run.setFixedWidth(160)
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.setStyleSheet("""
            QPushButton { background: #4F46E5; color: white; border: none; border-radius: 8px; padding: 10px; font-weight: 700; font-size: 13px; }
            QPushButton:hover { background: #4338CA; }
        """)
        self.btn_run.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_clear)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_run)
        self.layout.addLayout(btn_layout)

    def _populate_list(self, list_widget):
        for code in self.codes:
            item = QListWidgetItem(f"🏷️ {code['name']}")
            item.setData(Qt.ItemDataRole.UserRole, code['id'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            list_widget.addItem(item)
            
    def _clear_selections(self):
        for lw in [self.and_list, self.or_list, self.not_list]:
            for i in range(lw.count()):
                lw.item(i).setCheckState(Qt.CheckState.Unchecked)

    def get_query_parameters(self):
        """Extract selected IDs for each logic group."""
        def get_checked(lw):
            return [lw.item(i).data(Qt.ItemDataRole.UserRole) 
                    for i in range(lw.count()) 
                    if lw.item(i).checkState() == Qt.CheckState.Checked]
        
        return {
            'and_ids': get_checked(self.and_list),
            'or_ids': get_checked(self.or_list),
            'not_ids': get_checked(self.not_list),
            'doc_scope': self.cb_doc_scope.isChecked()
        }
