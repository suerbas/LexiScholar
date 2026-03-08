"""
Data management and general event handlers for LexiScholar.
"""

from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt6.QtCore import Qt
from typing import Any
import logging

from .survey_import import SurveyImportWizard
from .worker_threads import SurveyImportWorker
from processors.excel_survey_processor import parse_survey_data
from .commands import DeleteSegmentCommand, BatchDeleteSegmentsCommand
from .common_ui import show_info, show_warning, show_error, ask_confirmation

logger = logging.getLogger(__name__)

class DataHandlersMixin:
    """Mixin for data management and general handlers."""
    
    def show_error(self, title: str, message: str, exception: Exception = None):
        """Show a standardized error message to the user."""
        detail = f"\n\nDetay: {str(exception)}" if exception else ""
        show_error(self, title, f"{message}{detail}")
        if exception:
            logging.getLogger(__name__).error(f"{title}: {message}", exc_info=exception)

    def _show_survey_import_dialog(self):
        """Open the Survey Import Dialog."""
        dialog = SurveyImportWizard(self)
        dialog.import_requested.connect(self._on_survey_import_requested)
        dialog.exec()

    def _on_survey_import_requested(self, file_path: str, sheet_name: str, config: dict, survey_name: str, include_headers: bool = False):
        """Handle execution of survey import."""
        try:
            self.statusbar.showMessage("Anket verileri okunuyor...")
            rows = parse_survey_data(file_path, sheet_name, config)
            if not rows:
                show_warning(self, "Bilgi", "İçe aktarılacak geçerli satır bulunamadı.")
                return
            
            target_folder_id = self._get_active_folder_id()
            self.survey_worker = SurveyImportWorker(self.db_path, rows, folder_id=target_folder_id, survey_name=survey_name, include_headers=include_headers)
            self.survey_worker.progress.connect(lambda i, msg: self.statusbar.showMessage(msg))
            self.survey_worker.finished.connect(self._on_survey_import_finished)
            self.survey_worker.error.connect(lambda err: self.show_error("Anket İçe Aktarma Hatası", "Hata oluştu.", Exception(err)))
            self.survey_worker.start()
        except Exception as e:
            self.show_error("Anket Okuma Hatası", "Excel verisi işlenirken hata oluştu.", e)

    def _on_survey_import_finished(self, doc_count: int):
        """Callback when survey import completes."""
        self.statusbar.showMessage(f"Anket içe aktarma tamamlandı ({doc_count} katılımcı).")
        doc_list = self.doc_dao.get_all()
        folder_list = self.folder_dao.get_all()
        self.document_tree.populate_tree(doc_list, folder_list)
        code_list = self.code_dao.get_all()
        self.code_tree.populate_codes(code_list)
        self.set_dirty()
        show_info(self, "Başarılı", f"Anket içe aktarıldı! ({doc_count} belge)")

    def _on_quick_code_requested(self, code_id: int, code_name: str, code_color: str):
        """Open Survey Quick Code dialog."""
        from .survey_quick_code import SurveyQuickCodeDialog
        segments = self.segment_dao.get_by_code(code_id)
        if not segments:
            self.show_error("Bilgi", f"'{code_name}' için segment bulunamadı.")
            return
        
        all_codes = self.code_dao.get_all() if self.code_dao else []
        # Store reference to prevent garbage collection on non-modal show
        self._survey_dialog = SurveyQuickCodeDialog(
            segments=segments, code_name=code_name, code_id=code_id,
            code_color=code_color, all_codes=all_codes,
            segment_dao=self.segment_dao, parent=self
        )
        self._survey_dialog.sub_code_created.connect(self._on_code_created)
        self._survey_dialog.show()

    def _on_ai_action_requested(self, code_id: int, code_name: str, action: str):
        """Handle AI action requests."""
        from llm_engine import OpenRouterEngine
        segments = self.segment_dao.get_by_code(code_id)
        if not segments:
            self.show_error("Bilgi", f"'{code_name}' için bölüm bulunamadı.")
            return
            
        texts = [f"- {s.get('segment_text', '').strip()}" for s in segments if s.get('segment_text', '').strip()]
        if not texts:
            self.show_error("Bilgi", "Metin bulunamadı.")
            return
            
        combined_text = "\n".join(texts)[:12000]
        prompts = {
            "summarize": ("You are an expert qualitative data analyst. Summarize...", f"Summarize themes for '{code_name}':\n\n{combined_text}", f"AI Özet: {code_name}"),
            "suggest_subcodes": ("You are an expert qualitative data analyst. Suggest...", f"Suggest sub-codes for '{code_name}':\n\n{combined_text}", f"AI Alt Kod Önerileri: {code_name}"),
            "find_outliers": ("You are a critical-thinking expert data analyst. Find...", f"Find outliers for '{code_name}':\n\n{combined_text}", f"AI Aykırı Görüş Analizi: {code_name}")
        }
        
        if action not in prompts: return
        sys_prompt, prompt, title = prompts[action]
            
        # Use LLMWorker to prevent UI freezing
        from .llm_worker import LLMWorker
        
        progress = QProgressDialog("AI analiz ediyor...", "İptal", 0, 0, self)
        progress.setWindowTitle("AI İşlemi")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        self._llm_worker = LLMWorker(prompt, sys_prompt, model="google/gemini-2.5-flash", parent=self)
        
        def on_success(response):
            progress.close()
            from .common_ui import show_scrollable_info
            show_scrollable_info(self, title, response)
            
        def on_error(err_msg):
            progress.close()
            self.show_error("AI Hatası", "AI analizi sırasında hata oluştu.", Exception(err_msg))
            
        self._llm_worker.finished_success.connect(on_success)
        self._llm_worker.finished_error.connect(on_error)
        
        # Connect cancel button
        progress.canceled.connect(lambda: self._llm_worker.terminate())
        
        self._llm_worker.start()

    def _on_segment_clicked(self, doc_id: int, segment_id: int):
        """Navigate to document location."""
        if self.document_browser._current_doc_id != doc_id:
            self._on_document_selected(doc_id)
        
        segs = self.segment_dao.get_by_document(doc_id)
        for s in segs:
            if s['id'] == segment_id:
                self.document_browser.highlight_active_segment(s['start_pos'], s['end_pos'])
                break
    
    def _on_segment_delete_requested(self, segment_id: int):
        """Handle segment deletion."""
        segment = self.segment_dao.get_by_id(segment_id)
        if not segment: return

        code_id = segment['code_id']
        text = segment['segment_text']
        duplicates = [s for s in self.segment_dao.get_by_code(code_id) if s['segment_text'] == text]
        
        if len(duplicates) > 1:
            from .common_ui import ask_confirmation
            if ask_confirmation(self, "Silme Seçenekleri", f"Toplam {len(duplicates)} benzer segment bulundu.\n\nHepsini silmek istiyor musunuz?"):
                self.command_stack.push(BatchDeleteSegmentsCommand(self.segment_dao, [s['id'] for s in duplicates]))
                self.set_dirty()
                self._refresh_after_delete(code_id)
                return

        if ask_confirmation(self, "Sil", "Emin misiniz?") :
            self.command_stack.push(DeleteSegmentCommand(self.segment_dao, segment_id))
            self.set_dirty()
            self._refresh_after_delete(code_id)

    def _refresh_after_delete(self, code_id: int):
        """Helper to refresh UI."""
        self._update_retrieved_segments()
        if self.document_browser._current_doc_id:
            self._on_document_selected(self.document_browser._current_doc_id)
    
    def _reload_all_data(self):
        """Reload all data after project load."""
        try:
            if hasattr(self, 'code_tree'): self.code_tree.code_dao = self.code_dao
            if hasattr(self, 'document_tree'):
                if hasattr(self.document_tree, 'set_daos'): self.document_tree.set_daos(self.doc_dao, self.folder_dao)
                else:
                    self.document_tree.doc_dao = self.doc_dao
                    self.document_tree.folder_dao = self.folder_dao
            if hasattr(self, 'document_browser'): self.document_browser._db_path = self.db_path
            
            if hasattr(self, 'code_tree') and self.code_dao: self.code_tree.populate_codes(self.code_dao.get_all())
            if hasattr(self, 'document_tree') and self.doc_dao and self.folder_dao:
                self.document_tree.populate_tree(self.doc_dao.get_all(), self.folder_dao.get_all())
        except Exception as e:
            self.statusbar.showMessage(f"Yükleme hatası: {e}")
        
    def _update_retrieved_segments(self):
        """Update retrieved segments panel."""
        active_docs = self.doc_dao.get_active_ids()
        active_codes = self.code_dao.get_active_ids()
        
        if not active_docs or not active_codes:
            self.retrieved_segments.clear()
            return
            
        segs = self.segment_dao.get_by_active_criteria(active_docs, active_codes)
        self.retrieved_segments.set_segments(segs)

    def _on_query_requested(self):
        """Show Advanced Query Builder dialog."""
        from .query_builder import QueryBuilderDialog
        dialog = QueryBuilderDialog(self.code_dao.get_all(), self)
        if dialog.exec():
            p = dialog.get_query_parameters()
            segs = self.segment_dao.get_by_boolean_query(p['and_ids'], p['or_ids'], p['not_ids'], p['doc_scope'])
            self.retrieved_segments.set_segments(segs)
            self.statusbar.showMessage(f"Sorgu tamamlandı: {len(segs)} sonuç.")
