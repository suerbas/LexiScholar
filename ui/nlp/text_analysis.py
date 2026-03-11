"""
Text Analysis (KWIC, Document Portrait, etc.)
"""

from .. import common_ui
from ..common_ui import show_warning
from core.utils import natural_sort_key

class TextAnalysisMixin:
    def _show_kwic_dialog(self):
        """Show Key Word In Context (KWIC) analysis dialog."""
        from ..modern_dialogs import ModernInputDialog
        from ..modern_dialogs import ModernProgressDialog
        from ..worker_threads import NLPWorker
        
        texts = self._get_document_texts()
        if not texts:
            show_warning(self, "Uyarı", "Analiz için aktif belge bulunamadı.")
            return

        keyword, ok = ModernInputDialog.get_input(self, "KWIC Analizi", "Aranacak kelime:")
        if not ok or not keyword.strip():
            return
            
        keyword = keyword.strip()
        self.nlp_progress = ModernProgressDialog("KWIC analizi hazırlanıyor...", "İptal", 0, len(texts), self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        self.nlp_worker = NLPWorker('kwic', texts, options={"keyword": keyword})
        self.nlp_worker.progress.connect(self._update_nlp_progress)
        self.nlp_worker.finished.connect(self._on_kwic_finished)
        self.nlp_worker.error.connect(self._on_nlp_error)
        self.nlp_progress.canceled.connect(self.nlp_worker.cancel)
        self.nlp_worker.start()

    def _on_kwic_finished(self, results):
        if hasattr(self, 'nlp_progress'):
            self.nlp_progress.close()
        try:
            payload = results[0]
            keyword = payload["keyword"]
            all_results = payload["results"]
            doc_label = payload["doc_label"]
            if not all_results:
                common_ui.show_info(self, "Sonuç", f"'{keyword}' için sonuç bulunamadı.")
                return
            from ..visualizations.text_analytics import generate_kwic_html
            file_path = generate_kwic_html(all_results, keyword, doc_label)
            title = "KWIC Analizi"
            subtitle = f"'{keyword}' • {len(all_results)} sonuç • {doc_label}"
            widget = self._open_visualization(title, file_path, subtitle=subtitle)
            if widget:
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()
        except Exception as e:
            common_ui.show_error(self, "Hata", f"KWIC analizi başarısız:\n{str(e)}")
        finally:
            if hasattr(self, 'nlp_worker') and self.nlp_worker:
                try:
                    self.nlp_worker.progress.disconnect()
                    self.nlp_worker.finished.disconnect()
                    self.nlp_worker.error.disconnect()
                except TypeError:
                    pass
                self.nlp_worker.deleteLater()
                self.nlp_worker = None

    def _show_document_portrait(self):
        """Show Document Portrait visualization for the active document or prompt selection."""
        from ..modern_dialogs import ModernComboboxDialog
        from ..modern_dialogs import ModernProgressDialog
        from ..worker_threads import NLPWorker
        
        # Get active documents
        active_docs = self.doc_dao.get_all()
        active_docs = [d for d in active_docs if d.get('is_active', True)]
        
        # Sort documents by title naturally
        active_docs.sort(key=lambda x: natural_sort_key(x.get('title', '')))
        
        if not active_docs:
            common_ui.show_warning(self, "Uyarı", "Analiz için aktif belge bulunamadı.")
            return
            
        target_doc = None
        
        # If multiple documents are active, ask user to select one
        if len(active_docs) > 1:
            items = [d.get('title', f"Belge {d['id']}") for d in active_docs]
            # Use modern dialog instead of QInputDialog
            item, ok = ModernComboboxDialog.get_item(
                self, 
                "Belge Portresi", 
                "Portresi oluşturulacak belgeyi seçin:", 
                items
            )
            
            if ok and item:
                # Find the selected document object
                for d in active_docs:
                    if d.get('title', f"Belge {d['id']}") == item:
                        target_doc = d
                        break
            else:
                return # User cancelled
        else:
            # Only one document active, use it directly
            target_doc = active_docs[0]
            
        if not target_doc: return

        # Get text content length
        text = target_doc.get('extracted_text', '') or target_doc.get('content', '')
        if not text:
            # Try to load if missing
            full_doc = self.doc_dao.get_by_id(target_doc['id'])
            text = full_doc.get('extracted_text', '') or full_doc.get('content', '')
            
        doc_len = len(text)
        
        if doc_len < 10:
            common_ui.show_warning(self, "Uyarı", "Belge içeriği çok kısa veya boş.")
            return

        segments = self.segment_dao.get_by_document(target_doc['id'])
        clean_segments = []
        for s in segments:
            clean_segments.append({
                "start": s['start_pos'],
                "end": s['end_pos'],
                "color": s.get('code_color', '#CCCCCC')
            })
        self.nlp_progress = ModernProgressDialog("Belge portresi hazırlanıyor...", "İptal", 0, 0, self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        self.nlp_worker = NLPWorker(
            'document_portrait',
            [],
            options={
                "doc_len": doc_len,
                "segments": clean_segments,
                "title": target_doc.get('title', 'Belge')
            }
        )
        self.nlp_worker.progress.connect(self._update_nlp_progress)
        self.nlp_worker.finished.connect(self._on_document_portrait_finished)
        self.nlp_worker.error.connect(self._on_nlp_error)
        self.nlp_progress.canceled.connect(self.nlp_worker.cancel)
        self.nlp_worker.start()

    def _on_document_portrait_finished(self, results):
        if hasattr(self, 'nlp_progress'):
            self.nlp_progress.close()
        try:
            payload = results[0]
            from visualizations import generate_document_portrait_html
            file_path = generate_document_portrait_html(payload["title"], payload["grid_colors"])
            title = "Belge Portresi"
            subtitle = f"{payload['title']} • {payload['segments_count']} segment"
            widget = self._open_visualization(title, file_path, subtitle=subtitle)
            if widget:
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()
        except Exception as e:
            common_ui.show_error(self, "Hata", f"Belge portresi oluşturulamadı:\n{str(e)}")
        finally:
            if hasattr(self, 'nlp_worker') and self.nlp_worker:
                try:
                    self.nlp_worker.progress.disconnect()
                    self.nlp_worker.finished.disconnect()
                    self.nlp_worker.error.disconnect()
                except TypeError:
                    pass
                self.nlp_worker.deleteLater()
                self.nlp_worker = None
