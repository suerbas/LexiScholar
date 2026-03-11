"""
Base NLP actions and helpers for RAM checking.
"""

from PyQt6.QtWidgets import QApplication, QMessageBox
import logging
from .. import common_ui

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


class NLPBaseMixin:
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
