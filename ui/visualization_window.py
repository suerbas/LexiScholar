
"""
Visualization Window for LexiScholar
Displays HTML content within the application using QWebEngineView.
"""


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QFileDialog, QToolButton
)
from PyQt6.QtCore import QUrl, pyqtSignal, Qt
from PyQt6.QtGui import QDesktopServices
import os
from .styles import get_color
from .visualizations import (
    generate_keywords_html, generate_sentiment_html, generate_topics_html, 
    generate_entities_html, generate_kwic_html, generate_document_portrait_html,
    generate_coverage_heatmap_html, generate_code_timeline_html, generate_sankey_html
)


IMPORT_ERROR_MSG = None

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except Exception as e:
    print(f"DEBUG: Error importing QWebEngineView: {e}")
    IMPORT_ERROR_MSG = str(e)
    # import traceback
    # traceback.print_exc()
    WEBENGINE_AVAILABLE = False


class VisualizationWindow(QWidget):
    """Widget for displaying HTML visualizations embedded in main window."""
    
    close_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header layout - Ultra Compact version
        header_frame = QFrame()
        header_frame.setFixedHeight(34) # Slim ribbon
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('bg_panel')};
                border-bottom: 1px solid {get_color('border')};
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(0)
        
        # We'll hide the label entirely to save space, or make it very small
        self.time_label = QLabel("") 
        self.time_label.setVisible(False)
        
        # Context help was here previously

        close_btn = QPushButton("← Belgeye Dön")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('bg_main')};
                border: 1px solid {get_color('border')};
                border-radius: 4px;
                padding: 2px 10px;
                color: {get_color('text_secondary')};
                font-weight: 600;
                font-size: 11px;
                height: 24px;
            }}
            QPushButton:hover {{
                background-color: {get_color('bg_hover')};
                border-color: {get_color('border_hover')};
                color: {get_color('text_primary')};
            }}
        """)
        close_btn.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(self.time_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        self.layout.addWidget(header_frame)
        
        # Content area
        if WEBENGINE_AVAILABLE:
            self.browser = QWebEngineView()
            self.browser.page().profile().downloadRequested.connect(self._handle_download)
            self.layout.addWidget(self.browser)
        else:
            self.error_widget = QWidget()
            err_layout = QVBoxLayout(self.error_widget)
            self.error_label = QLabel()
            self.error_label.setStyleSheet("font-size: 14px; padding: 20px; color: #DC2626;")
            err_layout.addWidget(self.error_label)
            self.layout.addWidget(self.error_widget)
            
    def load_visualization(self, title: str, html_path: str):
        """Load a new visualization."""
        self.time_label.setText(title)
        self._set_help_for_title(title)
        
        if WEBENGINE_AVAILABLE:
            if os.path.exists(html_path):
                url = QUrl.fromLocalFile(html_path)
                self.browser.setUrl(url)
            else:
                self.browser.setHtml(f"<h3 style='color:red; padding:20px'>Dosya bulunamadı: {html_path}</h3>")
        else:
            error_msg = IMPORT_ERROR_MSG or "Bilinmeyen hata"
            self.error_label.setText(
                f"Görselleştirme için 'PyQt6-WebEngine' kütüphanesi gerekli.\n"
                f"Hata Detayı: {error_msg}\n\n"
                "Lütfen terminalden şu komutu çalıştırın:\n"
                "pip install PyQt6-WebEngine"
            )

    def _set_help_for_title(self, title: str):
        """No longer adds tooltip directly to VisualizationWindow as it's handled by PanelHeader."""
        pass

    def _handle_download(self, download):
        """Handle download requests from the browser."""
        # Simple data URL download handler
        path = download.downloadFileName()
        suffix = os.path.splitext(path)[1] or ".png"
        
        # Show file dialog to user
        from PyQt6.QtWidgets import QFileDialog
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Görüntüyü Kaydet", path, f"Resim Dosyası (*{suffix})"
        )
        
        if save_path:
            download.setDownloadDirectory(os.path.dirname(save_path))
            download.setDownloadFileName(os.path.basename(save_path))
            download.setDownloadFileName(os.path.basename(save_path))
            download.accept()

    # ============================================================================
    # New Visualizations (Phase 5)
    # ============================================================================

    def show_code_coverage(self, data: dict):
        """Show Code Coverage Heatmap."""
        html_path = generate_coverage_heatmap_html(data)
        self.load_visualization("Kod Kapsam Haritası", html_path)

    def show_code_timeline(self, data: list, doc_title: str):
        """Show Code Timeline."""
        html_path = generate_code_timeline_html(data, doc_title)
        self.load_visualization(f"Kod Zaman Çizelgesi: {doc_title}", html_path)

    def show_sankey_diagram(self, data: dict):
        """Show Code Relations Sankey Diagram."""
        html_path = generate_sankey_html(data)
        self.load_visualization("Kod İlişkileri (Sankey)", html_path)
