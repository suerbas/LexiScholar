"""
AnswerBlock widget for Survey Quick Code.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QFrame
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor
from ..styles import COLORS, get_color

class AnswerBlock(QFrame):
    """
    A single answer block — shows the participant ID / document name as a header
    and the full answer text as an editable (read-only) QTextEdit so the user
    can select text to assign a sub-code.
    """
    text_selected = pyqtSignal(str, int, dict)   # selected_text, block_index, segment_info

    def __init__(self, segment: dict, block_index: int, parent=None):
        super().__init__(parent)
        self._segment = segment
        self._block_index = block_index
        self._code_color = get_color('primary')
        self._badges_layout = None   # set during _setup_ui
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)

        self.setStyleSheet(f"""
            AnswerBlock {{
                border: 1px solid {get_color('border')};
                border-radius: 8px;
                background-color: {get_color('bg_panel')};
                margin-bottom: 8px;
            }}
        """)

        # — Header row (document name + position) ————————————
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {get_color('primary_50')};
            border-bottom: 1px solid {get_color('border')};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 6, 10, 6)
        h_layout.setSpacing(12)

        doc_label = QLabel(f"📄 {self._segment.get('document_title', '—')}")
        doc_label.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {get_color('text_primary')};")
        h_layout.addWidget(doc_label)

        folder_label = QLabel(self._segment.get('folder_name', '') or '')
        folder_label.setStyleSheet(f"font-size: 11px; color: {get_color('text_secondary')};")
        h_layout.addWidget(folder_label)

        h_layout.addStretch()

        pos_lbl = QLabel(
            f"Konum {self._segment.get('start_pos', '')}–{self._segment.get('end_pos', '')}"
        )
        pos_lbl.setStyleSheet(f"font-size: 11px; color: {get_color('text_muted')};")
        h_layout.addWidget(pos_lbl)

        layout.addWidget(header)

        # — Text Area ———————————————————————————————————————————
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        raw_text = (self._segment.get("segment_text") or "").strip()
        self.text_edit.setPlainText(raw_text)

        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                background-color: {get_color('bg_panel')};
                padding: 10px 14px;
                font-size: 13px;
                color: {get_color('text_primary')};
                line-height: 1.7;
            }}
        """)

        doc_height = min(220, max(60, raw_text.count('\n') * 22 + 80))
        self.text_edit.setFixedHeight(doc_height)
        self.text_edit.selectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.text_edit)

        # — Code Badges Footer ———————————————————————
        self._badges_footer = QWidget()
        self._badges_footer.setStyleSheet(
            f"background-color: {get_color('bg_panel')};"
            f"border-top: 1px solid {get_color('border')};"
            "border-bottom-left-radius: 8px;"
            "border-bottom-right-radius: 8px;"
        )
        badges_row = QHBoxLayout(self._badges_footer)
        badges_row.setContentsMargins(10, 5, 10, 5)
        badges_row.setSpacing(6)

        lbl_kodlar = QLabel("🏷 Kodlar:")
        lbl_kodlar.setStyleSheet(f"font-size: 10px; color: {get_color('text_muted')}; font-weight: 600;")
        badges_row.addWidget(lbl_kodlar)

        self._badges_inner = QWidget()
        self._badges_layout = QHBoxLayout(self._badges_inner)
        self._badges_layout.setContentsMargins(0, 0, 0, 0)
        self._badges_layout.setSpacing(4)
        self._badges_layout.addStretch()
        badges_row.addWidget(self._badges_inner)
        badges_row.addStretch()

        self._badges_footer.setFixedHeight(32)
        layout.addWidget(self._badges_footer)

    def _on_selection_changed(self):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText().strip()
            if selected:
                self.text_selected.emit(selected, self._block_index, self._segment)

    def add_code_badge(self, code_name: str, code_color: str):
        if self._badges_layout is None: return
        pill = QLabel(f"  {code_name}  ")
        pill.setStyleSheet(f"""
            QLabel {{
                background-color: {code_color}22;
                color: {code_color};
                border: 1px solid {code_color}66;
                border-radius: 9px; font-size: 10px; font-weight: 700; padding: 1px 6px;
            }}
        """)
        count = self._badges_layout.count()
        self._badges_layout.insertWidget(count - 1, pill)

    def highlight_coded_text(self, color: str):
        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        bg = QColor(color)
        bg.setAlpha(40)
        fmt.setBackground(bg)
        cursor.mergeCharFormat(fmt)

    def get_selected_text(self) -> str:
        return self.text_edit.textCursor().selectedText().strip()
