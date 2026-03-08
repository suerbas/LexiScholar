"""
Event Handlers for Document Browser
Interaction logic for coding, memos, and editing.
"""

from PyQt6.QtWidgets import QMenu, QMessageBox, QColorDialog
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor
from ..styles import CONTEXT_MENU_STYLE
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class DocumentBrowserEventHandlers:
    """Interaction logic for the DocumentBrowser."""

    def _show_context_menu(self, position):
        click_cursor = self.text_edit.cursorForPosition(position)
        current_memo = self._get_memo_at_position(click_cursor.position())
        selection_cursor = self.text_edit.textCursor()
        
        menu = QMenu(self)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        
        if current_memo:
            edit_memo_action = menu.addAction("📝 Notu Düzenle")
            delete_memo_action = menu.addAction("🗑️ Notu Sil")
            menu.addSeparator()
            
        if selection_cursor.hasSelection():
            if self._pending_code:
                code_name = self._pending_code.get('name', 'Bilinmeyen')
                apply_code_action = menu.addAction(f"🏷️ Hızlı Kodla: '{code_name}'")
            else:
                apply_code_action = menu.addAction("🏷️ Hızlı Kodla (önce kod seçin)")
                apply_code_action.setEnabled(False)
            
            in_vivo_action = menu.addAction("✨ In-Vivo Kodla")
            menu.addSeparator()
            
            ai_menu = menu.addMenu("🤖 AI Asistanı")
            ai_summarize_action = ai_menu.addAction("📄 Seçimi Özetle")
            ai_suggest_action = ai_menu.addAction("💡 Kod Önerisi Al")
            menu.addSeparator()
            
            add_memo_action = menu.addAction("📝 Yeni Not Ekle")
            menu.addSeparator()
            remove_code_action = menu.addAction("❌ Seçimden Kodu Kaldır")
        
        action = menu.exec(self.text_edit.viewport().mapToGlobal(position))
        
        if current_memo:
            if action == edit_memo_action:
                self.memo_edit_requested.emit(current_memo['id'], current_memo['content'])
            elif action == delete_memo_action:
                self.memo_delete_requested.emit(current_memo['id'])
                
        if selection_cursor.hasSelection():
            if action == apply_code_action and self._pending_code:
                self._apply_pending_code()
            elif action == in_vivo_action:
                self._in_vivo_coding()
            elif 'ai_summarize_action' in locals() and action == ai_summarize_action:
                self._ai_summarize_selection()
            elif 'ai_suggest_action' in locals() and action == ai_suggest_action:
                self._ai_suggest_codes()
            elif action == add_memo_action:
                self._add_memo()
            elif action == remove_code_action:
                self._remove_code_from_selection()

    def _on_selection_changed(self):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            self.text_selected.emit(cursor.selectionStart(), cursor.selectionEnd(), cursor.selectedText())

    def _on_code_dropped(self, code_data: dict):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            self.code_assigned.emit(cursor.selectionStart(), cursor.selectionEnd(), cursor.selectedText(), code_data['id'])
            self._highlight_segment(cursor.selectionStart(), cursor.selectionEnd(), code_data.get('color', '#4F46E5'))

    def _on_mouse_moved(self, pos, global_pos):
        memo = self._get_memo_at_position(pos)
        self.text_edit.viewport().setCursor(Qt.CursorShape.PointingHandCursor if memo else Qt.CursorShape.IBeamCursor)
        current_memo_id = memo['id'] if memo else None
        if current_memo_id != self._last_tooltip_memo_id:
            self._last_tooltip_memo_id = current_memo_id
            from PyQt6.QtWidgets import QToolTip
            if memo: QToolTip.showText(global_pos, f"📝 Not: {memo['content']}", self.text_edit)
            else: QToolTip.hideText()

    def _toggle_edit_mode(self, checked):
        if checked:
            if self._coded_segments or self._memos:
                from ..common_ui import ask_confirmation
                if not ask_confirmation(self, "Dikkat", "Metni düzenlemek, mevcut kodların ve notların konumunu kaydırabilir. Devam etmek istiyor musunuz?"):
                    self.btn_edit.setChecked(False)
                    return
            self.text_edit.setReadOnly(False)
            self.btn_edit.setText("✏️")
            self.btn_save_text.show()
        else:
            self._save_content()
            self.text_edit.setReadOnly(True)
            self.btn_edit.setText("🔒")
            self.btn_save_text.hide()

    def _save_content(self):
        if not self._current_doc_id: return
        new_content = self.text_edit.toHtml()
        from database.document_dao import DocumentDAO
        dao = DocumentDAO(self._db_path)
        if dao.update_content(self._current_doc_id, new_content):
            self.document_content_changed.emit(self._current_doc_id, new_content)
            QTimer.singleShot(2000, lambda: self._update_header_info())
        else:
            show_error(self, "Hata", "Belge kaydedilirken bir hata oluştu.")

    def _choose_color(self):
        color = QColorDialog.getColor(Qt.GlobalColor.black, self, "Metin Rengi Seç")
        if color.isValid(): self.text_edit.setTextColor(color)

    def _handle_link_click(self, url):
        url_str = url.toString()
        if url_str.startswith("play://"):
            try: self.playback_requested.emit(float(url_str.replace("play://", "")))
            except ValueError: pass
