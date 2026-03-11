"""
Standalone Browser Dialog for LexiScholar visualizations.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QFileDialog, QToolBar,
    QSlider, QSpinBox, QMessageBox, QToolButton, QWidget, QSizePolicy, QComboBox
)
from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from .modern_dialog import ModernBaseDialog
from .browser._mixins.export import BrowserExportMixin
from .browser._mixins.toolbar import BrowserToolbarMixin


class BrowserWidget(QWidget, BrowserExportMixin, BrowserToolbarMixin):
    """
    Widget version of HTML visualization browser for tabbed interface.
    """
    detach_requested = pyqtSignal()
    keyword_settings_changed = pyqtSignal(dict) # Emits {ngram_size, top_n, dedup_lim}

    def __init__(self, title: str, html_path: str, parent=None):
        super().__init__(parent)
        self.html_path = html_path
        self._base_for_docs = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._title = title
        
        # Initialize sentiment analysis attributes
        self._sentiment_results = None
        self._sentiment_model = "BERT"
        self._is_sentiment_analysis = False
        
        self._setup_ui()
        self.load_url(html_path)

    def _setup_ui(self):
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: #F8FAFC;")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────
        self.toolbar = QToolBar("Görselleştirme Araçları")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar { 
                background: white; border-bottom: 1px solid #E2E2E2; 
                padding: 2px 5px; spacing: 8px;
            }
            QLabel { color: #475569; font-weight: 600; font-size: 10px; margin-left: 2px; }
            QSlider::handle:horizontal { background: #3B82F6; border-radius: 5px; width: 14px; height: 14px; }
            QPushButton { 
                border: 1px solid #E2E8F0; border-radius: 4px; padding: 2px 8px; 
                font-size: 10px; font-weight: 600; color: #1E293B; background: #F8FAFC;
            }
            QPushButton:hover { background: #F1F5F9; border-color: #CBD5E1; }
        """)
        self.main_layout.addWidget(self.toolbar)

        self._add_trailing_controls()

        # Browser ─ Isolated profile per widget to prevent download-handler accumulation
        if WEBENGINE_AVAILABLE:
            from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
            self._profile = QWebEngineProfile(f"browser_widget_{id(self)}", self)
            self._page = QWebEnginePage(self._profile, self)
            self._is_handling_download = False
            self._profile.downloadRequested.connect(self._handle_download)

            self.browser = QWebEngineView()
            self.browser.setPage(self._page)
            self.main_layout.addWidget(self.browser)
        else:
            err = QLabel("Görselleştirme için PyQt6-WebEngine kütüphanesi yüklü değil.")
            err.setStyleSheet("padding: 50px; color: #DC2626; font-weight: bold;")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_layout.addWidget(err)

    def closeEvent(self, event):
        """Explicitly clear webengine objects on close to avoid profile lifecycle warnings."""
        if hasattr(self, 'browser') and self.browser:
            self.browser.setParent(None)
            self.browser.deleteLater()
        if hasattr(self, '_page') and self._page:
            self._page.deleteLater()
        super().closeEvent(event)
            
    def _handle_download(self, download):
        """Handle download requests triggered via JS data URLs (e.g. exportAsImage)."""
        if self._is_handling_download:
            try:
                download.cancel()
            except Exception:
                pass
            return
        
        self._is_handling_download = True
        try:
            path = download.downloadFileName()
            suffix = os.path.splitext(path)[1] or ".png"
            
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Görüntüyü Kaydet", path, f"Resim Dosyası (*{suffix})"
            )
            
            if save_path:
                download.setDownloadDirectory(os.path.dirname(save_path))
                download.setDownloadFileName(os.path.basename(save_path))
                download.accept()
            else:
                try:
                    download.cancel()
                except Exception:
                    pass
        finally:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, lambda: setattr(self, '_is_handling_download', False))

    def load_url(self, path):
        if WEBENGINE_AVAILABLE and os.path.exists(path):
            self.browser.setUrl(QUrl.fromLocalFile(path))

    def run_js(self, code):
        """Helper to execute JS in the browser."""
        if WEBENGINE_AVAILABLE and self.browser.page():
            self.browser.page().runJavaScript(code)


class BrowserDialog(ModernBaseDialog):
    """
    Standalone dialog wrapper for HTML visualizations.
    """
    def __init__(self, title: str, html_path: str, parent=None):
        super().__init__(parent, min_width=1100, min_height=800)
        self._title_text = title
        self._html_path = html_path
        self._setup_ui()
    
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header Area
        header_layout = QHBoxLayout()
        icon = QLabel("📈")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title_lbl = QLabel(self._title_text)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        
        # Red X Close Button
        close_btn_top = QPushButton("✕")
        close_btn_top.setFixedSize(32, 32)
        close_btn_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_top.clicked.connect(self.close)
        close_btn_top.setStyleSheet("""
            QPushButton { background: transparent; color: #64748B; font-size: 18px; font-weight: bold; border: none; border-radius: 16px; }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; }
        """)
        header_layout.addWidget(close_btn_top)
        self.layout.addLayout(header_layout)

        self.widget = BrowserWidget(self._title_text, self._html_path, self)
        self.layout.addWidget(self.widget)
        
        # Expose widget methods for caller (like add_word_cloud_controls)
        self.add_word_cloud_controls = self.widget.add_word_cloud_controls
        self.add_crosstab_controls = self.widget.add_crosstab_controls
        self.add_code_matrix_controls = self.widget.add_code_matrix_controls
        self.add_graph_controls = self.widget.add_graph_controls
        self.add_simple_controls = self.widget.add_simple_controls
        self.add_keyword_controls = self.widget.add_keyword_controls
        self.add_help = self.widget.add_help
        self.load_url = self.widget.load_url
        self.run_js = self.widget.run_js

        # Configure controls based on title
        t = self._title_text.lower()
        widget = self.widget
        help_anchor = ""

        if any(x in t for x in ["kelime", "bulut", "cloud"]) and "anahtar" not in t:
            widget.add_word_cloud_controls()
            help_anchor = "word-cloud" if "kelime" in t else "code-cloud"
        elif "anahtar" in t and "kelime" in t:
            # Anahtar Kelime Analizi (YAKE)
            help_anchor = "keyword-analysis"
        elif any(x in t for x in ["frekans", "frequency"]):
            widget.add_simple_controls()
            help_anchor = "word-frequency"
        elif any(x in t for x in ["çapraz", "crosstab"]):
            widget.add_crosstab_controls()
            help_anchor = "crosstab"
        elif any(x in t for x in ["kod matris", "matris", "matrix"]):
            widget.add_code_matrix_controls()
            help_anchor = "code-matrix"
        elif any(x in t for x in ["zaman", "timeline", "dağılım"]):
            widget.add_simple_controls()
            help_anchor = "timeline"
        elif any(x in t for x in ["kapsam", "ısı", "heatmap"]):
            widget.add_simple_controls()
            help_anchor = "coverage-heatmap"
        elif any(x in t for x in ["portre", "resmi", "portrait"]):
            widget.add_simple_controls()
            help_anchor = "portrait"
        elif "kwic" in t:
            widget.add_simple_controls()
            help_anchor = "kwic"
        else:
            widget.add_simple_controls()

        if help_anchor:
            widget.add_help(help_anchor)
