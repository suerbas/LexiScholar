"""
LexiScholar — Central Configuration File
All magic numbers and adjustable parameters are defined here.
Usage: from config import AppConfig, NLPConfig, UIConfig
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

@dataclass(frozen=True)
class AppConfig:
    """General application parameters."""

    # Project Management
    MAX_RECENT_PROJECTS: int = 10          # Limit for recent projects list
    BACKUP_SNAPSHOT_LIMIT: int = 5         # Maximum number of snapshots to keep
    AUTO_BACKUP_INTERVAL_MS: int = 300_000 # 5 min — auto-backup interval (ms)

    # Database
    DB_FILENAME: str = "lexischolar.db"
    DB_BUSY_TIMEOUT_MS: int = 5_000        # SQLite busy-timeout


@dataclass(frozen=True)
class UIConfig:
    """UI and document display parameters."""

    # Document Viewer
    MAX_DISPLAY_CHARS: int = 500_000       # Character limit for large documents
    SEGMENT_HIGHLIGHT_MAX: int = 2_000     # Max characters for segment highlighting
    LINE_NUMBER_WIDTH_PX: int = 45         # Width of the line number area

    # NLP Loading — Threshold shown to user
    NLP_LOADING_THRESHOLD_MS: int = 500    # Show spinner if operation takes longer than this

    # Tabs and Panel Defaults
    DEFAULT_FONT_SIZE_PT: int = 11
    MIN_FONT_SIZE_PT: int = 8
    MAX_FONT_SIZE_PT: int = 24

    # Style Save Debounce
    STYLE_SAVE_DEBOUNCE_MS: int = 1_000


@dataclass(frozen=True)
class NLPConfig:
    """NLP model and analysis parameters."""

    # Language Detection
    LANG_DETECT_MIN_CHARS: int = 10        # Minimum characters required for detection
    LANG_DETECT_FALLBACK: str = "tr"       # Default fallback language

    # YAKE / Keyword Extraction
    KEYWORD_MAX_NGRAM_SIZE: int = 2        # Max 2-gram keywords
    KEYWORD_DEDUP_THRESHOLD: float = 0.9   # YAKE deduplication threshold
    KEYWORD_TOP_N: int = 20                # Number of keywords to return

    # Topic Modeling (LDA)
    TOPIC_MIN_DOCS: int = 2                # Minimum docs required for topic modeling
    TOPIC_MIN_CHARS: int = 50              # Minimum characters for a valid doc
    TOPIC_MAX_FEATURES: int = 2_000        # CountVectorizer max_features
    TOPIC_MAX_ITER: int = 20               # LDA iterations
    TOPIC_RANDOM_STATE: int = 42

    # Sentiment / NER Models
    SENTIMENT_CACHE_SIZE: int = 3          # Max models to keep in cache
    NER_CACHE_SIZE: int = 3

    # KWIC (Key Word in Context)
    KWIC_DEFAULT_CONTEXT_WINDOW: int = 10  # Left/Right word window

    # Document Portrait
    PORTRAIT_GRID_SIZE: int = 10           # 10x10 = 100 cell grid


# ============================================================================
# DEFAULT INSTANCES (Singleton-like access)
# ============================================================================

APP   = AppConfig()
UI    = UIConfig()
NLP   = NLPConfig()
