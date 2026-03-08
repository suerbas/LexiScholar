"""
Highlight Management for Document Browser
Handles ExtraSelections for segments and memos.
"""

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont

class DocumentBrowserHighlightManager:
    """Methods for refreshing and managing text highlights."""

    def _sync_stripes(self):
        if self._coded_segments:
            self.coding_stripes.set_segments(self._coded_segments, self.text_edit)

    def _highlight_segment(self, start, end, color):
        self._refresh_highlights()
        self._sync_stripes()

    def _refresh_highlights(self):
        extra_selections = []
        doc_len = len(self.text_edit.toPlainText())

        # 1. Memo Highlights
        fmt_memo = QTextCharFormat()
        fmt_memo.setBackground(QColor("#FEF08A"))
        fmt_memo.setFontUnderline(True)
        fmt_memo.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        
        for memo in self._memos:
            start, end = memo.get('start_pos'), memo.get('end_pos')
            if start is None or end is None: continue
            cursor = self.text_edit.textCursor()
            cursor.setPosition(int(start))
            cursor.setPosition(min(int(end), doc_len), QTextCursor.MoveMode.KeepAnchor)
            sel = QTextEdit.ExtraSelection()
            sel.cursor, sel.format = cursor, fmt_memo
            extra_selections.append(sel)

        # 2. Active Segment Highlight
        if hasattr(self, '_active_segment_range') and self._active_segment_range:
            start, end = self._active_segment_range
            fmt_active = QTextCharFormat()
            fmt_active.setBackground(QColor("#FFD700"))
            fmt_active.setFontWeight(QFont.Weight.Bold)
            cursor = self.text_edit.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            sel = QTextEdit.ExtraSelection()
            sel.cursor, sel.format = cursor, fmt_active
            extra_selections.append(sel)

        # 3. Memos and Active Segment handled above.
        # General coded segments are only shown via coding stripes, 
        # avoiding "everything is highlighted" visual clutter.
        self.text_edit.setExtraSelections(extra_selections)

    def _highlight_all_segments(self):
        self._refresh_highlights()
        self.coding_stripes.set_segments(self._coded_segments, self.text_edit)

    def _highlight_memos(self):
        self._refresh_highlights()

    def highlight_active_segment(self, start, end):
        if end - start > 2000: return
        self._active_segment_range = (start, end)
        self._refresh_highlights()
        scroll_cursor = self.text_edit.textCursor()
        scroll_cursor.setPosition(start)
        self.text_edit.setTextCursor(scroll_cursor)
        self.text_edit.ensureCursorVisible()
