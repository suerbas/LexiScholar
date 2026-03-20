"""
LexiScholar — Merkezi Versiyon Bilgisi
Tüm modüller için tek kaynak (Single Source of Truth).
"""

# Uygulama sürüm numarası (UI, log ve PyInstaller için)
APP_VERSION = "3.8.0"
APP_NAME = "LexiScholar"
APP_DISPLAY_VERSION = "v3.8 Beta"

# Proje dosyası şema versiyonu (project.json içinde saklanır,
# gelecekteki migration'lar bu değere göre çalışır)
PROJECT_SCHEMA_VERSION = "1.1"

# Minimum desteklenen proje şeması (daha eski projeleri yine de aç)
MIN_SUPPORTED_SCHEMA = "1.0"

__all__ = [
    "APP_VERSION",
    "APP_NAME",
    "APP_DISPLAY_VERSION",
    "PROJECT_SCHEMA_VERSION",
    "MIN_SUPPORTED_SCHEMA",
]
