import os
import logging
import base64
from typing import Optional, Dict, Any

from openai import OpenAI
from dotenv import load_dotenv
from PyQt6.QtCore import QSettings

logger = logging.getLogger(__name__)

# Try to import keyring for secure persistence
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    logger.warning("keyring library not available; secure API key persistence disabled")
    KEYRING_AVAILABLE = False

class OpenRouterEngine:
    """
    A wrapper around standard OpenAI client customized for OpenRouter.
    Reads configuration from secure keyring storage with legacy migration support.
    """
    def __init__(self):
        # Load environment variables (if not already loaded)
        load_dotenv()
        
        # 1. Try keyring first (most secure)
        self.api_key = None
        if KEYRING_AVAILABLE:
            try:
                self.api_key = keyring.get_password("LexiScholar", "openrouter_api_key")
                if self.api_key:
                    logger.debug("API key loaded from keyring")
            except Exception as e:
                logger.warning(f"Failed to load API key from keyring: {e}")
        
        # 2. Fallback to QSettings (legacy migration only)
        if not self.api_key:
            try:
                settings = QSettings("LexiScholar", "Config")
                stored_key = settings.value("AI/API_KEY", "")
                if stored_key and stored_key.startswith("base64:"):
                    try:
                        migrated_key = base64.b64decode(stored_key[7:]).decode('utf-8')
                        if KEYRING_AVAILABLE:
                            self.api_key = migrated_key
                            keyring.set_password("LexiScholar", "openrouter_api_key", self.api_key)
                            settings.setValue("AI/API_KEY", "")
                            logger.debug("API key migrated from QSettings to keyring")
                        else:
                            logger.warning("QSettings içinde legacy API key bulundu ancak keyring yok; güvenlik nedeniyle yüklenmedi.")
                    except Exception as e:
                        logger.error(f"Failed to decode base64 API key: {e}")
                elif stored_key:
                    if KEYRING_AVAILABLE:
                        self.api_key = stored_key
                        keyring.set_password("LexiScholar", "openrouter_api_key", self.api_key)
                        settings.setValue("AI/API_KEY", "")
                        logger.debug("Plain API key migrated from QSettings to keyring")
                    else:
                        logger.warning("QSettings içinde düz API key bulundu ancak keyring yok; güvenlik nedeniyle yüklenmedi.")
            except Exception as e:
                logger.warning(f"Failed to load API key from QSettings: {e}")
        
        # 3. Fallback to .env / OS env
        if not self.api_key:
            self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
            if self.api_key:
                logger.debug("API key loaded from environment variables")
            
        if not self.api_key:
            logger.warning("OpenRouter API anahtarı bulunamadı (keyring, QSettings veya OS Env).")
            
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = None
        
        self._initialize_client()

    def _initialize_client(self):
        if self.api_key:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=30.0
            )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def save_api_key(self, api_key: str) -> bool:
        """Save API key securely using keyring with fallback."""
        if KEYRING_AVAILABLE:
            try:
                keyring.set_password("LexiScholar", "openrouter_api_key", api_key)
                # Clear QSettings if it exists
                settings = QSettings("LexiScholar", "Config")
                settings.setValue("AI/API_KEY", "")
                logger.debug("API key saved to keyring")
                return True
            except Exception as e:
                logger.warning(f"Failed to save API key to keyring: {e}")

        logger.error("API key güvenli olarak saklanamadı: keyring kullanılamıyor.")
        return False

    def get_configured_model(self) -> str:
        """Returns the user-selected model from QSettings or a default."""
        settings = QSettings("LexiScholar", "Config")
        return settings.value("AI/MODEL_ID", "google/gemini-2.0-flash-001")

    def generate_completion(self, prompt: str, system_prompt: str = "", model: str = None, temperature: float = 0.7) -> str:
        """
        Generates a chat completion.
        Uses configured model if none is provided.
        """
        if not self.is_configured():
            raise ValueError("OpenRouter API anahtarı ayarlanmamış. Lütfen 'Yapay Zeka Ayarları' menüsünden anahtarınızı girin.")
            
        if model is None:
            model = self.get_configured_model()
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                # Extra headers (OpenRouter recommendation)
                extra_headers={
                    "HTTP-Referer": "https://lexischolar.app", 
                    "X-Title": "LexiScholar QDA",
                },
                model=model,
                messages=messages,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenRouter API Error: {e}")
            raise RuntimeError(f"API Hatası: {str(e)}")

    def chat_completion(self, messages: list, model: str = None, temperature: float = 0.7) -> str:
        """
        Send a full OpenAI-style messages list and return the assistant reply.
        Use this for multi-turn conversations where you need to preserve history.
        """
        if not self.is_configured():
            raise ValueError("OpenRouter API anahtarı ayarlanmamış. Lütfen 'Yapay Zeka Ayarları' menüsünden anahtarınızı girin.")

        if model is None:
            model = self.get_configured_model()

        try:
            response = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://lexischolar.app",
                    "X-Title": "LexiScholar QDA",
                },
                model=model,
                messages=messages,
                temperature=temperature,
            )
            if not response.choices:
                logger.warning("Empty response from LLM API")
                return "Üzgünüm, API'den yanıt alınamadı."
                
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenRouter chat_completion Error: {e}")
            raise RuntimeError(f"API Hatası: {str(e)}")
