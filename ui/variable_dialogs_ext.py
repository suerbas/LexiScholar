"""
Analysis Dialogs for LexiScholar - Variable Statistics
UI for variable distribution and frequency analysis.
"""

from typing import List, Dict, Tuple, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QTabWidget, QWidget, QComboBox,
    QSpinBox, QGroupBox, QHeaderView, QMessageBox, QProgressBar, QFrame,
    QScrollArea, QTextEdit, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
    QSizeGrip, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QFont, QDesktopServices
from .styles import COLORS, TABLE_STYLE
from .common.modern_dialog import ModernBaseDialog
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class VariableStatisticsDialog(ModernBaseDialog):
    """Dialog for selecting a variable for distribution analysis."""
    
    def __init__(self, variables, parent=None):
        super().__init__(parent, min_width=480, min_height=400)
        self.variables = variables
        self.selected_var_id = None
        self.selected_var_name = None
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("📊", "Değişken İstatistikleri")
        self.layout.addWidget(header)

        desc = QLabel("İstatistiklerini (dağılımını) görmek istediğiniz değişkeni seçin.")
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        self.layout.addWidget(desc)

        self.var_list = QListWidget()
        self.var_list.setMinimumHeight(240)
        
        # SATIRLARIN KESİLMESİNİ ENGELLEYEN KRİTİK AYARLAR
        self.var_list.setWordWrap(True)                   # Sığmazsa alt satıra geç
        self.var_list.setTextElideMode(Qt.TextElideMode.ElideNone) # Asla "..." koyma, metni tam dök
        self.var_list.setResizeMode(QListWidget.ResizeMode.Adjust) # Pencere değiştikçe satırı uzat
        self.var_list.setUniformItemSizes(False)         # Her satır kendi genişliğini belirlesin
        self.var_list.setSpacing(0)                      # Satır içi sınırlayıcı boşlukları kaldır
        
        for var in self.variables:
            item = QListWidgetItem(var['name'])
            item.setData(Qt.ItemDataRole.UserRole, var['id'])
            self.var_list.addItem(item)
        
        self.var_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                background: white;
                padding: 5px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 15px;
                border-radius: 8px;
                color: #1E293B;
                margin-bottom: 2px;
                border: none;
            }
            QListWidget::item:hover {
                background: #F8FAFC;
            }
            QListWidget::item:selected {
                background: #EEF2FF;
                color: #4F46E5;
                font-weight: 700;
            }
        """)
        self.var_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.var_list)

        # Footer with Buttons & Size Grip
        footer_layout = QHBoxLayout()
        
        btns = QHBoxLayout()
        btns.addStretch() # Center alignment handle

        self.analyze_btn = QPushButton("Analizi Başlat")
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.analyze_btn.setStyleSheet("""
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
        btns.addWidget(self.analyze_btn)
        
        btns.addStretch() # Center alignment handle
        
        footer_layout.addLayout(btns)
        
        footer_layout.addStretch()
        self.layout.addLayout(footer_layout)

    def _on_analyze(self):
        item = self.var_list.currentItem()
        if not item:
            show_warning(self, "Uyarı", "Lütfen listeden bir değişken seçin.")
            return
            
        self.selected_var_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_var_name = item.text()
        self.accept()
        
    def get_selected_variable(self):
        return self.selected_var_id, self.selected_var_name


class VariableStatisticsResultWidget(QWidget):
    """Widget showing variable frequency distribution results for tab integration."""
    
    def __init__(self, var_name, stats_data, parent=None):
        super().__init__(parent)
        self.var_name = var_name
        self.stats = stats_data['stats']
        self.total = stats_data['total_count']
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(28, 28, 28, 28)
        
        # Header (Removed redundant internal title since the blue ribbon provides it)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Değişken Değeri", "Frekans (N)", "Yüzde (%)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        self.table.setRowCount(len(self.stats))
        for i, row in enumerate(self.stats):
            # Append document names in parentheses (e.g. "Male (K1, K2)")
            doc_str = f" ({', '.join(row['docs'])})" if row.get('docs') else ""
            val_item = QTableWidgetItem(f"{row['value']}{doc_str}")
            
            count_item = QTableWidgetItem(str(row['count']))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_item = QTableWidgetItem(f"{row['percentage']:.1f}%")
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.table.setItem(i, 0, val_item)
            self.table.setItem(i, 1, count_item)
            self.table.setItem(i, 2, pct_item)
            
        layout.addWidget(self.table)
        
        # Summary Area
        summary_frame = QFrame()
        from .styles.palette import get_color
        summary_frame.setStyleSheet(f"background-color: {get_color('bg_main')}; border-radius: 8px; border: 1px solid {get_color('border')};")
        summary_layout = QHBoxLayout(summary_frame)
        
        summary_txt = f"<b>Toplam Belge:</b> {self.total} | <b>Değer Sayısı:</b> {len(self.stats)}"
        summary_lbl = QLabel(summary_txt)
        summary_lbl.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 13px;")
        summary_layout.addWidget(summary_lbl)
        layout.addWidget(summary_frame)
        
        self.setStyleSheet(f"background-color: {get_color('bg_panel')};")
        self.table.setStyleSheet(TABLE_STYLE)


class VariableStatisticsResultDialog(QDialog):
    """Standalone dialog wrapper for VariableStatisticsResultWidget."""
    def __init__(self, var_name, stats_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"İstatistik: {var_name}")
        self.setMinimumSize(700, 550)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.widget = VariableStatisticsResultWidget(var_name, stats_data, self)
        layout.addWidget(self.widget)
        
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
