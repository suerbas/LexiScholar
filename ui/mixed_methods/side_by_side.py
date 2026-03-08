"""
Side-by-side comparison of groups.
"""

from typing import List, Dict
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QSplitter, 
    QScrollArea, QWidget, QFrame, QTextEdit, QToolBar, QSizePolicy, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
from ..common import ModernSegmentCard

class SideBySideWidget(QWidget):
    """Widget version of Side-by-side comparison for tabbed interface."""
    segment_clicked = pyqtSignal(int, int) # doc_id, seg_id
    
    def __init__(self, codes: List[Dict], variables: List[Dict], var_value_dao, parent=None):
        super().__init__(parent)
        self.codes = codes; self.variables = variables; self.var_value_dao = var_value_dao
        self.main_app = parent
        
        # DAOs need to be passed or accessed. 
        # In the dialog version, they were accessed via self.parent() which is risky in tabs.
        # We should pass them or find a way to access them.
        # Let's assume parent (MainWindow) has them or we pass them in constructor.
        # For now, let's try to get them from parent if available, or fail gracefully.
        
        self._setup_ui()
        
    def _setup_ui(self):
        self.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Selection Toolbar (MAXQDA Style)
        self.toolbar = QToolBar("Karşılaştırma Ayarları")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar { 
                background-color: white; border: 1px solid #E2E8F0; border-radius: 10px;
                padding: 6px 10px; spacing: 8px;
            }
            QLabel { color: #64748B; font-weight: 700; font-size: 9pt; border: none; }
            QComboBox { border: 1px solid #CBD5E1; border-radius: 8px; padding: 6px 8px; background: #F8FAFC; max-width: 120px; font-size: 10pt; }
            QPushButton { 
                background-color: #4F46E5; color: white; border-radius: 6px; 
                padding: 6px 16px; font-weight: 700; font-size: 10pt;
            }
            QPushButton:hover { background-color: #4338CA; }
        """)
        
        # Code selection
        self.toolbar.addWidget(QLabel("Kod:"))
        self.code_combo = QComboBox()
        for c in sorted(self.codes, key=lambda x: x['name'].lower()): 
            self.code_combo.addItem(c['name'], c['id'])
            self.code_combo.setItemData(self.code_combo.count() - 1, c['name'], Qt.ItemDataRole.ToolTipRole)
        self.toolbar.addWidget(self.code_combo)

        # Variable selection
        self.toolbar.addWidget(QLabel("Değ:"))
        self.var_combo = QComboBox()
        for v in self.variables: 
            self.var_combo.addItem(v['name'], v['id'])
            self.var_combo.setItemData(self.var_combo.count() - 1, v['name'], Qt.ItemDataRole.ToolTipRole)
        self.var_combo.currentIndexChanged.connect(self._update_group_combos)
        self.toolbar.addWidget(self.var_combo)

        # Groups
        self.toolbar.addWidget(QLabel("Grp A:"))
        self.group_a = QComboBox()
        self.toolbar.addWidget(self.group_a)

        self.toolbar.addWidget(QLabel("Grp B:"))
        self.group_b = QComboBox()
        self.toolbar.addWidget(self.group_b)

        # Run button
        self.run_btn = QPushButton("🚀 Kıyasla")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run_comparison)
        self.toolbar.addWidget(self.run_btn)
        
        layout.addWidget(self.toolbar)
        
        # Splitter for Panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #E2E8F0; }")
        
        self.scroll_a = QScrollArea(); self.scroll_a.setWidgetResizable(True); self.scroll_a.setFrameShape(QFrame.Shape.NoFrame)
        self.content_a = QWidget(); self.layout_a = QVBoxLayout(self.content_a); self.layout_a.setContentsMargins(0, 0, 5, 0); self.layout_a.setSpacing(0); self.scroll_a.setWidget(self.content_a)
        
        self.scroll_b = QScrollArea(); self.scroll_b.setWidgetResizable(True); self.scroll_b.setFrameShape(QFrame.Shape.NoFrame)
        self.content_b = QWidget(); self.layout_b = QVBoxLayout(self.content_b); self.layout_b.setContentsMargins(5, 0, 0, 0); self.layout_b.setSpacing(0); self.scroll_b.setWidget(self.content_b)
        
        splitter.addWidget(self.scroll_a); splitter.addWidget(self.scroll_b); layout.addWidget(splitter, 1)
        self._update_group_combos(0)
                
    def _update_group_combos(self, index):
        v_id = self.var_combo.currentData()
        if v_id:
            # Safe access to DAO
            if not self.var_value_dao: return
            all_v = self.var_value_dao.get_all_document_values()
            vals = sorted(list(set(str(v['value']).strip() if v['value'] is not None else "(Boş)" for v in all_v if v['variable_id'] == v_id)))
            if not vals: vals = ["(Boş)"]
            self.group_a.clear(); self.group_b.clear(); self.group_a.addItems(vals); self.group_b.addItems(vals)
            for i, val in enumerate(vals):
                self.group_a.setItemData(i, val, Qt.ItemDataRole.ToolTipRole)
                self.group_b.setItemData(i, val, Qt.ItemDataRole.ToolTipRole)
            if len(vals) > 1: self.group_b.setCurrentIndex(1)
                
    def _run_comparison(self):
        for la in [self.layout_a, self.layout_b]:
            while la.count():
                child = la.takeAt(0)
                if child.widget(): child.widget().deleteLater()
        
        c_id = self.code_combo.currentData()
        code_name = self.code_combo.currentText()
        v_id = self.var_combo.currentData()
        v_a = self.group_a.currentText(); v_b = self.group_b.currentText()
        
        # Find code color
        c_color = "#4F46E5"
        for c in self.codes:
            if c['id'] == c_id:
                c_color = c.get('color', c_color)
                break

        from analysis import AnalysisTools
        # Find MainWindow to get DAOs
        p = self.main_app
        if hasattr(p, 'doc_dao'):
            analysis = AnalysisTools(p.doc_dao, p.code_dao, p.segment_dao, p.var_dao, p.var_value_dao)
            res = analysis.get_quotes_by_variables([c_id], v_id)
            groups = res.get('groups', {})
            self._populate_view(self.layout_a, groups.get(v_a, []), v_a, code_name, c_color)
            self._populate_view(self.layout_b, groups.get(v_b, []), v_b, code_name, c_color)
        
    def _populate_view(self, layout, segments, group_name, code_name, code_color):
        header_frame = QFrame()
        header_frame.setFixedHeight(45)
        header_frame.setStyleSheet("""
            QFrame { background: white; border-bottom: 2px solid #E2E8F0; padding: 0 10px; }
            QLabel { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
        """)
        hl = QHBoxLayout(header_frame); hl.setContentsMargins(15, 0, 15, 0)
        label = QLabel(f"<span style='color: #64748B;'>GRUP:</span> <span style='color: #1E293B;'>{group_name}</span> &nbsp; <span style='color: #6366F1; font-size: 10px;'>({len(segments)} SEGMENT)</span>")
        hl.addWidget(label); layout.addWidget(header_frame)
        
        container = QWidget(); cl = QVBoxLayout(container); cl.setContentsMargins(5, 10, 5, 10); cl.setSpacing(8)
        container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        if not segments:
            empty = QLabel("Segment bulunmuyor."); empty.setStyleSheet("color: #94A3B8; padding: 20px;"); empty.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(empty)
        else:
            for s in segments:
                # Add document title and color to segment dict if missing
                s['document_title'] = s.get('document_title', 'Bilinmeyen')
                card = ModernSegmentCard(s, code_name, code_color)
                card.clicked.connect(self.segment_clicked.emit) # Pipe to dialog signal
                cl.addWidget(card)
                card.adjust_height_to_content()
        layout.addWidget(container)
        layout.addStretch() # Push everything to the top
