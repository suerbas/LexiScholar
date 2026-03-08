import sys
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.main_window import MainWindow
from ui.panel_header import PanelHeader
from ui.icons import IconProvider

pytestmark = pytest.mark.a11y


def test_main_window_accessibility_metadata_smoke(qapp, tmp_db_path):
    window = MainWindow(db_path=tmp_db_path, project_name="A11Y Test")
    try:
        assert window.objectName() == "MainWindow"
        assert window.ribbon.accessibleName() == "Uygulama Şeridi"
        assert window.central_tabs.accessibleName() == "Merkez Sekmeler"
        assert window.document_tree.tree.accessibleName() == "Belge Listesi"
        assert window.code_tree.tree.accessibleName() == "Kod Listesi"
        assert window.document_browser.text_edit.accessibleName() == "Belge Metin Alanı"
        assert window.retrieved_segments.btn_query.accessibleName() == "Gelişmiş Sorgu"
        assert window.retrieved_segments.btn_export.accessibleName() == "Segment Dışa Aktar"
    finally:
        window.close()
        window.deleteLater()


def test_keyboard_focus_policies_smoke(qapp, tmp_db_path):
    window = MainWindow(db_path=tmp_db_path, project_name="Focus Test")
    try:
        strong = Qt.FocusPolicy.StrongFocus
        assert window.btn_undo.focusPolicy() == strong
        assert window.btn_redo.focusPolicy() == strong
        assert window.btn_layout_toggle.focusPolicy() == strong
        assert window.btn_ai_settings.focusPolicy() == strong
        assert window.btn_guide.focusPolicy() == strong
        assert window.retrieved_segments.btn_query.focusPolicy() == strong
        assert window.retrieved_segments.btn_export.focusPolicy() == strong
        assert window.retrieved_segments.btn_prev_page.focusPolicy() == strong
        assert window.retrieved_segments.btn_next_page.focusPolicy() == strong
    finally:
        window.close()
        window.deleteLater()


def test_panel_header_controls_have_accessibility_and_icons(qapp):
    header = PanelHeader("Test Panel", has_minimize=True)
    try:
        assert header.btn_help.accessibleName() == "Yardım"
        assert header.btn_minimize.text() == "—"
        assert header.btn_minimize.accessibleName() == "Paneli Küçült"
        assert header.btn_detach.text() == "↗"
        assert header.btn_detach.accessibleName() == "Paneli Ayır"
        header.set_detached(True)
        assert header.btn_maximize.text() == "◻"
        assert header.btn_maximize.accessibleName() == "Tam Ekran"
        assert header.btn_dock.text() == "↙"
        assert header.btn_dock.accessibleName() == "Panele Geri Yerleştir"
        
        # Test close button visibility logic
        assert header.findChild(QPushButton, "CloseBtn") is not None
        
        header_no_close = PanelHeader("Non-closable", has_close=False)
        header_no_close.set_detached(True)
        assert header_no_close.findChild(QPushButton, "CloseBtn") is None
        header_no_close.deleteLater()
    finally:
        header.close()
        header.deleteLater()


def test_icon_provider_action_icons_smoke():
    assert not IconProvider.get_action_icon("undo").isNull()
    assert not IconProvider.get_action_icon("search").isNull()
    assert not IconProvider.get_action_icon("help").isNull()
