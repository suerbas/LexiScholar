"""
NLP Analysis Actions Mixin for LexiScholar Main Window.
Keyword extraction, sentiment analysis, topic modeling, NER, KWIC, and document portrait.
"""

from PyQt6.QtWidgets import QApplication, QMessageBox
from . import common_ui
from PyQt6.QtCore import Qt
import logging
from core.utils import natural_sort_key
from .common_ui import show_info, show_warning, show_error, ask_confirmation

logger = logging.getLogger(__name__)


def _get_available_ram_mb() -> int:
    """
    Windows'ta kullanılabilir fiziksel RAM'i MB cinsinden döndürür.
    ctypes kullanır (saf Windows, ek kurulum gerektirmez).
    Hata durumunda -1 döner.
    """
    try:
        import ctypes
        from ctypes import wintypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", wintypes.DWORD),
                ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.ullAvailPhys // (1024 * 1024)
    except Exception:
        return -1  # Tespit edilemedi


def _check_ram_before_nlp(parent, model_size_mb: int = 700) -> bool:
    """
    NLP analizi başlamadan önce kullanılabilir RAM'i kontrol eder.
    
    - Kullanılabilir RAM < model_size_mb * 1.5 ise uyarı gösterir.
    - Kullanıcı Devam Et derse True, İptal derse False döner.
    - RAM tespit edilemezse (Linux/Mac/hata) sessizce True döner.
    """
    avail_mb = _get_available_ram_mb()
    if avail_mb < 0:
        return True  # Tespit edilemedi, devam et

    threshold_mb = int(model_size_mb * 1.5)
    if avail_mb >= threshold_mb:
        return True  # Yeterli RAM var, uyarma

    return common_ui.ask_confirmation(
        parent,
        "Düşük Bellek Uyarısı",
        f"""⚠️ Bu analiz yaklaşık <b>{model_size_mb} MB</b> RAM gerektirir.<br><br>
Şu an kullanılabilir RAM: <b>{avail_mb:,} MB</b><br><br>
Devam ederseniz sistem yavaşlayabilir veya analiz başarsız olabilir.<br>
<i>Model analiz bittikten 10 dakika sonra otomatik olarak bellekten temizlenir.</i>"""
    )


