"""
Summary Grid Tool
Matrix view for summarizing coded segments across documents and codes.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QMessageBox, QHeaderView, QAbstractItemView,
    QTextEdit, QFrame, QToolBar, QScrollArea, QWidget, QToolButton
)
from PyQt6.QtGui import QFont, QColor, QBrush, QAction, QDesktopServices
from PyQt6.QtCore import Qt, QUrl
from database.schema import DocumentDAO, CodeDAO, CodeSummaryDAO, CodedSegmentDAO
from .icons import IconProvider
import os
from .styles import get_color
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class SummaryGridWidget(QFrame):
    """Widget version of Summary Grid for tabbed interface."""
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        
        # DAOs
        self.doc_dao = DocumentDAO(db_path)
        self.code_dao = CodeDAO(db_path)
        self.summary_dao = CodeSummaryDAO(db_path)
        self.segment_dao = CodedSegmentDAO(db_path)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header Area
        info_frame = QFrame()
        info_frame.setStyleSheet("background: white; border-bottom: 1px solid #E2E8F0; padding: 8px 12px;")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(0,0,0,0)
        
        # Actions in header
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_data)
        refresh_btn.setStyleSheet("""
            QPushButton { border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 12px; font-weight: 600; background: #F8FAFC; color: #1E293B; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        
        export_btn = QPushButton("📄 Excel'e Aktar")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_to_excel)
        export_btn.setStyleSheet("""
            QPushButton { border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 12px; font-weight: 600; background: #F8FAFC; color: #1E293B; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        
        info_layout.addWidget(refresh_btn)
        info_layout.addWidget(export_btn)
        info_layout.addStretch()
        
        self.layout.addWidget(info_frame)
        
        # Grid
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setWordWrap(True)
        self.table.setShowGrid(True)
        
        # Apply modern, clean styling
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {get_color('bg_panel')};
                alternate-background-color: {get_color('bg_main')};
                border: none;
                gridline-color: {get_color('border')};
                font-size: 13px;
                color: {get_color('text_primary')};
            }}
            QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {get_color('bg_hover')}; }}
            QTableWidget::item:selected {{ background-color: {get_color('primary_50')}; color: {get_color('primary')}; }}
            QHeaderView::section {{
                background-color: {get_color('bg_main')}; padding: 8px; border: none;
                border-right: 1px solid {get_color('border')}; border-bottom: 1px solid {get_color('border')};
                font-weight: 700; color: {get_color('text_secondary')}; font-size: 11px;
                text-transform: uppercase;
            }}
            QTableCornerButton::section {{ background: {get_color('bg_main')}; border: none; }}
        """)
        
        # Header configuration
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setMinimumSectionSize(40)
        
        self.table.cellDoubleClicked.connect(self._open_summary_editor)
        self.layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        """Load documents and codes to populate the grid."""
        active_docs = self.doc_dao.get_active_ids()
        self.docs = [self.doc_dao.get_by_id(did) for did in active_docs] if active_docs else self.doc_dao.get_all()
            
        active_codes = self.code_dao.get_active_ids()
        self.codes = [self.code_dao.get_by_id(cid) for cid in active_codes] if active_codes else self.code_dao.get_all()
            
        if not self.codes or not self.docs:
            return
            
        self.table.setRowCount(len(self.codes))
        self.table.setColumnCount(len(self.docs))
        self.table.setHorizontalHeaderLabels([d['title'] for d in self.docs])
        self.table.setVerticalHeaderLabels([c['name'] for c in self.codes])
        
        for r, code in enumerate(self.codes):
            for c, doc in enumerate(self.docs):
                summary = self.summary_dao.get_summary(doc['id'], code['id'])
                segments = self.segment_dao.get_by_document(doc['id'])
                code_segments = [s for s in segments if s['code_id'] == code['id']]
                
                item = QTableWidgetItem()
                if summary:
                    item.setText(summary[:120] + "..." if len(summary) > 120 else summary)
                    item.setBackground(QBrush(QColor("#dcfce7")))
                    item.setForeground(QBrush(QColor("#166534")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                elif code_segments:
                    item.setText(f"{len(code_segments)} SEG")
                    item.setBackground(QBrush(QColor("#f0f9ff")))
                    item.setForeground(QBrush(QColor("#0369a1")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    font = item.font()
                    font.setBold(True)
                    font.setPointSize(8)
                    item.setFont(font)
                else:
                    item.setText("-")
                    item.setForeground(QBrush(QColor("#94a3b8")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if code_segments:
                    tooltip = f"<b>{len(code_segments)} Segment:</b><br>"
                    for s in code_segments[:5]:
                        tooltip += f"- {s['segment_text'][:100]}...<br><br>"
                    item.setToolTip(tooltip)
                
                item.setData(Qt.ItemDataRole.UserRole, {'doc_id': doc['id'], 'code_id': code['id']})
                self.table.setItem(r, c, item)
                
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        for c in range(self.table.columnCount()):
            if self.table.columnWidth(c) < 120: self.table.setColumnWidth(c, 120)
            if self.table.columnWidth(c) > 350: self.table.setColumnWidth(c, 350)
        for r in range(self.table.rowCount()):
            if self.table.rowHeight(r) < 30: self.table.setRowHeight(r, 30)
            if self.table.rowHeight(r) > 100: self.table.setRowHeight(r, 100)

    def _export_to_excel(self):
        """Export grid content to CSV (Excel compatible)."""
        from PyQt6.QtWidgets import QFileDialog
        import csv
        
        path, _ = QFileDialog.getSaveFileName(self, "Excel'e Aktar", "summary_grid.csv", "CSV Files (*.csv)")
        if not path: return
        
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, delimiter=';')
                header = ["Kod / Belge"] + [d['title'] for d in self.docs]
                writer.writerow(header)
                
                for r, code in enumerate(self.codes):
                    row = [code['name']]
                    for c, doc in enumerate(self.docs):
                        summary = self.summary_dao.get_summary(doc['id'], code['id'])
                        if not summary:
                            segments = self.segment_dao.get_by_document(doc['id'])
                            code_segments = [s for s in segments if s['code_id'] == code['id']]
                            summary = f"({len(code_segments)} Segment)" if code_segments else "-"
                        row.append(summary)
                    writer.writerow(row)
            show_info(self, "Başarılı", f"Veriler başarıyla aktarıldı:\n{path}")
        except Exception as e:
            show_error(self, "Hata", f"Dışa aktarma başarısız oldu:\n{str(e)}")

    def _open_summary_editor(self, row, col):
        if not hasattr(self, 'docs') or not hasattr(self, 'codes'): return
        try:
            doc_id, code_id = self.docs[col]['id'], self.codes[row]['id']
            doc_title, code_name = self.docs[col]['title'], self.codes[row]['name']
            editor = SummaryEditor(doc_id, code_id, doc_title, code_name, self.summary_dao, self.segment_dao, self)
            if editor.exec(): self.load_data()
        except Exception: pass

class SummaryEditor(QDialog):
    def __init__(self, doc_id, code_id, doc_title, code_name, summary_dao, segment_dao, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Özet: {doc_title} - {code_name}")
        self.resize(700, 600)
        self.doc_id, self.code_id, self.summary_dao = doc_id, code_id, summary_dao
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("<b>İlgili Segmentler:</b>"))
        from .common import ModernSegmentCard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: 1px solid #E2E8F0; border-radius: 8px;")
        
        container = QWidget()
        cl = QVBoxLayout(container)
        segments = segment_dao.get_by_document(doc_id)
        code_segments = [s for s in segments if s['code_id'] == code_id]
        
        if not code_segments:
            cl.addWidget(QLabel("<i>Segment bulunamadı.</i>"))
        else:
            for s in code_segments:
                s['document_title'] = doc_title
                card = ModernSegmentCard(s, code_name)
                cl.addWidget(card)
                card.adjust_height_to_content()
        cl.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
        
        layout.addWidget(QLabel("<b>Özetiniz:</b>"))
        self.editor = QTextEdit()
        self.editor.setStyleSheet(f"border: 1px solid {get_color('border_hover')}; border-radius: 8px; font-size: 13px; padding: 10px;")
        current_summary = summary_dao.get_summary(doc_id, code_id)
        if current_summary: self.editor.setPlainText(current_summary)
        layout.addWidget(self.editor, 1)
        
        btns = QHBoxLayout()
        btn_save = QPushButton("💾 Kaydet")
        btn_save.clicked.connect(self.save)
        btn_save.setStyleSheet(f"background-color: {get_color('success')}; color: white; font-weight: bold; padding: 10px 30px; border-radius: 6px;")
        btns.addStretch(); btns.addWidget(QPushButton("İptal", clicked=self.reject)); btns.addWidget(btn_save)
        layout.addLayout(btns)
        
    def save(self):
        if self.summary_dao.upsert(self.doc_id, self.code_id, self.editor.toPlainText()):
            self.accept()
        else:
            show_warning(self, "Hata", "Özet kaydedilemedi.")
