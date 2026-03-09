"""
pytest Shared Fixtures — LexiScholar Test Altyapısı

Tüm testlerde kullanılacak ortak fixture'lar:
  - tmp_db_path:   her test için geçici, izole SQLite DB
  - initialized_db: şeması hazır DB
  - dao_*:         hazır DAO örnekleri
"""

import os
import sys

# Force offscreen platform ONLY on CI to allow local GUI testing.
if os.environ.get("GITHUB_ACTIONS"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# WebEngine/Chromium flags for headless/CI environments
os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --disable-gpu --disable-software-rasterizer"

import pytest
from pathlib import Path

# Proje kökünü Python path'e ekle (tests/ dışından import için)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure WebEngine is imported early to avoid "Contexts must be set" errors
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    pass # Handle cases where WebEngine is not installed

from database.connection import init_db, get_db_connection
from database.document_dao import DocumentDAO
from database.code_dao import CodeDAO
from database.segment_dao import CodedSegmentDAO
from database.memo_dao import MemoDAO
from database.folder_dao import FolderDAO
from PyQt6.QtWidgets import QApplication


@pytest.fixture
def tmp_db_path(tmp_path) -> str:
    """Her test için izole, geçici bir SQLite veritabanı yolu döner."""
    return str(tmp_path / "test.db")


@pytest.fixture
def initialized_db(tmp_db_path) -> str:
    """Şeması başlatılmış geçici DB döner."""
    init_db(tmp_db_path)
    return tmp_db_path


@pytest.fixture
def dao_document(initialized_db) -> DocumentDAO:
    return DocumentDAO(initialized_db)


@pytest.fixture
def dao_code(initialized_db) -> CodeDAO:
    return CodeDAO(initialized_db)


@pytest.fixture
def dao_segment(initialized_db) -> CodedSegmentDAO:
    return CodedSegmentDAO(initialized_db)


@pytest.fixture
def dao_memo(initialized_db) -> MemoDAO:
    return MemoDAO(initialized_db)


@pytest.fixture
def dao_folder(initialized_db) -> FolderDAO:
    return FolderDAO(initialized_db)


@pytest.fixture
def sample_document(dao_document, tmp_path) -> int:
    """Veritabanına bir örnek belge ekler ve ID'sini döner."""
    # Gerçek dosya yolu benzeri, geçici klasörde
    fake_path = str(tmp_path / "ornek_belge.txt")
    return dao_document.create(
        title="Örnek Belge",
        file_path=fake_path,
        file_type="txt",
        extracted_text="Bu bir örnek metin içeriğidir. Kodlama testi için kullanılır.",
    )


@pytest.fixture
def sample_code(dao_code) -> int:
    """Veritabanına bir örnek kod ekler ve ID'sini döner."""
    return dao_code.create(name="TestKodu", color="#FF5733", description="Test amaçlı kod")


@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtCore import Qt
    app = QApplication.instance()
    if app is None:
        # Essential for QWebEngine in many environments
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        # Pass a dummy name as sys.argv[0] to avoid "Argument list is empty" error
        app = QApplication(["LexiScholarTest"])
    return app
