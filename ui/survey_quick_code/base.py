"""
Base layout and UI components for Survey Quick Code Dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..styles import COLORS, get_color

class SurveyQuickCodeDialogBase(QDialog):
    """Base structure with three panels and layout logic."""
    
    # Signals
    sub_code_assigned = pyqtSignal(int, int, str, int)
    sub_code_created = pyqtSignal(str, str, int, str)

    def __init__(self, segments: list, code_name: str, code_id: int, code_color: str, parent=None):
        super().__init__(parent)
        self._segments = segments
        self._code_name = code_name
        self._code_id = code_id
        self._code_color = code_color
        self._answer_blocks = []
        
    def _setup_base_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1. Toolbar area
        self.toolbar_container = QWidget()
        self.toolbar_container.setFixedHeight(44)
        self.toolbar_container.setStyleSheet(f"""
            background-color: {get_color('bg_panel')};
            border-bottom: 1px solid {get_color('border')};
        """)
        root.addWidget(self.toolbar_container)

        # 2. Main Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(f"QSplitter::handle {{ background: {get_color('border')}; }}")

        # Panels will be built and added by mixins/subclasses
        root.addWidget(self.splitter)

        # 3. Status Bar
        self._status_bar = QLabel(f"  Total: {len(self._segments)} yanıt")
        self._status_bar.setStyleSheet(f"""
            background-color: {get_color('bg_panel')};
            border-top: 1px solid {get_color('border')};
            color: {get_color('text_secondary')};
            font-size: 11px; padding: 5px 16px;
        """)
        self._status_bar.setFixedHeight(30)
        root.addWidget(self._status_bar)
        
        self.setStyleSheet(f"QDialog {{ background-color: {get_color('bg_panel')}; }}")

    def _tool_btn_style(self, bg=None, color=None) -> str:
        bg = bg or get_color('bg_main')
        color = color or get_color('text_secondary')
        return f"""
            QPushButton {{
                background-color: {bg}; color: {color};
                border: 1px solid {get_color('border')}; border-radius: 6px;
                padding: 5px 12px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {get_color('bg_hover')}; }}
        """