class NLPActions:
    """Mixin class providing NLP analysis methods for MainWindow."""

    def _get_document_texts(self, active_only: bool = True):
        """Helper: Get document texts for NLP analysis."""
        from nlp_engine import clean_html
        
        documents = self.doc_dao.get_all()
        if active_only:
            documents = [d for d in documents if d.get('is_active', True)]
        
        texts = []
        for doc in documents:
            text = doc.get('extracted_text', '') or doc.get('content', '')
            if text:
                text = clean_html(text)
            if text and len(text.strip()) > 20:
                texts.append({
                    "doc_id": doc['id'],
                    "title": doc.get('title', 'Belge'),
                    "text": text
                })
        return texts

    def _show_keyword_extraction(self):
        """Show keyword extraction analysis using YAKE (initially with defaults)."""
        self._run_keyword_analysis(settings={'ngram_size': 2, 'top_n': 30, 'dedup_lim': 0.9})

    def _run_keyword_analysis(self, settings: dict):
        """Run keyword analysis with specific settings."""
        texts = self._get_document_texts()
        if not texts:
            show_warning(self, "Uyarı", "Analiz için aktif belge bulunamadı.")
            return

        # Prepare text for YAKE (concatenate with periods)
        # We do this here because it's fast enough usually
        combined = ". ".join(t["text"].strip().rstrip(".") for t in texts) + "."
        doc_label = f"{len(texts)} belge" if len(texts) > 1 else texts[0]["title"]
        
        # RAM Check? YAKE is memory efficient but for huge texts maybe check.
        # Skipping for now as YAKE is lighter than BERT.

        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
        self.nlp_progress = ModernProgressDialog("Anahtar kelimeler analiz ediliyor...", "İptal", 0, 0, self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
        options = {
            'combined_text': combined,
            'doc_label': doc_label,
            **settings
        }
        
        # Setup worker thread
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
            
            from .visualizations.text_analytics import generate_keywords_html
            file_path = generate_keywords_html(keywords, doc_label)
            
            from datetime import datetime
            subtitle = f"{doc_label} • {len(keywords)} anahtar kelime • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            # Open visualization
            title = "Anahtar Kelime Analizi"
            widget = self._open_visualization(title, file_path, subtitle=subtitle)
            
            # If widget is None, it means tab already exists. We need to find it to update controls/url
            if widget is None:
                # Find the existing widget
                for i in range(self.central_tabs.count()):
                    if self.central_tabs.tabText(i) == title:
                        container = self.central_tabs.widget(i)
                        # The tab contains a wrapper container, we need the original BrowserWidget
                        widget = container.property("original_widget")
                        
                        # Fallback if property is missing
                        if not widget:
                            from .common.browser_dialog import BrowserWidget
                            widget = container.findChild(BrowserWidget)
                            
                        # We also need to reload the page since we generated new HTML
                        if widget and hasattr(widget, 'load_url'):
                            widget.load_url(file_path)
                        break
            
            # Add controls and connect signal
            if widget:
                # Disconnect previous signals to avoid multiple calls
                try:
                    widget.keyword_settings_changed.disconnect()
                except TypeError:
                    pass # Not connected
                
                widget.add_keyword_controls(settings)
                widget.keyword_settings_changed.connect(self._run_keyword_analysis)
                
            self.statusbar.showMessage("Anahtar kelime analizi tamamlandı", 5000)
            
        except Exception as e:
            common_ui.show_error(self, "Hata", f"Görselleştirme oluşturulamadı:\n{str(e)}")
        finally:
            if hasattr(self, 'nlp_worker') and self.nlp_worker:
                self.nlp_worker.deleteLater()
                self.nlp_worker = None

    def _show_sentiment_analysis(self):
        """Show sentiment analysis for all documents using background thread."""
        texts = self._get_document_texts()
        if not texts:
            show_warning(self, "Uyarı", "Analiz için aktif belge bulunamadı.")
            return

        # RAM kontrolü — BERT modeli ~500-700 MB
        if not _check_ram_before_nlp(self, model_size_mb=600):
            return

        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
        self.nlp_progress = ModernProgressDialog("Duygu analizi hazırlanıyor...", "İptal", 0, len(texts), self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
        # Setup worker thread
        self.nlp_worker = NLPWorker('sentiment', texts)
        self.nlp_worker.progress.connect(self._update_nlp_progress)
        self.nlp_worker.finished.connect(self._on_sentiment_finished)
        self.nlp_worker.error.connect(self._on_nlp_error)
        self.nlp_progress.canceled.connect(self.nlp_worker.cancel)
        
        self.nlp_worker.start()

    def _update_nlp_progress(self, index, message):
        """Update progress dialog from worker thread."""
        if hasattr(self, 'nlp_progress'):
            self.nlp_progress.setValue(index + 1)
            self.nlp_progress.setLabelText(message)

    def _on_nlp_error(self, message):
        """Handle worker errors."""
        if hasattr(self, 'nlp_progress'):
            self.nlp_progress.close()
        common_ui.show_error(self, "NLP Hatası", f"Analiz sırasında bir hata oluştu:\n{message}")

    def _on_sentiment_finished(self, results):
        """Callback when sentiment analysis thread completes."""
        if hasattr(self, 'nlp_progress'):
            self.nlp_progress.close()
            
        try:
            from .visualizations.semantic_analytics import generate_sentiment_html
            file_path = generate_sentiment_html(results)
            
            title = "Duygu Analizi"
            doc_count = len(results)
            from datetime import datetime
            subtitle = f"{doc_count} belge analiz edildi • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            widget = self._open_visualization(title, file_path, subtitle=subtitle)
            
            if widget:
                # 1. Hide default toolbar (since we move controls to header)
                # Reverting: Keep toolbar visible but remove the manual header button injection below
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()
            
            self.statusbar.showMessage("Duygu analizi tamamlandı", 5000)
        except Exception as e:
            show_error(self, "Hata", f"Görselleştirme oluşturulamadı:\n{str(e)}")
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

    def _show_topic_modeling(self):
        """Show LDA topic modeling across all documents."""
        from PyQt6.QtWidgets import QApplication
        
        texts = self._get_document_texts()
        if len(texts) < 2:
            common_ui.show_warning(self, "Uyarı", "Konu modelleme için en az 2 aktif belge gerekli.")
            return
        
        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
        # Auto-adjust topic count
        n_topics = min(5, max(2, len(texts) // 2))
        
        self.nlp_progress = ModernProgressDialog("Konu modelleme başlatılıyor...", "İptal", 0, 0, self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
        # Setup worker thread
        self.nlp_worker = NLPWorker('topic_modeling', texts, options={'n_topics': n_topics})
        self.nlp_worker.progress.connect(self._update_nlp_progress)
        self.nlp_worker.finished.connect(self._on_topics_finished)
        self.nlp_worker.error.connect(self._on_nlp_error)
        self.nlp_progress.canceled.connect(self.nlp_worker.cancel)
        
        self.nlp_worker.start()

    def _on_topics_finished(self, results):
        """Callback when topic modeling thread completes."""
        if hasattr(self, 'nlp_progress'):
            self.nlp_progress.close()
            
        try:
            topic_data = results[0]
            from .visualizations.semantic_analytics import generate_topics_html
            
            file_path = generate_topics_html(topic_data)
            
            title = "Konu Modelleme"
            topic_count = len(topic_data.get("topics", []))
            doc_count = len(topic_data.get("doc_topics", []))
            from datetime import datetime
            subtitle = f"{topic_count} konu keşfedildi • {doc_count} belge • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            widget = self._open_visualization(title, file_path, subtitle=subtitle)
            
            if widget:
                # 1. Show default toolbar
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()
            
            self.statusbar.showMessage("Konu modelleme tamamlandı", 5000)
        except Exception as e:
            show_error(self, "Hata", f"Görselleştirme oluşturulamadı:\n{str(e)}")
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

    def _show_ner_analysis(self):
        """Show Named Entity Recognition using background thread."""
        texts = self._get_document_texts()
        if not texts:
            show_warning(self, "Uyarı", "Analiz için aktif belge bulunamadı.")
            return

        # RAM kontrolü — Multilingual NER ~600-700 MB
        if not _check_ram_before_nlp(self, model_size_mb=700):
            return

        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
        self.nlp_progress = ModernProgressDialog("Varlıklar tanımlanıyor...", "İptal", 0, len(texts), self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
        # Setup worker thread
        self.nlp_worker = NLPWorker('ner', texts)
        self.nlp_worker.progress.connect(self._update_nlp_progress)
        self.nlp_worker.finished.connect(self._on_ner_finished)
        self.nlp_worker.error.connect(self._on_nlp_error)
        self.nlp_progress.canceled.connect(self.nlp_worker.cancel)
        
        self.nlp_worker.start()

    def _on_ner_finished(self, results_list):
        """Callback when NER thread completes."""
        if hasattr(self, 'nlp_progress'):
            self.nlp_progress.close()
            
        try:
            ner_data = results_list[0]
            from .visualizations.semantic_analytics import generate_entities_html
            file_path = generate_entities_html(ner_data)
            
            title = "Varlık Tanıma (NER)"
            total_entities = sum(ner_data.get("summary", {}).values())
            doc_count = len(ner_data.get("documents", []))
            from datetime import datetime
            subtitle = f"{doc_count} belge • {total_entities} varlık • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            widget = self._open_visualization(title, file_path, subtitle=subtitle)
            
            if widget:
                # 1. Show default toolbar
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()
            
            self.statusbar.showMessage("Varlık tanıma tamamlandı", 5000)
        except Exception as e:
            show_error(self, "Hata", f"Görselleştirme oluşturulamadı:\n{str(e)}")
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

    def _show_kwic_dialog(self):
        """Show Key Word In Context (KWIC) analysis dialog."""
        from .modern_dialogs import ModernInputDialog
        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
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
            from .visualizations.text_analytics import generate_kwic_html
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
        from .modern_dialogs import ModernComboboxDialog
        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
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
