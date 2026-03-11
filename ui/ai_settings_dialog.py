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

from llm_engine import OpenRouterEngine

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
        super().__init__(parent, min_width=520, min_height=600)
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
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # Disable scroll bar as requested
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

        # --- Model Cards Section ---
        model_layout = QVBoxLayout()
        model_layout.setSpacing(12)
        model_label = QLabel("Kullanılan AI Modelleri")
        model_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #475569;")
        model_layout.addWidget(model_label)
        
        # Helper to create a model card
        def create_model_card(title, desc, badge_text, badge_color):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 1.5px solid {COLORS['border']};
                    border-radius: 10px;
                }}
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            
            # Left side texts
            text_layout = QVBoxLayout()
            text_layout.setSpacing(4)
            
            title_layout = QHBoxLayout()
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("font-weight: 800; font-size: 14px; color: #1E293B; border: none;")
            title_layout.addWidget(title_lbl)
            
            badge = QLabel(badge_text)
            badge.setStyleSheet(f"background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: bold; border: none;")
            badge.setFixedHeight(20)
            title_layout.addWidget(badge)
            title_layout.addStretch()
            
            text_layout.addLayout(title_layout)
            
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #64748B; font-size: 12px; border: none;")
            text_layout.addWidget(desc_lbl)
            
            card_layout.addLayout(text_layout)
            
            # Right side price label
            price_lbl = QLabel("Fiyat hesaplanıyor...")
            price_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            price_lbl.setStyleSheet("color: #4F46E5; font-size: 13px; font-weight: 700; border: none;")
            card_layout.addWidget(price_lbl)
            
            return card, price_lbl

        # Main Model Card
        engine = OpenRouterEngine()
        main_model_id = engine.DEFAULT_MODEL
        self.main_model_card, self.main_price_lbl = create_model_card(
            "Qwen 2.5 72B Instruct",
            "Tüm analiz görevleri için optimize edilmiş çok dilli ana model.",
            "ANA MODEL", "#4F46E5"
        )
        self.main_price_lbl.setProperty("model_id", main_model_id)
        model_layout.addWidget(self.main_model_card)

        # Judge Model Card
        judge_model_id = engine.JUDGE_MODEL
        self.judge_model_card, self.judge_price_lbl = create_model_card(
            "DeepSeek R1",
            "Güçlü analitik çıkarım ve hakemlik sentezi için kullanılan otorite modeli.",
            "HAKEM AI", "#8B5CF6"
        )
        self.judge_price_lbl.setProperty("model_id", judge_model_id)
        model_layout.addWidget(self.judge_model_card)

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

    def _save_settings(self):
        api_key = self.api_key_input.text().strip()
        
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
            
        show_info(self, "Başarılı", "Yapay zeka ayarları güvenli şekilde kaydedildi.")
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
        self.fetcher.error.connect(lambda msg: self.main_price_lbl.setText("Hata"))
        self.fetcher.start()

    def _on_prices_fetched(self, prices):
        self.pricing_data = prices
        self._update_model_labels()

    def _update_model_labels(self):
        for lbl in [self.main_price_lbl, self.judge_price_lbl]:
            m_id = lbl.property("model_id")
            p_data = self.pricing_data.get(m_id)
            if p_data:
                # Formula: (1000 * prompt_price) + (250 * completion_price)
                cost = (1000 * p_data["prompt"]) + (250 * p_data["completion"])
                if cost == 0:
                    lbl.setText("Ücretsiz")
                elif cost < 0.0001:
                    lbl.setText("< $0.0001 / sf")
                else:
                    lbl.setText(f"~${cost:.4f} / sf")
            else:
                lbl.setText("Fiyat ?")
