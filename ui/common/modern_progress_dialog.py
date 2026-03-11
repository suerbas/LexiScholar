"""
Modern Progress Dialog for LexiScholar.
Features a blue ribbon header and styled progress bar.
"""

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from .modern_dialog import ModernBaseDialog
from ui.styles import get_color

class ModernProgressDialog(ModernBaseDialog):
    """
    A modern alternative to QProgressDialog with blue ribbon header.
    """
    canceled = pyqtSignal()

    def __init__(self, parent=None, title: str = "İşlem Yapılıyor", 
                 message: str = "Lütfen bekleyin...", 
                 cancel_text: str = "İptal"):
        super().__init__(parent, min_width=400, min_height=180)
        self.title_text = title
        self.message_text = message
        self.cancel_text = cancel_text
        self._setup_ui()

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header (Ribbon)
        self.header = self.build_ribbon_header("⏳", self.title_text, on_close=self._on_cancel)
        self.layout.addWidget(self.header)

        # Message Label
        self.status_label = QLabel(self.message_text)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            font-size: 14px;
            color: {get_color('text_secondary')};
            padding: 10px 0;
        """)
        self.layout.addWidget(self.status_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 0)  # Indeterminate by default
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {get_color('bg_panel')};
                border: 1px solid {get_color('border')};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {get_color('primary')};
                border-radius: 4px;
            }}
        """)
        self.layout.addWidget(self.progress_bar)

        # Cancel Button area (Optional, only if cancel_text is provided)
        if self.cancel_text:
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            self.cancel_btn = QPushButton(self.cancel_text)
            self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.cancel_btn.clicked.connect(self._on_cancel)
            self.cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    border: 1px solid {get_color('border')};
                    border-radius: 6px;
                    color: {get_color('text_secondary')};
                    font-size: 12px;
                    font-weight: 600;
                    padding: 6px 16px;
                }}
                QPushButton:hover {{
                    background-color: #FEF2F2;
                    color: #EF4444;
                    border-color: #F87171;
                }}
            """)
            btn_layout.addWidget(self.cancel_btn)
            btn_layout.addStretch()
            self.layout.addLayout(btn_layout)

    def _on_cancel(self):
        self.canceled.emit()
        self.reject()

    def setLabelText(self, text: str):
        """Standard method name to match QProgressDialog API."""
        self.status_label.setText(text)

    def setRange(self, min_val: int, max_val: int):
        self.progress_bar.setRange(min_val, max_val)

    def setValue(self, value: int):
        self.progress_bar.setValue(value)
