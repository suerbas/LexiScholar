"""
Named Entity Recognition actions.
"""

from .. import common_ui
from ..common_ui import show_warning, ask_confirmation, show_error
from .base_actions import _check_ram_before_nlp

class EntityActionsMixin:
    def _show_ner_analysis(self):
        """Show Named Entity Recognition using background thread."""
        texts = self._get_document_texts()
        if not texts:
            show_warning(self, "Uyarı", "Analiz için aktif belge bulunamadı.")
            return

        from ..modern_dialogs import ModernComboboxDialog
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

        from ..modern_dialogs import ModernProgressDialog
        from ..worker_threads import NLPWorker
        
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
            from ..visualizations.semantic_analytics import generate_entities_html, generate_online_entities_html, generate_hybrid_entities_html

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
                    _ner_data_ref = ner_data
                    _model_ref = model_info
                    synth_btn.clicked.connect(lambda checked=False, d=_ner_data_ref, m=_model_ref: self._on_ner_synthesize_requested(d, m))
                    try:
                        widget.toolbar_layout.addWidget(synth_btn)
                    except AttributeError:
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
