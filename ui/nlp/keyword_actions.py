"""
Keyword analysis actions.
"""

from .. import common_ui
from ..common_ui import show_warning

class KeywordActionsMixin:
    def _show_keyword_extraction(self):
        """Show keyword extraction analysis using YAKE (initially with defaults)."""
        self._run_keyword_analysis(settings={'ngram_size': 2, 'top_n': 30, 'dedup_lim': 0.9})

    def _run_keyword_analysis(self, settings: dict):
        """Run keyword analysis with specific settings."""
        texts = self._get_document_texts()
        if not texts:
            show_warning(self, "Uyarı", "Analiz için aktif belge bulunamadı.")
            return

        combined = ". ".join(t["text"].strip().rstrip(".") for t in texts) + "."
        doc_label = f"{len(texts)} belge" if len(texts) > 1 else texts[0]["title"]
        
        from ..modern_dialogs import ModernProgressDialog
        from ..worker_threads import NLPWorker
        
        self.nlp_progress = ModernProgressDialog("Anahtar kelimeler analiz ediliyor...", "İptal", 0, 0, self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
        options = {
            'combined_text': combined,
            'doc_label': doc_label,
            **settings
        }
        
        self.nlp_worker = NLPWorker('keywords', [], options=options)
        self.nlp_worker.progress.connect(self._update_nlp_progress)
        self.nlp_worker.finished.connect(self._on_keywords_finished)
        self.nlp_worker.error.connect(self._on_nlp_error)
        self.nlp_progress.canceled.connect(self.nlp_worker.cancel)
        
        self.nlp_worker.start()

    def _on_keywords_finished(self, results):
        """Callback when keyword analysis completes."""
        if hasattr(self, 'nlp_progress'):
            self.nlp_progress.close()
            
        try:
            data = results[0]
            keywords = data['keywords']
            doc_label = data['doc_label']
            settings = data.get('settings', {'ngram_size': 2, 'top_n': 30})
            
            if not keywords:
                common_ui.show_info(self, "Sonuç", "Anahtar kelime bulunamadı.")
                return
            
            from ..visualizations.text_analytics import generate_keywords_html
            file_path = generate_keywords_html(keywords, doc_label)
            
            from datetime import datetime
            subtitle = f"{doc_label} • {len(keywords)} anahtar kelime • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            title = "Anahtar Kelime Analizi"
            widget = self._open_visualization(title, file_path, subtitle=subtitle)
            
            if widget is None:
                for i in range(self.central_tabs.count()):
                    if self.central_tabs.tabText(i) == title:
                        container = self.central_tabs.widget(i)
                        widget = container.property("original_widget")
                        if not widget:
                            from ..common.browser_dialog import BrowserWidget
                            widget = container.findChild(BrowserWidget)
                        if widget and hasattr(widget, 'load_url'):
                            widget.load_url(file_path)
                        break
            
            if widget:
                try:
                    widget.keyword_settings_changed.disconnect()
                except TypeError:
                    pass
                
                widget.add_keyword_controls(settings)
                widget.keyword_settings_changed.connect(self._run_keyword_analysis)
                
            self.statusbar.showMessage("Anahtar kelime analizi tamamlandı", 5000)
            
        except Exception as e:
            common_ui.show_error(self, "Hata", f"Görselleştirme oluşturulamadı:\n{str(e)}")
        finally:
            if hasattr(self, 'nlp_worker') and self.nlp_worker:
                self.nlp_worker.deleteLater()
                self.nlp_worker = None
