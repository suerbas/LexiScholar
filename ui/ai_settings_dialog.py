import sys
import os
import json
import logging
import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QWidget, QScrollArea,
    QPushButton, QComboBox, QFrame, QProgressBar, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
from .common.modern_dialog import ModernBaseDialog
from .styles import COLORS
from .common_ui import show_info, show_warning, show_error, ask_confirmation

logger = logging.getLogger(__name__)

# Model Mapping (OpenRouter ID -> Name)
MODEL_LIST = [
    {"name": "Gemini 2.5 Flash", "id": "google/gemini-2.0-flash-001"}, # Updated target
    {"name": "Claude 3.5 Sonnet", "id": "anthropic/claude-3.5-sonnet"},
    {"name": "Qwen 3 All-Round", "id": "qwen/qwen-plus"},
    {"name": "DeepSeek-V3", "id": "deepseek/deepseek-chat"},
    {"name": "Llama 4 Scout", "id": "meta-llama/llama-3.3-70b-instruct"},
    {"name": "Mixtral 8x22B Instruct", "id": "mistralai/mixtral-8x22b-instruct"}
]

class PriceFetcher(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
            if response.status_code == 200:
                data = response.json().get("data", [])
                prices = {}
                for model in data:
                    mid = model.get("id")
                    pricing = model.get("pricing", {})
                    # Costs are per token on OpenRouter, convert to per 1M or per 1K
                    # We'll store raw data: input/output per token
                    prices[mid] = {
                        "prompt": float(pricing.get("prompt", 0)),
                        "completion": float(pricing.get("completion", 0))
                    }
                self.finished.emit(prices)
            else:
                self.error.emit(f"API Hatası: {response.status_code}")
        except Exception as e:
            self.error.emit(str(e))

class AISettingsDialog(ModernBaseDialog):
    """Modernized AI Settings Dialog using ModernBaseDialog."""
    def __init__(self, parent=None):
        super().__init__(parent, min_width=520, min_height=480)
        self.settings = QSettings("LexiScholar", "Config")
        self.pricing_data = {}
        self._setup_ui()
        self._load_settings()
        self._fetch_prices()

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header (Blue gradient like Variable Manager)
        header = self.build_ribbon_header("🤖", "Yapay Zeka Ayarları")
        self.layout.addWidget(header)

        # 2. Main Scrollable Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(15)

        # Section Header
        section_header = QLabel("Yapay Zeka Yapılandırması")
        section_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #1E293B;")
        content_layout.addWidget(section_header)

        desc = QLabel("LexiScholar, yapay zeka işlemleri için OpenRouter API altyapısını kullanır.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #64748B; font-size: 12px;")
        content_layout.addWidget(desc)

        # API Key Section
        api_layout = QVBoxLayout()
        api_layout.setSpacing(6)
        api_label = QLabel("OpenRouter API Anahtarı")
        api_label.setStyleSheet("font-weight: 700; font-size: 12px; color: #475569;")
        api_layout.addWidget(api_label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-or-v1-...")
        self.api_key_input.setStyleSheet(f"padding: 6px 12px; border: 1.5px solid {COLORS['border']}; border-radius: 8px; min-height: 32px;")
        api_layout.addWidget(self.api_key_input)
        content_layout.addLayout(api_layout)

        # Model Selector Section
        model_layout = QVBoxLayout()
        model_layout.setSpacing(6)
        model_label = QLabel("Tercih Edilen Model")
        model_label.setStyleSheet("font-weight: 700; font-size: 12px; color: #475569;")
        model_layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px 12px;
                border: 1.5px solid {COLORS['border']};
                border-radius: 8px;
                background-color: white;
                color: #1E293B;
                font-size: 13px;
                min-height: 32px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border-left: 1px solid {COLORS['border']};
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748B;
                margin-right: 0px;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['primary_50']};
                selection-color: #4F46E5;
                outline: none;
                padding: 4px;
            }}
            QComboBox::item {{
                height: 32px;
                padding-left: 10px;
            }}
        """)
        for m in MODEL_LIST:
            self.model_combo.addItem(m["name"], m["id"])
        model_layout.addWidget(self.model_combo)

        self.pricing_info = QLabel("Fiyatlar yükleniyor...")
        self.pricing_info.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic; margin-top: 4px;")
        model_layout.addWidget(self.pricing_info)
        content_layout.addLayout(model_layout)

        # Info Box
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {COLORS['primary_50']}; border: 1px solid #E0E7FF; border-radius: 8px;")
        info_box = QVBoxLayout(info_frame)
        info_txt = QLabel("💡 Maliyet Tahmini:\n1 sayfa (~1000 kelime) özetleme için yapılan yaklaşık hesaplamadır. Seçilen modele göre bakiye harcaması değişebilir.")
        info_txt.setWordWrap(True)
        info_txt.setStyleSheet("color: #4338CA; font-size: 11px;")
        info_box.addWidget(info_txt)
        content_layout.addWidget(info_frame)
        
        scroll.setWidget(container)
        self.layout.addWidget(scroll)

        # 3. Footer Area
        btns = QHBoxLayout()
        btns.addStretch()
        
        help_btn = QPushButton("❓ Yardım")
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #4F46E5; font-weight: 700; border: none; font-size: 13px; }
            QPushButton:hover { text-decoration: underline; }
        """)
        help_btn.clicked.connect(self._open_guide)
        btns.addWidget(help_btn)
        
        btns.addStretch()
        
        cancel_btn = QPushButton("Vazgeç")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #475569; border: 1px solid #CBD5E1; 
                border-radius: 10px; padding: 10px 24px; font-weight: 700; font-size: 13px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        btns.addWidget(cancel_btn)
        
        save_btn = QPushButton("✅ Ayarları Kaydet")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5; color: white; border: none; border-radius: 10px;
                padding: 10px 32px; font-weight: 800; font-size: 14px;
            }
            QPushButton:hover { background: #4338CA; }
        """)
        btns.addWidget(save_btn)
        
        btns.addStretch()
        self.layout.addLayout(btns)

    def _load_settings(self):
        """Load settings from secure storage."""
        # Load API key from keyring (engine handles migration from QSettings)
        try:
            from llm_engine import OpenRouterEngine
            engine = OpenRouterEngine()
            if engine.api_key:
                self.api_key_input.setText(engine.api_key)
        except Exception as e:
            logger.warning(f"Failed to load API key: {e}")
        
        # Load model from QSettings (this is safe to store)
        model_id = self.settings.value("AI/MODEL_ID", "google/gemini-2.0-flash-001")
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == model_id:
                self.model_combo.setCurrentIndex(i)
                break

    def _save_settings(self):
        api_key = self.api_key_input.text().strip()
        model_id = self.model_combo.currentData()
        
        if not api_key:
            show_warning(self, "Uyarı", "Yapay zeka özelliklerini kullanabilmek için geçerli bir API anahtarı girmelisiniz.")
            # We still allow saving empty if they want to disable
        
        # Save API key using secure keyring storage
        try:
            from llm_engine import OpenRouterEngine
            engine = OpenRouterEngine()
            if engine.save_api_key(api_key):
                logger.debug("API key saved securely")
            else:
                show_warning(self, "Hata", "API anahtarı güvenli şekilde saklanamadı.")
                return
        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            show_warning(self, "Hata", f"API anahtarı kaydedilemedi: {e}")
            return
        
        # Save model preference to QSettings (safe)
        self.settings.setValue("AI/MODEL_ID", model_id)
        
        show_info(self, "Başarılı", "Yapay zeka ayarları güvenli şekilde kaydedildi. Model seçiminiz anında tüm sisteme entegre edildi.")
        self.accept()

    def _open_guide(self):
        # Using relative or absolute path for local doc
        path = os.path.join(os.getcwd(), "docs", "encyclopedia", "openrouter_guide.html")
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QDesktopServices.openUrl(QUrl("https://openrouter.ai/docs"))

    def _fetch_prices(self):
        self.fetcher = PriceFetcher()
        self.fetcher.finished.connect(self._on_prices_fetched)
        self.fetcher.error.connect(lambda msg: self.pricing_info.setText(f"Fiyatlar güncellenemedi: {msg}"))
        self.fetcher.start()

    def _on_prices_fetched(self, prices):
        self.pricing_data = prices
        self._update_model_labels()
        self.pricing_info.setText("Fiyatlar güncellendi. Metrik: 1 Sayfa (~1000 okuma + 250 yazma tokeni)")

    def _update_model_labels(self):
        for i in range(self.model_combo.count()):
            m_id = self.model_combo.itemData(i)
            m_name = MODEL_LIST[i]["name"] # Since items were added in same order
            
            p_data = self.pricing_data.get(m_id)
            if p_data:
                # Formula: (1000 * prompt_price) + (250 * completion_price)
                # OpenRouter pricing is per token in decimals, often like 0.0000001
                cost = (1000 * p_data["prompt"]) + (250 * p_data["completion"])
                if cost == 0:
                    label = f"{m_name} (Ücretsiz)"
                else:
                    label = f"{m_name} (~${cost:.5f} / Sayfa)"
                self.model_combo.setItemText(i, label)
            else:
                self.model_combo.setItemText(i, f"{m_name} (Fiyat bilinmiyor)")
