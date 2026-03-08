"""
Base UI for Coded Segments Dialog
Contains the main dialog class and layout definitions.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QLabel, QWidget, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ..styles import COLORS

COLUMNS = [
    ("Yorum",          120),
    ("Belge Grubu",    130),
    ("Belge Adı",      160),
    ("Kod Adı",        120),
    ("Başlangıç",       80),
    ("Bitiş",           80),
    ("Ağırlık",         70),
    ("Parafraze",      160),
    ("Önizleme Metni", 280),
]

_DIALOG_EXTRA_STYLE = f"""
QDialog {{
    background-color: {COLORS['bg_main']};
    font-family: 'Segoe UI', sans-serif;
}}
QPushButton#toolBtn {{
    background-color: #FFFFFF;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 9pt;
    font-weight: 600;
}}
QPushButton#toolBtn:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['border_hover']};
    color: {COLORS['text_primary']};
}}
QPushButton#primaryBtn {{
    background-color: #4F46E5;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 9pt;
    font-weight: 700;
}}
QPushButton#primaryBtn:hover {{ background-color: #4338CA; }}
QWidget#headerBar {{
    background-color: {COLORS['bg_panel']};
    border-bottom: 2px solid {COLORS['border_hover']};
}}
QTextEdit#previewEdit {{
    background: transparent;
    color: #1E293B;
    border: none;
    font-size: 11pt;
    line-height: 1.4;
    padding: 14px;
    selection-background-color: #EEF2FF;
}}
QTableWidget {{
    background-color: #FFFFFF;
    gridline-color: {COLORS['border']};
    border: none;
    font-size: 9pt;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['bg_selected']};
}}
QHeaderView::section {{
    background-color: {COLORS['primary_100']};
    color: {COLORS['text_secondary']};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {COLORS['border_hover']};
    border-bottom: 2px solid {COLORS['border_hover']};
    font-weight: 700;
    text-transform: uppercase;
}}
QLabel#statusLabel {{
    color: {COLORS['text_muted']};
    font-size: 8.5pt;
    padding: 4px 0px;
}}
QLabel#countBadge {{
    background-color: #4F46E5;
    color: #FFFFFF;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 8pt;
    font-weight: 700;
}}
QSplitter::handle:vertical {{
    background-color: {COLORS['border_hover']};
    height: 4px;
    margin: 0 8px;
}}
QSplitter::handle:vertical:hover {{ background-color: #4F46E5; }}
"""

class CodedSegmentsDialogBase(QDialog):
    segment_navigate_requested = pyqtSignal(int, int)

    COL_COMMENT  = 0
    COL_GROUP    = 1
    COL_DOC_NAME = 2
    COL_CODE     = 3
    COL_START    = 4
    COL_END      = 5
    COL_WEIGHT   = 6
    COL_PARAPHRASE = 7
    COL_PREVIEW  = 8

    def __init__(self, segments, code_name="", code_color="#4F46E5", parent=None):
        super().__init__(parent)
        self._segments = segments
        self._code_name = code_name
        self._code_color = code_color
        
        self.setWindowTitle(f"🔎 Kodlanmış Bölümler — {code_name}")
        self.setMinimumSize(QSize(960, 640))
        self.resize(QSize(1200, 750))
        self.setStyleSheet(_DIALOG_EXTRA_STYLE)
        self.setSizeGripEnabled(True)

    def _setup_base_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Build header
        self.header = self._build_header()
        root.addWidget(self.header)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(6)
        
        self.preview_panel = self._build_preview_panel()
        self.table_panel = self._build_table_panel()
        
        splitter.addWidget(self.preview_panel)
        splitter.addWidget(self.table_panel)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        splitter.setSizes([220, 480])
        
        root.addWidget(splitter, 1)

        # Footer
        self.footer = self._build_footer()
        root.addWidget(self.footer)

    def _build_header(self):
        from .table_manager import CodedSegmentsTableMixin
        # This will be implemented in the final class or overridden
        pass

    def _build_preview_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        strip = QLabel("  📄  SEGMENT ÖNİZLEME")
        strip.setStyleSheet(
            f"background-color:{COLORS['primary_50']}; color:{COLORS['text_secondary']}; "
            f"font-size:8pt; font-weight:700; padding:6px 12px; border-bottom:1px solid {COLORS['border']};"
        )
        layout.addWidget(strip)
        
        self.preview_edit = QTextEdit()
        self.preview_edit.setObjectName("previewEdit")
        self.preview_edit.setReadOnly(True)
        layout.addWidget(self.preview_edit)
        return container

    def _build_table_panel(self):
        # Implementation delegated to CodedSegmentsTableMixin
        pass

    def _build_footer(self):
        footer = QWidget()
        footer.setStyleSheet(f"background-color:{COLORS['bg_panel']}; border-top:1px solid {COLORS['border']};")
        footer.setFixedHeight(40)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(16, 4, 16, 4)
        
        self.lbl_status = QLabel("Segment seçmek için tabloya tıklayın.")
        self.lbl_status.setObjectName("statusLabel")
        layout.addWidget(self.lbl_status)
        layout.addStretch()
        
        tip = QLabel("💡 Çift tıklayarak belgedeki konuma git")
        tip.setObjectName("statusLabel")
        layout.addWidget(tip)
        return footer
