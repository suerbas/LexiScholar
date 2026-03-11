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

        # 1. Mode Selection Dialog
        from .modern_dialogs import ModernComboboxDialog
        modes = [
            "Local (Standard) - BERT Modeli (Lokal/Gizli)",
            "Online (AI) - Yapay Zeka (Hızlı/Gelişmiş)",
            "Hybrid (Comparison) - BERT vs. Yapay Zeka"
        ]
        
        selected_mode_str, ok = ModernComboboxDialog.get_item(
            self, "Duygu Analizi Modu", 
            "Analiz yöntemini seçin:", 
            modes
        )
        if not ok: return
        
        mode_key = 'local'
        if "Online" in selected_mode_str: mode_key = 'online'
        elif "Hybrid" in selected_mode_str: mode_key = 'hybrid'

        # 2. Model recommendation for Online/Hybrid
        model = None
        if mode_key in ['online', 'hybrid']:
            # Check if API configured
            from llm_engine import OpenRouterEngine
            engine = OpenRouterEngine()
            if not engine.is_configured():
                if ask_confirmation(self, "API Anahtarı Eksik", 
                                "Online analiz için bir OpenRouter API anahtarı gereklidir. Ayarlara gitmek ister misiniz?"):
                    self._show_ai_settings()
                return

            model = engine.get_configured_model()
            self._current_model_name = engine.get_model_display_name()

        # RAM check for local parts
        if mode_key in ['local', 'hybrid']:
            if not _check_ram_before_nlp(self, model_size_mb=600):
                return

        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
        self.nlp_progress = ModernProgressDialog(f"Duygu analizi hazırlanıyor ({mode_key})...", "İptal", 0, len(texts), self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
        # Setup worker thread with options
        options = {'mode': mode_key, 'model': model}
        self.nlp_worker = NLPWorker('sentiment', texts, options=options)
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
            mode = results[0].get("mode", "local") if results else "local"
            
            from .visualizations.semantic_analytics import generate_sentiment_html, generate_hybrid_sentiment_html
            
            title = "Duygu Analizi"
            model_info = getattr(self, "_current_model_name", "AI")
            
            if mode == 'hybrid':
                file_path = generate_hybrid_sentiment_html(results, model_name=model_info)
                title = "Hibrit Duygu Analizi"
            else:
                file_path = generate_sentiment_html(results, model_name=model_info)
                if mode == 'online':
                    title = f"Online Duygu Analizi ({model_info})"
            
            doc_count = len(results)
            from datetime import datetime
            subtitle = f"{doc_count} belge analiz edildi ({mode}) • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            # Pass sentiment results directly to enable export functionality
            widget = self._open_visualization(
                title, 
                file_path, 
                subtitle=subtitle,
                sentiment_results=results if ("duygu" in title.lower() or "sentiment" in title.lower()) else None,
                model_type=model_info
            )
            
            if widget:
                # Hide default toolbar (since we move controls to header)
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()

                # --- Hibrit modda "Sentezle 🪄" butonu ekle ---
                if mode == 'hybrid':
                    from PyQt6.QtWidgets import QPushButton
                    synth_btn = QPushButton("Sentezle 🪄")
                    synth_btn.setToolTip("İki modelin sonuçlarını hakem yapay zeka ile tek listeye dönüştür")
                    synth_btn.setStyleSheet(
                        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                        "stop:0 #6C63FF, stop:1 #A78BFA); color: white; border: none; "
                        "border-radius: 6px; padding: 5px 14px; font-weight: bold; }"
                        "QPushButton:hover { background: #7C73FF; }"
                        "QPushButton:pressed { background: #5C53EF; }"
                    )
                    _data_ref = results
                    synth_btn.clicked.connect(lambda checked=False, d=_data_ref: self._on_sentiment_synthesize_requested(d))
                    try:
                        widget.toolbar_layout.addWidget(synth_btn)
                    except AttributeError:
                        try:
                            widget.layout().addWidget(synth_btn)
                        except Exception:
                            pass
            
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
        """Show topic modeling across all documents with mode selection."""
        from PyQt6.QtWidgets import QApplication
        
        texts = self._get_document_texts()
        if len(texts) < 2:
            common_ui.show_warning(self, "Uyarı", "Konu modelleme için en az 2 aktif belge gerekli.")
            return
        
        # 1. Mode Selection Dialog
        from .modern_dialogs import ModernComboboxDialog
        modes = [
            "Local (Standard) - LDA Modeli (Lokal/Gizli)",
            "Online (AI) - Yapay Zeka (Hızlı/Gelişmiş)",
            "Hybrid (Comparison) - LDA vs. Yapay Zeka"
        ]
        
        selected_mode_str, ok = ModernComboboxDialog.get_item(
            self, "Konu Modelleme Modu", 
            "Analiz yöntemini seçin:", 
            modes
        )
        if not ok: return
        
        mode_key = 'local'
        if "Online" in selected_mode_str: mode_key = 'online'
        elif "Hybrid" in selected_mode_str: mode_key = 'hybrid'

        # 2. Model recommendation for Online/Hybrid
        model = None
        if mode_key in ['online', 'hybrid']:
            # Check if API configured
            from llm_engine import OpenRouterEngine
            engine = OpenRouterEngine()
            if not engine.is_configured():
                if ask_confirmation(self, "API Anahtarı Eksik", 
                                "Online analiz için bir OpenRouter API anahtarı gereklidir. Ayarlara gitmek ister misiniz?"):
                    self._show_ai_settings()
                return

            model = engine.get_configured_model()
            self._current_model_name = engine.get_model_display_name()

        # Auto-adjust topic count
        n_topics = min(5, max(2, len(texts) // 2))
        
        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
        self.nlp_progress = ModernProgressDialog(f"Konu modelleme hazırlanıyor ({mode_key})...", "İptal", 0, 0, self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
        # Setup worker thread with options
        options = {'n_topics': n_topics, 'mode': mode_key, 'model': model}
        self.nlp_worker = NLPWorker('topic_modeling', texts, options=options)
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
            mode = topic_data.get("mode", "local")
            
            from .visualizations.semantic_analytics import (
                generate_topics_html, 
                generate_online_topics_html, 
                generate_hybrid_topics_html
            )
            
            model_info = getattr(self, "_current_model_name", "AI")
            
            if mode == 'hybrid':
                file_path = generate_hybrid_topics_html(topic_data, model_name=model_info)
                title = "Hibrit Konu Modelleme"
            elif mode == 'online':
                file_path = generate_online_topics_html(topic_data, model_name=model_info)
                title = f"Online Konu Modelleme ({model_info})"
            else:
                file_path = generate_topics_html(topic_data)
                title = "Konu Modelleme"
            
            topic_count = len(topic_data.get("topics", [])) if mode != 'hybrid' else len(topic_data.get("local", {}).get("topics", []))
            doc_count = len(topic_data.get("doc_topics", [])) if mode != 'hybrid' else len(topic_data.get("local", {}).get("doc_topics", []))
            from datetime import datetime
            subtitle = f"{topic_count} konu • {doc_count} belge ({mode}) • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            # Pass topic results for export functionality
            widget = self._open_visualization(
                title,
                file_path,
                subtitle=subtitle,
                topic_results=topic_data if ("konu" in title.lower() or "topic" in title.lower()) else None,
                model_type=model_info
            )
            
            if widget:
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()

                # --- Hibrit modda "Sentezle 🪄" butonu ekle ---
                if mode == 'hybrid':
                    from PyQt6.QtWidgets import QPushButton
                    synth_btn = QPushButton("Sentezle 🪄")
                    synth_btn.setToolTip("İki modelin sonuçlarını hakem yapay zeka ile tek listeye dönüştür")
                    synth_btn.setStyleSheet(
                        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                        "stop:0 #6C63FF, stop:1 #A78BFA); color: white; border: none; "
                        "border-radius: 6px; padding: 5px 14px; font-weight: bold; }"
                        "QPushButton:hover { background: #7C73FF; }"
                        "QPushButton:pressed { background: #5C53EF; }"
                    )
                    _data_ref = topic_data
                    synth_btn.clicked.connect(lambda checked=False, d=_data_ref: self._on_topic_synthesize_requested(d))
                    try:
                        widget.toolbar_layout.addWidget(synth_btn)
                    except AttributeError:
                        try:
                            widget.layout().addWidget(synth_btn)
                        except Exception:
                            pass
            
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

        from .modern_dialogs import ModernComboboxDialog
        modes = [
            "Local (Standard) - NER Modeli (Lokal/Gizli)",
            "Online (AI) - Yapay Zeka (Hızlı/Gelişmiş)",
            "Hybrid (Comparison) - NER vs. Yapay Zeka"
        ]

        selected_mode_str, ok = ModernComboboxDialog.get_item(
            self, "Varlık Tanıma Modu",
            "Analiz yöntemini seçin:",
            modes
        )
        if not ok: return

        mode_key = 'local'
        if "Online" in selected_mode_str: mode_key = 'online'
        elif "Hybrid" in selected_mode_str: mode_key = 'hybrid'

        model = None
        if mode_key in ['online', 'hybrid']:
            from llm_engine import OpenRouterEngine
            engine = OpenRouterEngine()
            if not engine.is_configured():
                if ask_confirmation(self, "API Anahtarı Eksik",
                                "Online analiz için bir OpenRouter API anahtarı gereklidir. Ayarlara gitmek ister misiniz?"):
                    self._show_ai_settings()
                return

            model = engine.get_configured_model()
            self._current_model_name = engine.get_model_display_name()

        if mode_key in ['local', 'hybrid']:
            if not _check_ram_before_nlp(self, model_size_mb=700):
                return

        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import NLPWorker
        
        self.nlp_progress = ModernProgressDialog(f"Varlıklar tanımlanıyor ({mode_key})...", "İptal", 0, len(texts), self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
        options = {'mode': mode_key, 'model': model}
        self.nlp_worker = NLPWorker('ner', texts, options=options)
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
            mode = ner_data.get("mode", "local")
            model_info = getattr(self, "_current_model_name", "AI")
            from .visualizations.semantic_analytics import generate_entities_html, generate_online_entities_html, generate_hybrid_entities_html

            if mode == 'hybrid':
                file_path = generate_hybrid_entities_html(ner_data, model_name=model_info)
                title = "Hibrit Varlık Tanıma (NER)"
            elif mode == 'online':
                file_path = generate_online_entities_html(ner_data, model_name=model_info)
                title = f"Online Varlık Tanıma ({model_info})"
            else:
                file_path = generate_entities_html(ner_data)
                title = "Varlık Tanıma (NER)"
            
            total_entities = sum(ner_data.get("summary", {}).values())
            doc_count = len(ner_data.get("documents", []))
            from datetime import datetime
            subtitle = f"{doc_count} belge • {total_entities} varlık ({mode}) • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            widget = self._open_visualization(title, file_path, subtitle=subtitle, ner_results=ner_data, model_type=model_info)
            
            if widget:
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()

                # --- Hibrit modda "Sentezle 🪄" butonu ekle ---
                if mode == 'hybrid':
                    from PyQt6.QtWidgets import QPushButton
                    synth_btn = QPushButton("Sentezle 🪄")
                    synth_btn.setToolTip("İki modelin sonuçlarını hakem yapay zeka ile tek listeye dönüştür")
                    synth_btn.setStyleSheet(
                        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                        "stop:0 #6C63FF, stop:1 #A78BFA); color: white; border: none; "
                        "border-radius: 6px; padding: 5px 14px; font-weight: bold; }"
                        "QPushButton:hover { background: #7C73FF; }"
                        "QPushButton:pressed { background: #5C53EF; }"
                    )
                    # Capture ner_data and model_info for the closure
                    _ner_data_ref = ner_data
                    _model_ref = model_info
                    synth_btn.clicked.connect(lambda checked=False, d=_ner_data_ref, m=_model_ref: self._on_ner_synthesize_requested(d, m))
                    # Try adding to the existing toolbar inside the widget
                    try:
                        widget.toolbar_layout.addWidget(synth_btn)
                    except AttributeError:
                        # Fallback: if there's no toolbar_layout, just try addWidget
                        try:
                            widget.layout().addWidget(synth_btn)
                        except Exception:
                            pass
            
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

    def _on_ner_synthesize_requested(self, hybrid_ner_data: dict, original_model: str):
        """Launches the AI-judge synthesis for hybrid NER results."""
        from llm_engine import OpenRouterEngine
        engine = OpenRouterEngine()
        if not engine.is_configured():
            if ask_confirmation(self, "API Anahtarı Eksik",
                             "Sentez için bir OpenRouter API anahtarı gereklidir. Ayarlara gitmek ister misiniz?"):
                self._show_ai_settings()
            return

        judge_model = engine.get_judge_model()


        from .modern_dialogs import ModernProgressDialog
        from .worker_threads import SynthesisWorker

        # Show progress dialog
        self.synth_progress = ModernProgressDialog(
            "Hakem AI sonuçları sentezliyor, lütfen bekleyin...", "İptal", 0, 0, self
        )
        self.synth_progress.setWindowTitle("Akıllı Sentez")
        self.synth_progress.show()

        self.synthesis_worker = SynthesisWorker(
            data=hybrid_ner_data,
            task_type="ner",
            judge_model=judge_model,
            original_model=original_model
        )
        self.synthesis_worker.finished.connect(self._on_synthesis_finished)
        self.synthesis_worker.error.connect(self._on_synthesis_error)
        self.synth_progress.canceled.connect(self.synthesis_worker.cancel)
        self.synthesis_worker.start()

    def _on_sentiment_synthesize_requested(self, hybrid_sentiment_data: list):
        """Launches the AI-judge synthesis for hybrid Sentiment results."""
        from llm_engine import OpenRouterEngine
        engine = OpenRouterEngine()
        if not engine.is_configured():
            if ask_confirmation(self, "API Anahtarı Eksik", 
                             "Sentez için bir OpenRouter API anahtarı gereklidir. Ayarlara gitmek ister misiniz?"):
                self._show_ai_settings()
            return
        
        judge_model = engine.get_judge_model()
        from .modern_dialogs import ModernProgressDialog
        self.synth_progress = ModernProgressDialog("Hakem AI duygu sonuçlarını sentezliyor...", "İptal", 0, 0, self)
        self.synth_progress.show()

        from .worker_threads import SynthesisWorker
        self.synthesis_worker = SynthesisWorker(data=hybrid_sentiment_data, task_type="sentiment", judge_model=judge_model)
        self.synthesis_worker.finished.connect(self._on_synthesis_finished)
        self.synthesis_worker.error.connect(self._on_synthesis_error)
        self.synth_progress.canceled.connect(self.synthesis_worker.cancel)
        self.synthesis_worker.start()

    def _on_topic_synthesize_requested(self, hybrid_topic_data: dict):
        """Launches the AI-judge synthesis for hybrid Topic modeling results."""
        from llm_engine import OpenRouterEngine
        engine = OpenRouterEngine()
        if not engine.is_configured():
            if ask_confirmation(self, "API Anahtarı Eksik", 
                             "Sentez için bir OpenRouter API anahtarı gereklidir. Ayarlara gitmek ister misiniz?"):
                self._show_ai_settings()
            return
        
        judge_model = engine.get_judge_model()
        from .modern_dialogs import ModernProgressDialog
        self.synth_progress = ModernProgressDialog("Hakem AI konuları sentezliyor...", "İptal", 0, 0, self)
        self.synth_progress.show()

        from .worker_threads import SynthesisWorker
        self.synthesis_worker = SynthesisWorker(data=hybrid_topic_data, task_type="topics", judge_model=judge_model)
        self.synthesis_worker.finished.connect(self._on_synthesis_finished)
        self.synthesis_worker.error.connect(self._on_synthesis_error)
        self.synth_progress.canceled.connect(self.synthesis_worker.cancel)
        self.synthesis_worker.start()

    def _on_synthesis_finished(self, synthesized_data: object):
        """Callback when AI-judge synthesis completes (for any task type)."""
        if hasattr(self, 'synth_progress'):
            self.synth_progress.close()

        try:
            from datetime import datetime
            from .visualizations.semantic_analytics import (
                generate_online_entities_html, 
                generate_sentiment_html,
                generate_topics_html
            )

            if isinstance(synthesized_data, list):
                # Sentiment Synthesis Result
                file_path = generate_sentiment_html(synthesized_data, model_name="Sentez (Hakem)")
                title = "Sentezlenmiş Duygu Analizi ✨"
                subtitle = f"{len(synthesized_data)} belge (sentezlenmiş) • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                widget = self._open_visualization(title, file_path, subtitle=subtitle, sentiment_results=synthesized_data)
            elif isinstance(synthesized_data, dict) and "topics" in synthesized_data:
                # Topic Synthesis Result
                file_path = generate_topics_html(synthesized_data)
                title = "Sentezlenmiş Konu Modelleme ✨"
                tc = len(synthesized_data.get("topics", []))
                dc = len(synthesized_data.get("doc_topics", []))
                subtitle = f"{tc} konu • {dc} belge • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                widget = self._open_visualization(title, file_path, subtitle=subtitle, topic_results=synthesized_data)
            else:
                # Assume NER Synthesis Result
                model_name = synthesized_data.get("model_name", "Hakem AI")
                file_path = generate_online_entities_html(synthesized_data, model_name=f"Sentez ({model_name})")
                total_entities = sum(synthesized_data.get("summary", {}).values())
                doc_count = len(synthesized_data.get("documents", []))
                subtitle = f"{doc_count} belge • {total_entities} varlık (sentezlenmiş) • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                title = "Sentezlenmiş Varlık Tanıma ✨"
                widget = self._open_visualization(title, file_path, subtitle=subtitle, ner_results=synthesized_data)

            if widget:
                widget.set_toolbar_visible(True)
                widget.add_simple_controls()

            self.statusbar.showMessage("Akıllı sentez tamamlandı ✨", 7000)
        except Exception as e:
            show_error(self, "Sentez Hatası", f"Görselleştirme oluşturulamadı:\n{str(e)}")
        finally:
            if hasattr(self, 'synthesis_worker') and self.synthesis_worker:
                self.synthesis_worker.deleteLater()
                self.synthesis_worker = None


    def _on_synthesis_error(self, error_msg: str):
        """Callback when AI-judge synthesis fails."""
        if hasattr(self, 'synth_progress'):
            self.synth_progress.close()
        show_error(self, "Sentez Hatası", f"Akıllı sentez sırasında hata oluştu:\n{error_msg}")
        if hasattr(self, 'synthesis_worker') and self.synthesis_worker:
            self.synthesis_worker.deleteLater()
            self.synthesis_worker = None

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
