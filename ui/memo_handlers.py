"""
Memo-related event handlers for LexiScholar.
"""

from PyQt6.QtWidgets import QMessageBox
from .common import MemoDialog
from .commands import CreateMemoCommand, UpdateMemoCommand, DeleteMemoCommand
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class MemoHandlersMixin:
    """Mixin for memo management handlers."""
    
    def _on_memo_requested(self, start_pos: int, end_pos: int, text: str):
        """Handle memo creation request."""
        dialog = MemoDialog(self, segment_text=text)
        if dialog.exec():
            content = dialog.get_memo_content()
            if content:
                doc_id = self.document_browser._current_doc_id
                coder_id = getattr(self, 'current_coder_id', 1)
                
                cmd = CreateMemoCommand(self.memo_dao, content, doc_id=doc_id, start=start_pos, end=end_pos, coder_id=coder_id)
                self.command_stack.push(cmd)
                
                self.set_dirty()
                self.statusbar.showMessage("Not eklendi")
                self._refresh_doc_browser(doc_id)
    
    def _on_memo_edit_requested(self, memo_id: int, current_content: str):
        """Handle memo edit request."""
        dialog = MemoDialog(self, existing_content=current_content)
        if dialog.exec():
            new_content = dialog.get_memo_content()
            if new_content and new_content != current_content:
                cmd = UpdateMemoCommand(self.memo_dao, memo_id, new_content)
                self.command_stack.push(cmd)
                self.set_dirty()
                self.statusbar.showMessage("Not güncellendi")
                doc_id = self.document_browser._current_doc_id
                if doc_id: self._refresh_doc_browser(doc_id)

    def _on_document_memo_requested(self, doc_id: int, title: str):
        """Handle request to add/edit a general document memo."""
        memo = self.memo_dao.get_general_document_memo(doc_id)
        existing_content = memo['content'] if memo else ""
        
        dialog = MemoDialog(self, existing_content=existing_content)
        dialog.setWindowTitle(f"📄 Belge Notu: {title}")
        
        if dialog.exec():
            new_content = dialog.get_memo_content()
            if memo:
                if new_content != existing_content:
                    cmd = UpdateMemoCommand(self.memo_dao, memo['id'], new_content)
                    self.command_stack.push(cmd)
                    self.set_dirty()
                    self.statusbar.showMessage(f"Belge notu güncellendi: {title}")
            elif new_content:
                cmd = CreateMemoCommand(self.memo_dao, new_content, title=f"Belge: {title}", doc_id=doc_id)
                self.command_stack.push(cmd)
                self.set_dirty()
                self.statusbar.showMessage(f"Belge notu oluşturuldu: {title}")

    def _on_code_memo_requested(self, code_id: int, name: str):
        """Handle request to add/edit a code memo."""
        memo = self.memo_dao.get_by_code(code_id)
        existing_content = memo['content'] if memo else ""
        
        dialog = MemoDialog(self, existing_content=existing_content)
        dialog.setWindowTitle(f"🏷️ Kod Notu: {name}")
        
        if dialog.exec():
            new_content = dialog.get_memo_content()
            if memo:
                if new_content != existing_content:
                    cmd = UpdateMemoCommand(self.memo_dao, memo['id'], new_content)
                    self.command_stack.push(cmd)
                    self.set_dirty()
                    self.statusbar.showMessage(f"Kod notu güncellendi: {name}")
            elif new_content:
                cmd = CreateMemoCommand(self.memo_dao, new_content, title=f"Kod: {name}", code_id=code_id)
                self.command_stack.push(cmd)
                self.set_dirty()
                self.statusbar.showMessage(f"Kod notu oluşturuldu: {name}")

    def _on_memo_delete_requested(self, memo_id: int):
        """Handle memo deletion request."""
        reply = ask_confirmation(
            self, "Notu Sil", "Bu notu silmek istediğinizden emin misiniz?"
        )
        if reply :
            cmd = DeleteMemoCommand(self.memo_dao, memo_id)
            self.command_stack.push(cmd)
            self.set_dirty()
            self.statusbar.showMessage("Not silindi")
            doc_id = self.document_browser._current_doc_id
            if doc_id: self._refresh_doc_browser(doc_id)

    def _refresh_doc_browser(self, doc_id):
        """Helper to refresh document browser."""
        coder_id = getattr(self, 'current_coder_id', 1)
        segs = self.segment_dao.get_by_document(doc_id, coder_id=coder_id)
        doc = self.doc_dao.get_by_id(doc_id)
        memos = self.memo_dao.get_by_document(doc_id, coder_id=coder_id)
        self.document_browser.set_document(doc_id, doc['extracted_text'] or "", segs, memos)
