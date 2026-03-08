"""
DocumentHighlighterMixin — LexiScholar Document Browser
Segment ve memo highlight mantığını yönetir.
DocumentBrowser tarafından miras alınır.
"""

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont


class DocumentHighlighterMixin:
    """
    Mixin: Belge içinde kodlanmış segment ve memo vurgulama işlemlerini yönetir.

    DocumentBrowser'ın ihtiyaç duyduğu attribute'lar (parent sınıfta bulunmalı):
        self.text_edit      — CodableTextEdit
        self._coded_segments — List[dict]
        self._memos          — List[dict]
        self._active_segment_range — Optional[Tuple[int, int]]
        self.coding_stripes  — CodingStripesWidget
    """

    # ─── Public API ──────────────────────────────────────────────

    def highlight_active_segment(self, start: int, end: int):
        """
        Bir segmenti 'aktif' olarak vurgular (metin seçimi yapmadan).
        Büyük segmentleri atlar (> 2000 karakter) performans için.
        """
        if end - start > 2000:
            return

        self._active_segment_range = (start, end)
        self._refresh_highlights()

        # İmleci konuma taşı ama metni seçme (Select All bug'ını önler)
        scroll_cursor = self.text_edit.textCursor()
        scroll_cursor.setPosition(start)
        self.text_edit.setTextCursor(scroll_cursor)
        self.text_edit.ensureCursorVisible()

    # ─── Segment Highlight ───────────────────────────────────────

    def _highlight_all_segments(self):
        """Var olan tüm kodlanmış segmentlere toplu renk biçimi uygular."""
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        try:
            for seg in self._coded_segments:
                cursor.setPosition(seg['start_pos'])
                cursor.setPosition(seg['end_pos'], QTextCursor.MoveMode.KeepAnchor)

                fmt = QTextCharFormat()
                bg = QColor(seg['code_color'])
                bg.setAlpha(50)
                fmt.setBackground(bg)
                cursor.mergeCharFormat(fmt)
        finally:
            cursor.endEditBlock()

        self.coding_stripes.set_segments(self._coded_segments, self.text_edit)

    # ─── Memo Highlight ──────────────────────────────────────────

    def _highlight_memos(self):
        """Memo vurgulamasını tetikler (tam yenileme)."""
        self._refresh_highlights()

    def _refresh_highlights(self):
        """
        Tüm ExtraSelection'ları (memo + aktif segment) sıfırdan hesaplar ve uygular.
        Bir türün diğerini ezmesini önler.
        """
        extra = []
        doc_len = len(self.text_edit.toPlainText())

        # 1. Memo vurguları
        fmt_memo = QTextCharFormat()
        fmt_memo.setBackground(QColor("#FEF08A"))
        fmt_memo.setFontUnderline(True)
        fmt_memo.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)

        for memo in self._memos:
            try:
                start = memo.get('start_pos')
                end = memo.get('end_pos')
                if start is None or end is None:
                    continue
                start, end = int(start), int(end)
                if start < 0 or start >= doc_len or end <= start:
                    continue
                end = min(end, doc_len)
                # Tüm belgeyi kaplayan sahte memoları atla
                if (end - start) > (doc_len * 0.95) and doc_len > 100:
                    continue

                cur = self.text_edit.textCursor()
                cur.setPosition(start)
                cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

                sel = QTextEdit.ExtraSelection()
                sel.cursor = cur
                sel.format = QTextCharFormat(fmt_memo)
                extra.append(sel)
            except (ValueError, TypeError):
                continue

        # 2. Aktif segment vurgusu (en üstte görünsün)
        if getattr(self, '_active_segment_range', None):
            start, end = self._active_segment_range
            fmt_active = QTextCharFormat()
            fmt_active.setBackground(QColor("#FFD700"))
            fmt_active.setFontWeight(QFont.Weight.Bold)

            cur = self.text_edit.textCursor()
            cur.setPosition(start)
            cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

            sel = QTextEdit.ExtraSelection()
            sel.cursor = cur
            sel.format = fmt_active
            extra.append(sel)

        self.text_edit.setExtraSelections(extra)

    # ─── Memo konumu bulma ───────────────────────────────────────

    def _get_memo_at_position(self, pos: int):
        """Verilen doküman pozisyonunda bulunan ilk memo'yu döner."""
        for memo in self._memos:
            start = memo.get('start_pos')
            end = memo.get('end_pos')
            if start is not None and end is not None:
                if start <= pos <= end:
                    return memo
        return None

    def _get_memo_at_cursor(self):
        """İmlecin bulunduğu konumdaki memo'yu döner."""
        cursor = self.text_edit.textCursor()
        return self._get_memo_at_position(cursor.position())
