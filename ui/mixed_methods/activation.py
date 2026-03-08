"""
Variable-based document activation dialog.
"""

from typing import List, Dict, Tuple
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QComboBox, QPushButton, QToolButton,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor
from ..common.modern_dialog import ModernBaseDialog

class ActivateByVariablesDialog(ModernBaseDialog):
    """Wizard to activate documents based on variable values."""
    def __init__(self, variables: List[Dict], var_value_dao, parent=None):
        super().__init__(parent, min_width=620, min_height=400)
        self.variables = variables
        self.var_value_dao = var_value_dao
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header Area
        header_layout = QHBoxLayout()
        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel("Belge Filtreleme Sihirbazı")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Red X Close Button
        close_btn_top = QPushButton("✕")
        close_btn_top.setFixedSize(32, 32)
        close_btn_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_top.clicked.connect(self.reject)
        close_btn_top.setStyleSheet("""
            QPushButton { background: transparent; color: #64748B; font-size: 18px; font-weight: bold; border: none; border-radius: 16px; }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; }
        """)
        header_layout.addWidget(close_btn_top)
        self.layout.addLayout(header_layout)

        desc = QLabel("Belirlediğiniz kurala uyan belgeleri otomatik olarak etkinleştirin.")
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        self.layout.addWidget(desc)

        form_group = QGroupBox("Kural Tanımla")
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
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                color: #1E293B;
                font-size: 13px;
                min-height: 32px;
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
                padding: 2px;
            }
        """)
        form_layout = QVBoxLayout(form_group)
        form_layout.setContentsMargins(18, 28, 18, 18)
        form_layout.setSpacing(12)

        h_ctrl = QHBoxLayout()
        self.var_combo = QComboBox()
        self.var_combo.setMinimumWidth(200)
        for var in self.variables:
            self.var_combo.addItem(var['name'], var['id'])
        self.var_combo.currentIndexChanged.connect(self._on_var_changed)
        
        self.op_combo = QComboBox()
        self.op_combo.setMinimumWidth(120)
        self.op_combo.addItems(["= (eşittir)", "≠ (eşit değil)", "∋ (içerir)"])
        
        self.val_combo = QComboBox()
        self.val_combo.setMinimumWidth(200)
        self.val_combo.setEditable(True)
        
        h_ctrl.addWidget(self.var_combo, 3)
        h_ctrl.addWidget(self.op_combo, 2)
        h_ctrl.addWidget(self.val_combo, 3)
        form_layout.addLayout(h_ctrl)
        
        self.layout.addWidget(form_group)

        status = QLabel("ℹ️ Kurala uyan belgeler otomatik olarak etkinleştirilecek, diğerleri deaktif edilecektir.")
        status.setStyleSheet("color: #64748B; font-size: 12px; font-style: italic;")
        status.setWordWrap(True)
        self.layout.addWidget(status)
        
        self.layout.addSpacing(10)

        btns = QHBoxLayout()
        btns.addStretch()

        self.btn_run = QPushButton("Etkinleştir")
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn = self.btn_run # For internal consistency if needed
        self.btn_run.clicked.connect(self.accept)
        self.btn_run.setStyleSheet("""
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
        btns.addWidget(self.btn_run)
        
        btns.addStretch()
        self.layout.addLayout(btns)
        
        if self.variables:
            self._on_var_changed(0)
            
    def _on_var_changed(self, index):
        var_id = self.var_combo.currentData()
        if var_id:
            all_vals = self.var_value_dao.get_all_document_values()
            vals = sorted(list(set(str(v['value']) for v in all_vals if v['variable_id'] == var_id and v['value'] is not None)))
            self.val_combo.clear(); self.val_combo.addItems(vals)
            
    def get_rule(self) -> Tuple[int, str, str]:
        var_id = self.var_combo.currentData(); op = self.op_combo.currentText().split(" ")[0]; val = self.val_combo.currentText().strip()
        return var_id, op, val
