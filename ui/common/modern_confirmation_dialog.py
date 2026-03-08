"""
Modern Confirmation Dialog for LexiScholar
Standardized Yes/No confirmation with modern styling.
"""

from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from .modern_dialog import ModernBaseDialog
from ui.styles import get_color


class ModernConfirmationDialog(ModernBaseDialog):
    """A modern yes/no confirmation dialog with Turkish labels."""
    
    def __init__(self, parent=None, title: str = "Onay", message: str = "", 
                 yes_text: str = "Evet", no_text: str = "Hayır", 
                 default_yes: bool = False):
        super().__init__(parent, min_width=400, min_height=180)
        self.title_text = title
        self.message_text = message
        self.yes_text = yes_text
        self.no_text = no_text
        self.default_yes = default_yes
        self._setup_ui()
    
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header
        header = self.build_ribbon_header("❓", self.title_text)
        self.layout.addWidget(header)
        
        # Message
        message_label = QLabel(self.message_text)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            font-size: 14px; 
            color: {get_color('text_secondary')}; 
            line-height: 1.5; 
            padding: 20px 0;
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(message_label, 1)
        
        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # No Button
        self.no_btn = QPushButton(self.no_text)
        self.no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.no_btn.clicked.connect(self.reject)
        self.no_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('bg_panel')};
                border: 1px solid {get_color('border')};
                border-radius: 6px;
                color: {get_color('text_secondary')};
                font-size: 13px;
                font-weight: 600;
                padding: 8px 24px;
            }}
            QPushButton:hover {{
                background-color: {get_color('bg_hover')};
                border-color: {get_color('border_hover')};
            }}
        """)
        button_layout.addWidget(self.no_btn)
        
        # Yes Button
        self.yes_btn = QPushButton(self.yes_text)
        self.yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.yes_btn.clicked.connect(self.accept)
        self.yes_btn.setStyleSheet(f"""
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
        button_layout.addWidget(self.yes_btn)
        
        button_layout.addStretch()
        self.layout.addLayout(button_layout)
        
        # Set default button
        if self.default_yes:
            self.yes_btn.setDefault(True)
        else:
            self.no_btn.setDefault(True)
    
    def get_result(self) -> bool:
        """Returns True if Yes was clicked, False if No was clicked."""
        return self.exec() == 1
