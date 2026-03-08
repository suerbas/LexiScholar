"""
Code-related event handlers for LexiScholar.
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from typing import Any
from .commands import (
    CreateCodeCommand, DeleteCodeCommand, CreateSegmentCommand, 
    DeleteSegmentCommand, InVivoCodingCommand
)
from .common import WeightDialog

class CodeHandlersMixin:
    """Mixin for code management handlers."""
    
    def _on_code_selected(self, code_id: int):
        """Handle code selection."""
        if code_id is None:
            return
            
        code = None
        for c in self.code_dao.get_all():
            if c['id'] == code_id:
                code = c
                break
        
        if code:
            self.document_browser.set_active_code(code_id, code['color'], code['name'])
            if hasattr(self, 'retrieved_segments'):
                self.retrieved_segments.set_current_code_id(code_id)
            
    def _on_code_created(self, name: str, color: str, parent_id: Any, description: str = ""):
        """Handle new code creation."""
        try:
            final_parent_id = parent_id if parent_id and parent_id != 0 else None
            cmd = CreateCodeCommand(self.code_dao, name, color, description, final_parent_id)
            self.command_stack.push(cmd)
            
            codes = self.code_dao.get_all()
            self.code_tree.populate_codes(codes)
            self.set_dirty()
        except Exception as e:
            self.show_error("Kod Oluşturulamadı", "Veritabanına yeni kod eklenirken hata oluştu.", e)

    def _on_code_deleted(self, code_id: int):
        """Handle code deletion."""
        try:
            cmd = DeleteCodeCommand(self.code_dao, self.segment_dao, code_id)
            self.command_stack.push(cmd)
            self.set_dirty()
            
            codes = self.code_dao.get_all()
            self.code_tree.populate_codes(codes)
            self._refresh_after_delete(code_id)
            self.statusbar.showMessage("Kod ve ilgili segmentler silindi.")
        except Exception as e:
            self.show_error("Hata", "Kod silinirken bir hata oluştu.", e)

    def _on_code_assigned(self, start_pos: int, end_pos: int, text: str, code_id: int):
        """Handle code assignment to text segment."""
        try:
            doc_id = self.document_browser._current_doc_id
            if doc_id:
                coder_id = getattr(self, 'current_coder_id', 1)
                
                # Check for duplicates
                existing_segments = self.segment_dao.get_by_document(doc_id, coder_id=coder_id)
                for seg in existing_segments:
                    if seg['code_id'] == code_id and seg['start_pos'] == start_pos and seg['end_pos'] == end_pos:
                        self.show_error("Bilgi", "Bu metin parçası zaten aynı kodla kodlanmış durumda.")
                        return
                        
                # Get code name for dialog
                code_name = ""
                for c in self.code_dao.get_all():
                    if c['id'] == code_id:
                        code_name = c['name']
                        break
                
                # Show weight selection dialog
                weight_dialog = WeightDialog(code_name, text, self)
                weight_dialog.exec()
                weight = weight_dialog.get_weight()
                
                # Create segment
                cmd = CreateSegmentCommand(self.segment_dao, doc_id, code_id, start_pos, end_pos, text, weight, coder_id)
                self.command_stack.push(cmd)
                self.set_dirty()
                
                self.statusbar.showMessage(f"Kodlandı ({weight} ⭐): {text[:40]}...")
                
                # Refresh document view
                segments = self.segment_dao.get_by_document(doc_id, coder_id=coder_id)
                doc = self.doc_dao.get_by_id(doc_id)
                if doc:
                    memos = self.memo_dao.get_by_document(doc_id, coder_id=coder_id)
                    self.document_browser.set_document(doc_id, doc['extracted_text'] or "", segments, memos)
                
                # Refresh retrieved segments if this code is selected
                if self.retrieved_segments._current_code_id == code_id:
                    code = None
                    for c in self.code_dao.get_all():
                        if c['id'] == code_id:
                            code = c
                            break
                    if code:
                        segs = self.segment_dao.get_by_code(code_id)
                        self.retrieved_segments.set_code(code_id, code['name'], segs)
        except Exception as e:
            self.show_error("Kodlama Hatası", "Metin kodlanırken bir hata oluştu.", e)

    def _on_remove_code_requested(self, start_pos: int, end_pos: int):
        """Kaldırma işlemi seçili aralıktaki kodlamaları siler."""
        try:
            doc_id = self.document_browser._current_doc_id
            if not doc_id: return
                
            coder_id = getattr(self, 'current_coder_id', 1)
            segments = self.segment_dao.get_by_document(doc_id, coder_id=coder_id)
            
            to_delete = [seg for seg in segments if seg['start_pos'] < end_pos and seg['end_pos'] > start_pos]
                    
            if not to_delete:
                self.statusbar.showMessage("Bu aralıkta kodlama bulunamadı.")
                return
                
            for seg in to_delete:
                cmd = DeleteSegmentCommand(self.segment_dao, seg['id'])
                self.command_stack.push(cmd)
                
            self.set_dirty()
            
            # Refresh doc view
            refreshed_segments = self.segment_dao.get_by_document(doc_id, coder_id=coder_id)
            doc = self.doc_dao.get_by_id(doc_id)
            if doc:
                memos = self.memo_dao.get_by_document(doc_id, coder_id=coder_id)
                self.document_browser.set_document(doc_id, doc['extracted_text'] or "", refreshed_segments, memos)
                
            self.statusbar.showMessage(f"{len(to_delete)} kodlama kaldırıldı.")
            codes = self.code_dao.get_all()
            self.code_tree.populate_codes(codes)
            
        except Exception as e:
            self.show_error("Kaldırma Hatası", "Kod kaldırma işlemi sırasında bir hata oluştu.", e)
    
    def _on_in_vivo_code_requested(self, start_pos: int, end_pos: int, text: str, code_name: str):
        """Handle In-Vivo coding request."""
        try:
            existing_code = next((c for c in self.code_dao.get_all() if c['name'].lower() == code_name.lower()), None)
            
            if existing_code:
                code_id = existing_code['id']
                color = existing_code['color']
            else:
                import random
                from .styles import COLORS
                code_colors = [v for k, v in COLORS.items() if k.startswith('code_')] or list(COLORS.values())
                color = random.choice(code_colors)
                code_id = self.code_dao.create(code_name, color, "In-Vivo Kodlama ile oluşturuldu")
                
            doc_id = self.document_browser._current_doc_id
            if doc_id:
                coder_id = getattr(self, 'current_coder_id', 1)
                cmd = InVivoCodingCommand(self.segment_dao, self.code_dao, doc_id, code_name, color, start_pos, end_pos, text, coder_id)
                self.command_stack.push(cmd)
                
                codes = self.code_dao.get_all()
                self.code_tree.populate_codes(codes)
                self.set_dirty()
                self.statusbar.showMessage(f"In-Vivo Kodlandı: {code_name}")
                
                # Refresh document view
                segments = self.segment_dao.get_by_document(doc_id, coder_id=coder_id)
                doc = self.doc_dao.get_by_id(doc_id)
                if doc:
                    memos = self.memo_dao.get_by_document(doc_id, coder_id=coder_id)
                    self.document_browser.set_document(doc_id, doc['extracted_text'] or "", segments, memos)
        except Exception as e:
            self.show_error("In-Vivo Kodlama Hatası", "Hata oluştu.", e)

    def _on_code_activation_changed(self, code_id: int, is_active: bool):
        """Handle code activation toggle."""
        self._update_retrieved_segments()

    def _on_coded_segments_requested(self, code_id: int, code_name: str, code_color: str):
        """Show central tab with all segments of a code."""
        try:
            segments = self.segment_dao.get_by_code(code_id)
            if not segments:
                self.statusbar.showMessage(f"'{code_name}' için kodlanmış bölüm bulunamadı.")
                return

            tab_name = f"🧩 Kod Bölümleri: {code_name}"
            # Activate if already open
            for i in range(self.central_tabs.count()):
                if self.central_tabs.tabText(i) == tab_name:
                    self.central_tabs.setCurrentIndex(i)
                    return

            from .coded_segments.dialog import CodedSegmentsWidget
            widget = CodedSegmentsWidget(
                segments=segments,
                code_name=code_name,
                code_color=code_color,
                segment_dao=self.segment_dao,
                command_stack=self.command_stack,
                parent=self
            )
            widget.segment_navigate_requested.connect(self._on_segment_clicked)
            self.add_analysis_tab(widget, tab_name)
            
            self.statusbar.showMessage(f"'{code_name}' için {len(segments)} bölüm sekmeye eklendi.")
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.show_error("Kodlanmış Bölümler", f"Sekme açılırken hata oluştu:\n{str(e)}\n\n{tb}", e)
