"""
Code Statistics Widget and Dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QFont, QDesktopServices
from ..styles import TABLE_STYLE, get_color
from ..common.modern_dialog import ModernBaseDialog

class StatisticsWidget(QWidget):
    """Widget showing code statistics for tab integration."""
    
    def __init__(self, analysis_tools, parent=None):
        super().__init__(parent)
        self.analysis = analysis_tools
        self._setup_ui()
        self._load_data()
    
    def _open_help(self, anchor):
        """Open encyclopedia help with correct anchor."""
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        page = os.path.join(base, "docs", "encyclopedia", "analysis_tools.html")
        url = QUrl.fromLocalFile(page)
        if anchor:
            url.setFragment(anchor.lstrip('#'))
        QDesktopServices.openUrl(url)

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Kod", "Segment Sayısı", "Belge Sayısı", "Toplam Karakter", "Yoğunluk"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        
        self.table.verticalHeader().setVisible(False)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {get_color('bg_panel')};
                alternate-background-color: {get_color('bg_main')};
                border: 1px solid {get_color('border')};
                border-radius: 8px;
                gridline-color: {get_color('bg_hover')};
                font-size: 13px;
                color: {get_color('text_primary')};
                selection-background-color: {get_color('primary_50')};
                selection-color: {get_color('text_primary')};
            }}
            QTableWidget::item {{ padding: 10px; outline: none; }}
            QTableWidget::item:hover {{ background-color: {get_color('bg_hover')}; color: {get_color('text_secondary')}; outline: none; }}
            QTableWidget::item:selected {{ background-color: {get_color('primary_50')}; color: {get_color('text_primary')}; outline: none; }}
            QHeaderView::section {{
                background-color: {get_color('bg_main')};
                padding: 12px;
                border: none;
                border-bottom: 1px solid {get_color('border')};
                font-weight: 700;
                color: {get_color('text_secondary')};
                font-size: 11px;
                text-transform: uppercase;
            }}
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table)
        
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"background-color: {get_color('bg_main')}; border-radius: 8px; border: 1px solid {get_color('border')};")
        summary_layout = QHBoxLayout(summary_frame)
        
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 13px; font-weight: 600;")
        summary_layout.addWidget(self.summary_label)
        layout.addWidget(summary_frame)
        
        self.setStyleSheet(f"background-color: {get_color('bg_panel')};")
    
    def _load_data(self):
        """Load statistics data."""
        stats = self.analysis.get_code_statistics()
        
        self.table.setRowCount(len(stats))
        total_segments = sum(s['segment_count'] for s in stats)
        
        for i, stat in enumerate(stats):
            name_item = QTableWidgetItem(f"● {stat['name']}")
            name_item.setForeground(QColor(stat['color']))
            name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            
            name_item.setData(Qt.ItemDataRole.UserRole, stat['id'])
            name_item.setData(Qt.ItemDataRole.UserRole + 1, stat['name'])
            name_item.setData(Qt.ItemDataRole.UserRole + 2, stat['color'])
            
            self.table.setItem(i, 0, name_item)
            
            seg_item = QTableWidgetItem(str(stat['segment_count']))
            seg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, seg_item)
            
            doc_item = QTableWidgetItem(str(stat['document_count']))
            doc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, doc_item)
            
            char_item = QTableWidgetItem(f"{stat['total_characters']:,}")
            char_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 3, char_item)
            
            if total_segments > 0:
                density = (stat['segment_count'] / total_segments) * 100
                dens_text = f"{density:.1f}%"
            else:
                dens_text = "0%"
            
            dens_item = QTableWidgetItem(dens_text)
            dens_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 4, dens_item)
        
        self.summary_label.setText(
            f"Toplam: {len(stats)} kod, {total_segments} segment"
        )
        
    def _on_cell_clicked(self, row, col):
        """Handle double-click on a row to show segments."""
        name_item = self.table.item(row, 0)
        if not name_item: return
        
        code_id = name_item.data(Qt.ItemDataRole.UserRole)
        code_name = name_item.data(Qt.ItemDataRole.UserRole + 1)
        code_color = name_item.data(Qt.ItemDataRole.UserRole + 2)
        
        if code_id is None: return
        
        parent = self.parent()
        while parent:
            if hasattr(parent, '_on_coded_segments_requested'):
                parent._on_coded_segments_requested(code_id, code_name, code_color)
                return
            parent = parent.parent()
    
    def _table_style(self):
        return TABLE_STYLE


class StatisticsDialog(ModernBaseDialog):
    """Standalone dialog wrapper for StatisticsWidget."""
    def __init__(self, analysis_tools, parent=None):
        super().__init__(parent, min_width=800, min_height=600)
        self._setup_ui(analysis_tools)
        
    def _setup_ui(self, analysis_tools):
        self._setup_base_ui()
        
        header_layout = QHBoxLayout()
        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel("Kod İstatistikleri")
        title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {get_color('text_primary')};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        close_btn_top = QPushButton("✕")
        close_btn_top.setFixedSize(32, 32)
        close_btn_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_top.clicked.connect(self.reject)
        close_btn_top.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {get_color('text_secondary')}; font-size: 18px; font-weight: bold; border: none; border-radius: 16px; }}
            QPushButton:hover {{ background: {get_color('error_bg')}; color: {get_color('error')}; }}
        """)
        header_layout.addWidget(close_btn_top)
        self.layout.addLayout(header_layout)

        self.widget = StatisticsWidget(analysis_tools, self)
        self.layout.addWidget(self.widget)
        
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: {get_color('primary')}; color: white; border: none; border-radius: 10px; padding: 10px 40px; font-weight: 800; font-size: 13px; }}
            QPushButton:hover {{ background: {get_color('primary_dark')}; }}
        """)
        footer_layout.addWidget(close_btn)
        
        footer_layout.addStretch()
        self.layout.addLayout(footer_layout)
