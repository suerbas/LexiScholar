"""
Variance Analysis (ANOVA) dialogs for Mixed Methods.
"""

from typing import List, Dict
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QFrame, QSizePolicy, QToolButton, QGraphicsDropShadowEffect, QWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QFont, QDesktopServices
from ..common.modern_dialog import ModernBaseDialog

class VarianceAnalysisDialog(ModernBaseDialog):
    """Selection dialog for One-Way ANOVA."""
    def __init__(self, codes: List[Dict], variables: List[Dict], parent=None):
        super().__init__(parent, min_width=560, min_height=480)
        self.codes = codes
        self.variables = variables
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("📊", "Tek Yönlü Varyans Analizi (One-Way ANOVA)")
        self.layout.addWidget(header)

        desc = QLabel(
            "Bir kodun kullanım sıklığının (frekans), seçilen değişken grupları arasında istatistiksel olarak "
            "anlamlı bir fark gösterip göstermediğini test eder."
        )
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

        form_layout.addWidget(QLabel("Bağımlı Değişken (Kod Frekansı):"))
        self.code_combo = QComboBox()
        for code in sorted(self.codes, key=lambda x: x['name'].lower()):
            self.code_combo.addItem(code['name'], code['id'])
        form_layout.addWidget(self.code_combo)
        
        form_layout.addSpacing(6)

        form_layout.addWidget(QLabel("Bağımsız Değişken (Grup):"))
        self.var_combo = QComboBox()
        for var in self.variables:
            self.var_combo.addItem(var['name'], var['id'])
        form_layout.addWidget(self.var_combo)

        self.layout.addWidget(form_group)
        self.layout.addSpacing(10)

        btns = QHBoxLayout()
        btns.addStretch()

        self.run_btn = QPushButton("Analizi Çalıştır")
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
        
    def get_selection(self):
        return self.code_combo.currentData(), self.var_combo.currentData(), self.code_combo.currentText().replace("🏷️ ", ""), self.var_combo.currentText().replace("🔹 ", "")


class VarianceResultWidget(QFrame):
    """Displays ANOVA results as a tab widget."""
    def __init__(self, result: Dict, code_name: str, var_name: str, parent=None):
        super().__init__(parent)
        self.result = result
        self.code_name = code_name
        self.var_name = var_name
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Summary Box
        is_sig = self.result.get('significant', False)
        p_val = self.result.get('p_value', 1.0)
        f_stat = self.result.get('f_statistic', 0.0)
        
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#F0FDF4' if is_sig else '#F8FAFC'}; 
                border: 1px solid {'#16A34A' if is_sig else '#E2E8F0'}; 
                border-radius: 12px; 
                padding: 20px;
            }}
        """)
        sl = QVBoxLayout(summary_frame)
        
        status_text = "✅ İstatistiksel olarak ANLAMLI fark bulundu." if is_sig else "❌ İstatistiksel olarak anlamlı bir fark BULUNAMADI."
        status_lbl = QLabel(status_text)
        status_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {'#166534' if is_sig else '#475569'};")
        sl.addWidget(status_lbl)
        
        detail_text = f"F({self.result.get('df_between')}, {self.result.get('df_within')}) = {f_stat:.3f}, p = {p_val:.4f}"
        if p_val < 0.001: detail_text += " (p < .001)"
        
        detail_lbl = QLabel(detail_text)
        detail_lbl.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; color: #334155; margin-top: 8px;")
        sl.addWidget(detail_lbl)
        
        layout.addWidget(summary_frame)
        
        # Group Stats Table
        table_header = QLabel("📊 Grup İstatistikleri")
        table_header.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B; margin-top: 10px;")
        layout.addWidget(table_header)
        
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Grup", "N (Belge)", "Ortalama (Mean)", "Std. Sapma"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        
        groups = self.result.get('groups', {})
        table.setRowCount(len(groups))
        
        sorted_groups = sorted(groups.keys())
        for i, g_name in enumerate(sorted_groups):
            stats = groups[g_name]
            table.setItem(i, 0, QTableWidgetItem(str(g_name)))
            table.setItem(i, 1, QTableWidgetItem(str(stats['n'])))
            table.setItem(i, 2, QTableWidgetItem(f"{stats['mean']:.2f}"))
            table.setItem(i, 3, QTableWidgetItem(f"{stats['std']:.2f}"))
            
        table.setStyleSheet("""
            QTableWidget { 
                border: 1px solid #E2E8F0; 
                border-radius: 8px; 
                background-color: white;
                gridline-color: #F1F5F9;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section { 
                background-color: #F8FAFC; 
                border: none; 
                border-bottom: 1px solid #E2E8F0; 
                padding: 10px; 
                font-weight: bold; 
                color: #475569;
            }
        """)
        table.setMinimumHeight(200)
        layout.addWidget(table)
        
        layout.addStretch()
        
        # No footer actions needed for tab view (user closes tab)
