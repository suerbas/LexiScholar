"""
Populator logic for Survey Quick Code.
"""

from PyQt6.QtWidgets import QPushButton, QLabel, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from .answer_block import AnswerBlock
from ..styles import get_color

class SurveyQuickCodePopulatorMixin:
    """Handles building the answer list and code list UI."""

    def _populate_answers(self):
        """Build AnswerBlock widgets."""
        # Clear
        while self._answers_layout.count() > 1:
            item = self._answers_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self._answer_blocks = []
        for idx, seg in enumerate(self._segments):
            block = AnswerBlock(seg, idx, self._answers_container)
            block.text_selected.connect(self._on_text_selected)
            self._answer_blocks.append(block)
            self._answers_layout.insertWidget(idx, block)

    def _refresh_code_list(self):
        """Build the quick-code button panel."""
        while self._code_list_layout.count() > 1:
            item = self._code_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for code in self._all_codes:
            btn = QPushButton(f"● {code['name']}")
            c = code.get('color', get_color('primary'))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {get_color('bg_panel')}; color: {c}; border: 1.5px solid {c};
                    border-radius: 6px; padding: 7px 10px; font-size: 12px; font-weight: 600; text-align: left;
                }}
                QPushButton:hover {{ background-color: {c}18; }}
            """)
            btn.clicked.connect(lambda checked, co=code: self._assign_code(co))
            self._code_list_layout.insertWidget(self._code_list_layout.count() - 1, btn)
