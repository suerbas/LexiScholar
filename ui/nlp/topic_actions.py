"""
Topic modeling actions.
"""

from .. import common_ui
from ..common_ui import show_warning, ask_confirmation, show_error
from .base_actions import _check_ram_before_nlp

class TopicActionsMixin:
    def _show_topic_modeling(self):
        """Show topic modeling across all documents with mode selection."""
        texts = self._get_document_texts()
        if len(texts) < 2:
            common_ui.show_warning(self, "Uyarı", "Konu modelleme için en az 2 aktif belge gerekli.")
            return
        
        from ..modern_dialogs import ModernComboboxDialog
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

        n_topics = min(5, max(2, len(texts) // 2))
        
        from ..modern_dialogs import ModernProgressDialog
        from ..worker_threads import NLPWorker
        
        self.nlp_progress = ModernProgressDialog(f"Konu modelleme hazırlanıyor ({mode_key})...", "İptal", 0, 0, self)
        self.nlp_progress.setWindowTitle("NLP Analiz")
        self.nlp_progress.show()
        
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
            
            from ..visualizations.semantic_analytics import (
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
            time_str = datetime.now().strftime('%d.%m.%Y %H:%M')
            subtitle = f"{topic_count} konu • {doc_count} belge ({mode})"
            if mode != 'local':
                 subtitle += f" • {model_info}"
            subtitle += f" • {time_str}"
            
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
