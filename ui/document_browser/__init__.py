"""
Document Browser Sub-package for LexiScholar
Assembled from modular mixins and builders.
"""

from .base import DocumentBrowserBase
from .ui_builder import DocumentBrowserUIBuilder
from .event_handlers import DocumentBrowserEventHandlers
from .highlight_manager import DocumentBrowserHighlightManager

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer
from config import UI as _UI_CFG

class DocumentBrowser(DocumentBrowserBase, DocumentBrowserUIBuilder, 
                      DocumentBrowserEventHandlers, DocumentBrowserHighlightManager):
    """
    Main workspace for reading and coding documents.
    Modularized implementation.
    """

    def __init__(self, parent=None, db_path: str = "lexischolar.db"):
        super().__init__(parent, db_path)
        self._setup_ui()

    def set_document(self, doc_id: int, text: str, segments: list, memos: list = None, title: str = None):
        self._current_doc_id = doc_id
        self._current_doc_title = title
        self._coded_segments = segments
        self._memos = memos or []
        self._active_segment_range = None
        
        MAX_DISPLAY = _UI_CFG.MAX_DISPLAY_CHARS
        is_html = bool(text and (text.strip().startswith("<!DOCTYPE HTML") or text.strip().startswith("<html>")))

        if len(text) > MAX_DISPLAY:
            cut = text[:MAX_DISPLAY]
            last_break = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "), cut.rfind(".\n"))
            if last_break > MAX_DISPLAY * 0.8: cut = cut[: last_break + 1]
            warning_msg = f"\n\n[Uyarı: Belge çok büyük, performans için yalnızca ilk {len(cut):,} karakter gösteriliyor]"
            text = cut + (f"<br><br><b>{warning_msg}</b>" if is_html else warning_msg)

        if is_html: self.text_edit.setHtml(text)
        else: self.text_edit.setPlainText(text)
        
        para_count = len([p for p in self.text_edit.toPlainText().split('\n') if p.strip()])
        # display_title = title if title else f"BELGE: {doc_id}"
        # self.header.set_title(f"{display_title} ({para_count} Paragraf)")
        
        self._highlight_all_segments()
        self._highlight_memos()
        self.coding_stripes.set_segments(segments, self.text_edit)

    def set_pending_code(self, code_info: dict):
        self._pending_code = code_info
        if code_info:
            self.code_indicator.setText(f"🏷️ Aktif Kod: {code_info['name']} — Metin seçip sağ tıklayın")
            self.code_indicator.setStyleSheet(f"QLabel {{ background-color: {code_info['color']}15; color: {code_info['color']}; font-size: 12px; padding: 8px 16px; border-bottom: 2px solid {code_info['color']}; font-weight: 500; }}")
            self.code_indicator.show()
        else:
            self.code_indicator.hide()

    def set_active_code(self, code_id: int, color: str, name: str = ""):
        self._pending_code = {'id': code_id, 'name': name, 'color': color}
        if name: self.set_pending_code(self._pending_code)

    def _update_header_info(self):
        # Header removed
        return
        # if not self._current_doc_id: return
        # text = self.header.text()
        # for tag in (" (Kaydedildi)", " [DÜZENLENİYOR]", " - [AI Özetliyor... ⏳]", " - [AI Kod Öneriyor... ⏳]"):
        #     text = text.replace(tag, "")
        # self.header.setText(text.strip())

    def _get_memo_at_position(self, pos):
        for memo in self._memos:
            start, end = memo.get('start_pos'), memo.get('end_pos')
            if start is not None and end is not None and start <= pos <= end: return memo
        return None

    def _add_memo(self):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            self.memo_requested.emit(cursor.selectionStart(), cursor.selectionEnd(), cursor.selectedText())

    def _remove_code_from_selection(self):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            self.remove_code_requested.emit(cursor.selectionStart(), cursor.selectionEnd())

    def _in_vivo_coding(self):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            code_name = text.strip()[:50]
            if code_name: self.in_vivo_code_requested.emit(cursor.selectionStart(), cursor.selectionEnd(), text, code_name)

    def _apply_pending_code(self):
        if self._pending_code:
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                self.code_assigned.emit(cursor.selectionStart(), cursor.selectionEnd(), cursor.selectedText(), self._pending_code['id'])
                self._highlight_segment(cursor.selectionStart(), cursor.selectionEnd(), self._pending_code['color'])

    def _ai_summarize_selection(self): super()._ai_summarize_selection()
    def _ai_suggest_codes(self): super()._ai_suggest_codes()

    def set_detached(self, detached: bool):
        """Update toolbar icons and tooltips based on docking state."""
        if not hasattr(self, 'btn_detach'): return
        
        if detached:
            self.btn_detach.setText("↙") # SW Arrow (pointing back to dock)
            self.btn_detach.setToolTip("Paneli Yerleştir (Esc)")
            if hasattr(self, 'action_maximize'):
                self.action_maximize.setVisible(True)
            elif hasattr(self, 'btn_maximize'):
                self.btn_maximize.show()
        else:
            self.btn_detach.setText("↗") # NE Arrow (pointing away)
            self.btn_detach.setToolTip("Paneli Ayır")
            if hasattr(self, 'action_maximize'):
                self.action_maximize.setVisible(False)
            elif hasattr(self, 'btn_maximize'):
                self.btn_maximize.hide()
