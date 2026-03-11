"""
Modern Save-Before-Exit Dialog for LexiScholar
Provides Save, Don't Save, and Cancel options.
"""

from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from .modern_dialog import ModernBaseDialog
from ui.styles import get_color


class ModernSaveExitDialog(ModernBaseDialog):
    """
    A modern dialog with three options:
    - Save (Accepts) -> result 1
    - Don't Save (Custom code) -> result 2
    - Cancel (Rejects) -> result 0
    """
    
    def __init__(self, parent=None, title: str = "Değişiklikleri Kaydet", 
                 message: str = "Kaydedilmemiş değişiklikleriniz var. Çıkmadan önce kaydetmek ister misiniz?"):
        super().__init__(parent, min_width=450, min_height=200)
        self.title_text = title
        self.message_text = message
        self._setup_ui()
    
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header
        header = self.build_ribbon_header("💾", self.title_text)
        self.layout.addWidget(header)
        
        # Message
        message_label = QLabel(self.message_text)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            font-size: 14px; 
            color: {get_color('text_secondary')}; 
            line-height: 1.6; 
            padding: 20px 0;
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(message_label, 1)
        
        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        # Cancel Button
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {get_color('border')};
                border-radius: 6px;
                color: {get_color('text_secondary')};
                font-size: 13px;
                font-weight: 500;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {get_color('bg_hover')};
            }}
        """)
        button_layout.addWidget(self.cancel_btn)

        # Don't Save Button
        self.no_btn = QPushButton("Kaydetme")
        self.no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.no_btn.clicked.connect(lambda: self.done(2))
        self.no_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FEE2E2;
                border: 1px solid #FECACA;
                border-radius: 6px;
                color: #B91C1C;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: #FECACA;
            }}
        """)
        button_layout.addWidget(self.no_btn)
        
        # Save Button
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('primary')};
                border: none;
                border-radius: 6px;
                color: {get_color('text_inverse')};
                font-size: 13px;
                font-weight: 700;
                padding: 8px 24px;
            }}
            QPushButton:hover {{
                background-color: {get_color('primary_dark')};
            }}
        """)
        button_layout.addWidget(self.save_btn)
        
        button_layout.addStretch()
        self.layout.addLayout(button_layout)
        
        # Set default button
        self.save_btn.setDefault(True)
    
    def get_result(self) -> str:
        """Returns 'save', 'discard', or 'cancel'."""
        code = self.exec()
        if code == 1: return "save"
        if code == 2: return "discard"
        return "cancel"
