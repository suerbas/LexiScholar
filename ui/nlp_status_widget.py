"""
NLPStatusWidget — LexiScholar Status Bar
Anlık NLP model durumu VE kullanılabilir RAM göstergesi.
Status bar'a eklenir; kullanıcıdan hiçbir eylem gerektirmez.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QFrame
from PyQt6.QtCore import Qt, QTimer


# Model isimlerini kısalt
_MODEL_LABELS = {
    "sentiment-analysis:tr": "Duygu-TR",
    "sentiment-analysis:en": "Duygu-EN",
    "ner:tr":                 "NER-TR",
    "ner:en":                 "NER-EN",
    "embedding:multilingual": "BGE-M3",
}

_STYLE_ACTIVE = (
    "background-color: #d1fae5; color: #065f46; "
    "border: 1px solid #6ee7b7; border-radius: 4px; "
    "padding: 1px 6px; font-size: 9px; font-weight: 600;"
)
_STYLE_IDLE = (
    "background-color: #f1f5f9; color: #64748b; "
    "border: 1px solid #cbd5e1; border-radius: 4px; "
    "padding: 1px 6px; font-size: 9px;"
)

# RAM göstergesi renk eşikleri
_RAM_STYLE_OK      = "color: #16a34a; font-size: 9px; font-weight: 600;"   # Yeşil  ≥ 2 GB
_RAM_STYLE_WARN    = "color: #d97706; font-size: 9px; font-weight: 600;"   # Turuncu 1-2 GB
_RAM_STYLE_DANGER  = "color: #dc2626; font-size: 9px; font-weight: 600;"   # Kırmızı < 1 GB
_RAM_STYLE_UNKNOWN = "color: #94a3b8; font-size: 9px;"                     # Gri — ölçülemedi


def _read_available_ram_mb() -> int:
    """ctypes ile kullanılabilir fiziksel RAM'i MB olarak döner. Hata: -1."""
    try:
        import ctypes
        from ctypes import wintypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength",                wintypes.DWORD),
                ("dwMemoryLoad",            wintypes.DWORD),
                ("ullTotalPhys",            ctypes.c_ulonglong),
                ("ullAvailPhys",            ctypes.c_ulonglong),
                ("ullTotalPageFile",        ctypes.c_ulonglong),
                ("ullAvailPageFile",        ctypes.c_ulonglong),
                ("ullTotalVirtual",         ctypes.c_ulonglong),
                ("ullAvailVirtual",         ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return int(stat.ullAvailPhys // (1024 * 1024))
    except Exception:
        return -1


class NLPStatusWidget(QWidget):
    """
    Status bar için NLP model + RAM göstergesi.

    Sol taraf  : Yüklü NLP modelleri (yeşil etiket / gri çizgi)
    Sağ taraf  : Kullanılabilir RAM (yeşil/turuncu/kırmızı)

    Otomatik güncelleme:
      - Modeller: 30 saniyede bir (TTL eviction'ı yansıtır)
      - RAM     :  5 saniyede bir (gerçek zamanlıya yakın)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            from nlp import get_nlp_memory_info, unload_all_models
            self._get_nlp_memory_info = get_nlp_memory_info
            self._unload_all_models = unload_all_models
        except ImportError:
            self._get_nlp_memory_info = None
            self._unload_all_models = None
        self._setup_ui()

        # Model durumu — 2 sn
        self._model_timer = QTimer(self)
        self._model_timer.setInterval(2_000)
        self._model_timer.timeout.connect(self._refresh_models)
        self._model_timer.start()

        # RAM — 5 sn
        self._ram_timer = QTimer(self)
        self._ram_timer.setInterval(5_000)
        self._ram_timer.timeout.connect(self._refresh_ram)
        self._ram_timer.start()

        self.refresh()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 6, 0)
        layout.setSpacing(4)

        # ── NLP Model Bölümü ────────────────────────────────────────────────
        nlp_prefix = QLabel("NLP:")
        nlp_prefix.setStyleSheet("color: #94a3b8; font-size: 9px; font-weight: 600;")
        layout.addWidget(nlp_prefix)

        self._model_container = QHBoxLayout()
        self._model_container.setContentsMargins(0, 0, 0, 0)
        self._model_container.setSpacing(3)
        layout.addLayout(self._model_container)

        self._btn_unload = QToolButton()
        self._btn_unload.setText("✕")
        self._btn_unload.setToolTip("Yüklü AI modellerini bellekten temizle")
        self._btn_unload.setStyleSheet(
            "QToolButton { background: transparent; color: #94a3b8; "
            "border: none; font-size: 9px; padding: 1px 2px; }"
            "QToolButton:hover { color: #dc2626; }"
        )
        self._btn_unload.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_unload.clicked.connect(self._unload_models)
        self._btn_unload.setVisible(False)
        layout.addWidget(self._btn_unload)

        # ── Ayırıcı ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #e2e8f0;")
        layout.addWidget(sep)

        # ── RAM Bölümü ───────────────────────────────────────────────────────
        ram_prefix = QLabel("RAM:")
        ram_prefix.setStyleSheet("color: #94a3b8; font-size: 9px; font-weight: 600;")
        layout.addWidget(ram_prefix)

        self._ram_label = QLabel("…")
        self._ram_label.setStyleSheet(_RAM_STYLE_UNKNOWN)
        self._ram_label.setToolTip("Kullanılabilir fiziksel RAM")
        layout.addWidget(self._ram_label)

        self.setToolTip(
            "NLP: Aktif modeller — 10 dk kullanılmazsa otomatik temizlenir.\n"
            "RAM: Anlık kullanılabilir bellek (5 sn'de bir güncellenir)."
        )

    # ── Güncelleme ──────────────────────────────────────────────────────────

    def refresh(self):
        """Her iki bölümü de günceller."""
        self._refresh_models()
        self._refresh_ram()

    def _refresh_models(self):
        if not hasattr(self, "_get_nlp_memory_info") or self._get_nlp_memory_info is None:
            loaded = []
        else:
            try:
                info = self._get_nlp_memory_info()
                loaded = info.get("loaded", [])
            except Exception:
                loaded = []

        while self._model_container.count():
            item = self._model_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if loaded:
            for key in loaded:
                human = _MODEL_LABELS.get(key, key)
                lbl = QLabel(human)
                lbl.setStyleSheet(_STYLE_ACTIVE)
                self._model_container.addWidget(lbl)
            self._btn_unload.setVisible(True)
        else:
            lbl = QLabel("—")
            lbl.setStyleSheet(_STYLE_IDLE)
            self._model_container.addWidget(lbl)
            self._btn_unload.setVisible(False)

    def _refresh_ram(self):
        avail = _read_available_ram_mb()
        if avail < 0:
            self._ram_label.setText("?")
            self._ram_label.setStyleSheet(_RAM_STYLE_UNKNOWN)
            return

        if avail >= 2048:
            style = _RAM_STYLE_OK
        elif avail >= 1024:
            style = _RAM_STYLE_WARN
        else:
            style = _RAM_STYLE_DANGER

        if avail >= 1024:
            text = f"{avail / 1024:.1f} GB"
        else:
            text = f"{avail} MB"

        self._ram_label.setText(text)
        self._ram_label.setStyleSheet(style)
        self._ram_label.setToolTip(f"Kullanılabilir RAM: {avail:,} MB")

    # ── Boşalt ──────────────────────────────────────────────────────────────

    def _unload_models(self):
        try:
            from nlp import unload_all_models
            unload_all_models()
        except Exception:
            pass
        self.refresh()
