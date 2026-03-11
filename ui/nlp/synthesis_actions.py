"""
Synthesis/Referee mode actions for comparing local vs AI models.
"""

from .. import common_ui
from ..common_ui import show_error, ask_confirmation

class SynthesisActionsMixin:
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

        from ..modern_dialogs import ModernProgressDialog
        from ..worker_threads import SynthesisWorker

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
        from ..modern_dialogs import ModernProgressDialog
        self.synth_progress = ModernProgressDialog("Hakem AI duygu sonuçlarını sentezliyor...", "İptal", 0, 0, self)
        self.synth_progress.show()

        from ..worker_threads import SynthesisWorker
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
        from ..modern_dialogs import ModernProgressDialog
        self.synth_progress = ModernProgressDialog("Hakem AI konuları sentezliyor...", "İptal", 0, 0, self)
        self.synth_progress.show()

        from ..worker_threads import SynthesisWorker
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
            from ..visualizations.semantic_analytics import (
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
