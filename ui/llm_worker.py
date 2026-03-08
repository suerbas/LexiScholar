from PyQt6.QtCore import QThread, pyqtSignal
from llm_engine import OpenRouterEngine
import logging

logger = logging.getLogger(__name__)

class LLMWorker(QThread):
    """
    Asynchronous worker for making LLM API calls without blocking the UI.
    Emits signals upon success or failure.
    """
    finished_success = pyqtSignal(str) # Döndürülen metin (cevap)
    finished_error = pyqtSignal(str)   # Hata mesajı

    def __init__(self, prompt: str, system_prompt: str = "", model: str = "google/gemini-2.5-flash", temperature: float = 0.7, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.engine = OpenRouterEngine()

    def run(self):
        try:
            response = self.engine.generate_completion(
                prompt=self.prompt,
                system_prompt=self.system_prompt,
                model=self.model,
                temperature=self.temperature
            )
            self.finished_success.emit(response)
        except Exception as e:
            logger.error(f"LLMWorker error: {e}")
            self.finished_error.emit(str(e))

