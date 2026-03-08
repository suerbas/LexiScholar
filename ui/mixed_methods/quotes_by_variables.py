"""
Quotes by Variables analysis dialogs.
"""

from typing import List, Dict, Tuple
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton, 
    QListWidget, QListWidgetItem, QComboBox, QFrame, QScrollArea, QWidget, QTextEdit,
    QToolButton, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor
from ..styles import COLORS
from ..common.modern_dialog import ModernBaseDialog

class QuotesByVariablesDialog(ModernBaseDialog):
    """Selection dialog for Quotes by Variables analysis."""
    def __init__(self, codes: List[Dict], variables: List[Dict], parent=None):
        super().__init__(parent, min_width=620, min_height=520)
        self.codes = codes
        self.variables = variables
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("🧩", "Karma Yöntem Analizi")
        self.layout.addWidget(header)

        desc = QLabel("Bir kodun farklı değişken değerlerine göre dağılımını metin olarak inceleyin.")
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        self.layout.addWidget(desc)

        form_group = QGroupBox("Analiz Parametreleri")
        form_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                margin-top: 14px;
                background: rgba(255,255,255,0.7);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #334155;
                font-weight: 700;
                font-size: 13px;
            }
            QLabel { color: #334155; font-size: 12px; font-weight: 600; margin-bottom: 2px; }
            QListWidget {
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                padding: 4px;
                font-size: 13px;
            }
            QListWidget::item { 
                padding: 8px; 
                border-radius: 4px; 
                color: #1E293B;
            }
            QListWidget::item:hover { background: #F1F5F9; }
            QListWidget::indicator {
                width: 18px;
                height: 18px;
                border: 1.5px solid #CBD5E1;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::indicator:checked {
                background-color: #4F46E5;
                border-color: #4F46E5;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjIwIDYgOSAxNyA0IDEyIj48L3BvbHlsaW5lPjwvc3ZnPg==);
            }
            QListWidget::indicator:unchecked:hover {
                border-color: #94A3B8;
            }
            QComboBox {
                min-height: 42px;
                padding: 0px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #0F172A;
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #4F46E5;
                selection-color: white;
                color: #0F172A;
                font-size: 13px;
                border: 1px solid #E2E8F0;
                outline: none;
            }
        """)
        form_layout = QVBoxLayout(form_group)
        form_layout.setContentsMargins(18, 28, 18, 18)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("1. Analiz Edilecek Kodları Seçin:"))
        self.code_list = QListWidget()
        self.code_list.setMinimumHeight(200)
        sorted_codes = sorted(self.codes, key=lambda x: x['name'].lower())
        for code in sorted_codes:
            item = QListWidgetItem(code['name'])
            item.setData(Qt.ItemDataRole.UserRole, code['id'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.code_list.addItem(item)
        form_layout.addWidget(self.code_list)

        sel_btns = QHBoxLayout()
        btn_all = QPushButton("Tümünü Seç")
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(self._select_all_codes)
        btn_all.setStyleSheet("""
            QPushButton {
                background: #F8FAFC;
                color: #334155;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 8px 14px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)

        btn_none = QPushButton("Seçimi Kaldır")
        btn_none.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_none.clicked.connect(self._select_no_codes)
        btn_none.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 14px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        sel_btns.addWidget(btn_all)
        sel_btns.addWidget(btn_none)
        sel_btns.addStretch()
        form_layout.addLayout(sel_btns)
        
        form_layout.addSpacing(10)

        form_layout.addWidget(QLabel("2. Gruplandırma Değişkenini Seçin:"))
        self.var_combo = QComboBox()
        for var in self.variables:
            self.var_combo.addItem(var['name'], var['id'])
        form_layout.addWidget(self.var_combo)
        
        self.layout.addWidget(form_group)
        self.layout.addSpacing(10)

        btns = QHBoxLayout()
        btns.addStretch()

        self.run_btn = QPushButton("Analiz Et")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self.accept)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 32px;
                font-weight: 800;
                font-size: 14px;
            }
            QPushButton:hover { background: #4338CA; }
        """)
        btns.addWidget(self.run_btn)
        
        btns.addStretch()
        self.add_size_grip(btns)
        self.layout.addLayout(btns)
        
    def _select_all_codes(self):
        for i in range(self.code_list.count()): self.code_list.item(i).setCheckState(Qt.CheckState.Checked)

    def _select_no_codes(self):
        for i in range(self.code_list.count()): self.code_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    def get_selection(self) -> Tuple[List[int], str, int, str]:
        selected_ids, selected_names = [], []
        for i in range(self.code_list.count()):
            item = self.code_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_ids.append(item.data(Qt.ItemDataRole.UserRole))
                selected_names.append(item.text())
        return selected_ids, ", ".join(selected_names) if selected_names else "Seçili Değil", self.var_combo.currentData(), self.var_combo.currentText()

from ..common import ModernSegmentCard

class QuotesByVariablesResultWidget(QFrame):
    """Displays coded segments grouped by variable values as a tab widget."""
    def __init__(self, code_names: str, var_name: str, grouped_data: Dict, parent=None):
        super().__init__(parent)
        self.code_names = code_names
        self.var_name = var_name
        self.grouped_data = grouped_data['groups']
        self.total_segments = grouped_data['total_segments']
        self._setup_ui()
        
    def _setup_ui(self):
        self.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Main Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.setSpacing(20)
        
        # Iterate Groups
        for group_val in sorted(self.grouped_data.keys(), key=lambda x: str(x).lower()):
            segments = self.grouped_data[group_val]
            
            group_box = QFrame()
            group_box.setStyleSheet("background: transparent;")
            group_layout = QVBoxLayout(group_box)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(5)
            
            # Group Header
            gh = QLabel(f"📍 {group_val} <span style='color: #6366F1;'>({len(segments)})</span>")
            gh.setStyleSheet("font-size: 13px; font-weight: 800; color: #1E293B; background: #F1F5F9; padding: 6px 12px; border-radius: 4px;")
            group_layout.addWidget(gh)
            
            # Cards
            for seg in segments:
                card = ModernSegmentCard(
                    seg, 
                    seg.get('code_name'), 
                    seg.get('code_color', '#4F46E5')
                )
                group_layout.addWidget(card)
                card.adjust_height_to_content()
                
            content_layout.addWidget(group_box)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
