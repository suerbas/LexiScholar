"""
Document Comparison Tool
Side-by-side comparison of coded segments between two documents.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QTextBrowser, QSplitter, QFrame, QPushButton, QWidget,
    QScrollArea, QToolButton
)
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import Qt, QUrl
from database.schema import DocumentDAO, CodedSegmentDAO, CodeDAO

class ComparisonToolWidget(QWidget):
    """Widget version of Comparison Tool for tabbed interface."""
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.doc_dao = DocumentDAO(db_path)
        self.segment_dao = CodedSegmentDAO(db_path)
        self.code_dao = CodeDAO(db_path)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Header / Toolbar
        toolbar = QHBoxLayout()
        
        title = QLabel("⚖️ Belge Karşılaştırma")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")
        toolbar.addWidget(title)
        
        toolbar.addSpacing(20)
        
        self.combo_doc1 = QComboBox()
        self.combo_doc2 = QComboBox()
        self.combo_doc1.setMinimumWidth(200)
        self.combo_doc2.setMinimumWidth(200)
        self.combo_doc1.currentIndexChanged.connect(self._load_comparison)
        self.combo_doc2.currentIndexChanged.connect(self._load_comparison)
        
        toolbar.addWidget(QLabel("Belge 1:"))
        toolbar.addWidget(self.combo_doc1)
        toolbar.addWidget(QLabel("Belge 2:"))
        toolbar.addWidget(self.combo_doc2)
        
        toolbar.addStretch()
        
        self.layout.addLayout(toolbar)
        
        # Splitter for Content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background: #E2E8F0; width: 4px; }")
        
        self.view1 = QTextBrowser()
        self.view2 = QTextBrowser()
        
        # Modern Styling for TextBrowsers
        for v in [self.view1, self.view2]:
            v.setStyleSheet("border: 1px solid #E2E8F0; border-radius: 6px; background: white;")
            v.setOpenExternalLinks(False)
        
        self.splitter.addWidget(self.view1)
        self.splitter.addWidget(self.view2)
        
        self.layout.addWidget(self.splitter, 1)
        
        # Load Documents
        self._load_docs()

    def _load_docs(self):
        """Load document list into combos."""
        docs = self.doc_dao.get_all()
        for d in docs:
            self.combo_doc1.addItem(d['title'], d['id'])
            self.combo_doc2.addItem(d['title'], d['id'])
            
        # Select first two if available
        if len(docs) > 1:
            self.combo_doc2.setCurrentIndex(1)
            
        self._load_comparison()
        
    def _load_comparison(self):
        """Load coded segments for selected documents."""
        doc1_id = self.combo_doc1.currentData()
        doc2_id = self.combo_doc2.currentData()
        
        if doc1_id is None or doc2_id is None:
            return
            
        self._display_doc(doc1_id, self.view1)
        self._display_doc(doc2_id, self.view2)
        
    def _display_doc(self, doc_id, view):
        """Format and display coded segments for a document."""
        segments = self.segment_dao.get_by_document(doc_id)
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; padding: 10px; }}
                .segment {{ margin-bottom: 15px; border: 1px solid #ddd; padding: 10px; border-radius: 4px; background-color: #f9f9f9; }}
                .code-tag {{ font-weight: bold; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; }}
                .text {{ display: block; margin-top: 5px; line-height: 1.4; }}
            </style>
        </head>
        <body>
        """
        
        if not segments:
            html += "<p><i>Bu belgede kodlanmış segment bulunmuyor.</i></p>"
        else:
            for s in segments:
                color = s.get('code_color', '#333')
                code_name = s.get('code_name', 'Kod')
                text = s.get('segment_text', '')
                
                html += f"""
                <div class="segment">
                    <span class="code-tag" style="background-color: {color};">{code_name}</span>
                    <span class="text">{text}</span>
                </div>
                """
                
        html += "</body></html>"
        view.setHtml(html)
