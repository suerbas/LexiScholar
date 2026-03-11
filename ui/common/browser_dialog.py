"""
Standalone Browser Dialog for LexiScholar visualizations.
"""

import os
from pathlib import Path
import tempfile
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QFileDialog, QToolBar,
    QSlider, QSpinBox, QMessageBox, QToolButton, QWidget, QSizePolicy, QComboBox
)
from PyQt6.QtCore import QUrl, Qt, pyqtSlot
from PyQt6.QtGui import QDesktopServices, QFont

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from PyQt6.QtCore import pyqtSignal
from .modern_dialog import ModernBaseDialog

class BrowserWidget(QWidget):
    """
    Widget version of HTML visualization browser for tabbed interface.
    """
    detach_requested = pyqtSignal()
    keyword_settings_changed = pyqtSignal(dict) # Emits {ngram_size, top_n, dedup_lim}

    def __init__(self, title: str, html_path: str, parent=None):
        super().__init__(parent)
        self.html_path = html_path
        # Fix: browser_dialog.py is in ui/common, so we need 3 dirnames to reach project root
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
            # Each BrowserWidget gets its own profile so downloadRequested signals don't pile up
            self._profile = QWebEngineProfile(f"browser_widget_{id(self)}", self)
            # Each BrowserWidget gets its own profile so downloadRequested signals don't pile up
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

    def setup_header_controls(self, layout, sentiment_results=None, topic_results=None, ner_results=None, model_type="BERT"):
        """Setup header controls for browser widget."""
        # Add export controls for sentiment analysis
        if sentiment_results:
            self._sentiment_results = sentiment_results
            self._sentiment_model = model_type
            self._is_sentiment_analysis = True
            self._setup_sentiment_export_controls(layout)
        # Add export controls for topic modeling
        elif topic_results:
            self._topic_results = topic_results
            self._topic_model = model_type
            self._is_topic_modeling = True
            self._setup_topic_export_controls(layout)
        elif ner_results:
            self._ner_results = ner_results
            self._ner_model = model_type
            self._is_ner_analysis = True
            self._setup_ner_export_controls(layout)
        else:
            self._is_sentiment_analysis = False
            self._is_topic_modeling = False

    def _setup_ner_export_controls(self, layout):
        """Add export buttons for NER results."""
        from PyQt6.QtWidgets import QPushButton, QMenu

        export_btn = QPushButton("📊 Dışa Aktar")
        export_btn.setToolTip("NER sonuçlarını farklı formatlarda kaydet")
        export_btn.setFixedHeight(32)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)

        menu = QMenu(self)
        word_action = menu.addAction("📝 Word (.docx)")
        word_action.triggered.connect(lambda: self._export_ner_word(self._ner_results, self._ner_model))
        html_action = menu.addAction("🌐 HTML (.html)")
        html_action.triggered.connect(lambda: self._export_ner_html(self._ner_results, self._ner_model))
        export_btn.setMenu(menu)
        layout.addWidget(export_btn)

    def _setup_sentiment_export_controls(self, layout):
        """Add export buttons for sentiment analysis results."""
        from PyQt6.QtWidgets import QPushButton, QMenu
        
        # Export button with dropdown
        export_btn = QPushButton("📊 Dışa Aktar")
        export_btn.setToolTip("Analiz sonuçlarını farklı formatlarda kaydet")
        export_btn.setFixedHeight(32)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        # Create menu
        menu = QMenu(self)
        
        # Excel action
        excel_action = menu.addAction("📊 Excel (.xlsx)")
        excel_action.triggered.connect(lambda: self._export_sentiment_excel(self._sentiment_results, self._sentiment_model))
        
        # Word action
        word_action = menu.addAction("📝 Word (.docx)")
        word_action.triggered.connect(lambda: self._export_sentiment_word(self._sentiment_results, self._sentiment_model))
        
        # HTML action
        html_action = menu.addAction("🌐 HTML (.html)")
        html_action.triggered.connect(lambda: self._export_sentiment_html(self._sentiment_results, self._sentiment_model))
        
        export_btn.setMenu(menu)
        layout.addWidget(export_btn)

    def _setup_topic_export_controls(self, layout):
        """Add export buttons for topic modeling results."""
        from PyQt6.QtWidgets import QPushButton, QMenu
        
        # Export button with dropdown
        export_btn = QPushButton("📊 Dışa Aktar")
        export_btn.setToolTip("Analiz sonuçlarını farklı formatlarda kaydet")
        export_btn.setFixedHeight(32)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        # Create menu
        menu = QMenu(self)
        
        # Check if this is hybrid mode
        is_hybrid = self._topic_results and self._topic_results.get("mode") == "hybrid"
        
        # Excel action
        excel_action = menu.addAction("📊 Excel (.xlsx)")
        if is_hybrid:
            excel_action.triggered.connect(lambda: self._export_topics_excel(self._topic_results, hybrid=True))
        else:
            excel_action.triggered.connect(lambda: self._export_topics_excel(self._topic_results, hybrid=False))
        
        # Word action
        word_action = menu.addAction("📝 Word (.docx)")
        if is_hybrid:
            word_action.triggered.connect(lambda: self._export_topics_word(self._topic_results, hybrid=True))
        else:
            word_action.triggered.connect(lambda: self._export_topics_word(self._topic_results, hybrid=False))
        
        # HTML action
        html_action = menu.addAction("🌐 HTML (.html)")
        if is_hybrid:
            html_action.triggered.connect(lambda: self._export_topics_html(self._topic_results, hybrid=True))
        else:
            html_action.triggered.connect(lambda: self._export_topics_html(self._topic_results, hybrid=False))
        
        export_btn.setMenu(menu)
        layout.addWidget(export_btn)

    def _export_topics_excel(self, topic_data, hybrid=False):
        """Export topic modeling results to Excel."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            if hybrid:
                from export.topic_exporters import export_hybrid_topics_to_excel
                default_name = "hibrit_konu_modelleme.xlsx"
            else:
                from export.topic_exporters import export_topics_to_excel
                default_name = "konu_modelleme.xlsx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Excel olarak kaydet",
                default_name,
                "Excel Dosyaları (*.xlsx)"
            )
            
            if file_path:
                if hybrid:
                    success = export_hybrid_topics_to_excel(file_path, topic_data)
                else:
                    model_type = topic_data.get("model_name", "LDA")
                    success = export_topics_to_excel(file_path, topic_data, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "Excel export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Excel export için openpyxl kütüphanesi gerekli:\n{e}")

    def _export_topics_html(self, topic_data, hybrid=False):
        """Export topic modeling results to HTML."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            if hybrid:
                from ..visualizations.semantic_analytics import generate_hybrid_topics_html
                model_name = topic_data.get("online", {}).get("model_name", "AI")
                generated_html_path = generate_hybrid_topics_html(topic_data, model_name=model_name)
                default_name = "hibrit_konu_modelleme.html"
            else:
                mode = topic_data.get("mode", "local")
                if mode == "online":
                    from ..visualizations.semantic_analytics import generate_online_topics_html
                    generated_html_path = generate_online_topics_html(topic_data, model_name=topic_data.get("model_name", "AI"))
                else:
                    from ..visualizations.semantic_analytics import generate_topics_html
                    generated_html_path = generate_topics_html(topic_data)
                default_name = "konu_modelleme.html"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "HTML olarak kaydet",
                default_name,
                "HTML Dosyaları (*.html)"
            )
            
            if file_path:
                with open(generated_html_path, 'r', encoding='utf-8') as src:
                    html_content = src.read()
                with open(file_path, 'w', encoding='utf-8') as dst:
                    dst.write(html_content)
                from ..common_ui import show_info
                show_info(self, "Başarılı", f"HTML kaydedildi:\n{file_path}")
        except Exception as e:
            from ..common_ui import show_error
            show_error(self, "Hata", f"HTML export sırasında hata oluştu:\n{str(e)}")

    def _export_topics_word(self, topic_data, hybrid=False):
        """Export topic modeling results to Word."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            if hybrid:
                from export.topic_exporters import export_hybrid_topics_to_word
                default_name = "hibrit_konu_modelleme.docx"
            else:
                from export.topic_exporters import export_topics_to_word
                default_name = "konu_modelleme.docx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Word olarak kaydet",
                default_name,
                "Word Belgeleri (*.docx)"
            )
            
            if file_path:
                if hybrid:
                    model_type = topic_data.get("online", {}).get("model_name", "AI")
                    success = export_hybrid_topics_to_word(file_path, topic_data, model_type)
                else:
                    model_type = topic_data.get("model_name", "LDA")
                    success = export_topics_to_word(file_path, topic_data, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "Word export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Word export için python-docx kütüphanesi gerekli:\n{e}")

    def _export_sentiment_excel(self, results, model_type):
        """Export sentiment results to Excel."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            from export.sentiment_exporters import export_sentiment_to_excel
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Excel olarak kaydet",
                "duygu_analizi.xlsx",
                "Excel Dosyaları (*.xlsx)"
            )
            
            if file_path:
                success = export_sentiment_to_excel(file_path, results, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "Excel export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Excel export için openpyxl kütüphanesi gerekli:\n{e}")

    def _export_sentiment_word(self, results, model_type):
        """Export sentiment results to Word."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            from export.sentiment_exporters import export_sentiment_to_word
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Word olarak kaydet",
                "duygu_analizi.docx",
                "Word Belgeleri (*.docx)"
            )
            
            if file_path:
                success = export_sentiment_to_word(file_path, results, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "Word export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Word export için python-docx kütüphanesi gerekli:\n{e}")

    def _export_sentiment_html(self, results, model_type):
        """Export sentiment results to HTML."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            from export.sentiment_exporters import export_sentiment_to_html
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "HTML olarak kaydet",
                "duygu_analizi.html",
                "HTML Dosyaları (*.html)"
            )
            
            if file_path:
                success = export_sentiment_to_html(file_path, results, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "HTML export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"HTML export sırasında hata oluştu:\n{e}")

    def _export_ner_word(self, ner_data, model_type):
        """Export NER results to Word."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            from export.ner_exporters import export_ner_to_word
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Word olarak kaydet",
                "varlik_tanima.docx",
                "Word Belgeleri (*.docx)"
            )
            if file_path:
                success = export_ner_to_word(file_path, ner_data, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "Word export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Word export için python-docx kütüphanesi gerekli:\n{e}")

    def _export_ner_html(self, ner_data, model_type):
        """Export NER results to HTML."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            from export.ner_exporters import export_ner_to_html
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "HTML olarak kaydet",
                "varlik_tanima.html",
                "HTML Dosyaları (*.html)"
            )
            if file_path:
                success = export_ner_to_html(file_path, ner_data, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "HTML export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"HTML export sırasında hata oluştu:\n{e}")

    def closeEvent(self, event):
        """Explicitly clear webengine objects on close to avoid profile lifecycle warnings."""
        if hasattr(self, 'browser') and self.browser:
            # Setting a blank page or deleting the view early can help
            self.browser.setParent(None)
            self.browser.deleteLater()
        if hasattr(self, '_page') and self._page:
            self._page.deleteLater()
        super().closeEvent(event)
            
    def _handle_download(self, download):
        """Handle download requests triggered via JS data URLs (e.g. exportAsImage)."""
        # Guard: Prevent re-entrant calls (multiple widgets sharing the same profile
        # can trigger this handler more than once for a single download event).
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
                # İptal edildi — indirmeyi reddet
                try:
                    download.cancel()
                except Exception:
                    pass
        finally:
            # Reset flag after a short delay to avoid blocking legitimate next downloads
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, lambda: setattr(self, '_is_handling_download', False))

    def load_url(self, path):
        if WEBENGINE_AVAILABLE and os.path.exists(path):
            self.browser.setUrl(QUrl.fromLocalFile(path))

    def set_toolbar_visible(self, visible: bool):
        """Show or hide the main toolbar."""
        self.toolbar.setVisible(visible)

    def _add_trailing_controls(self):
        """Add detach button to the end of the toolbar."""
        self.toolbar.addSeparator()
        
        # Fresh button with standard icon design
        btn = QPushButton("↗")
        btn.setToolTip("Pencereyi Ayır")
        btn.setFixedSize(28, 28)
        btn.setStyleSheet("""
            QPushButton { 
                border: 1px solid #E2E8F0; background: #F8FAFC; color: #64748B; 
                font-size: 14px; font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background: #F1F5F9; color: #1E293B; border-color: #CBD5E1; }
        """)
        btn.clicked.connect(self.detach_requested.emit)
        self.toolbar.addWidget(btn)
        btn.show()

    def add_word_cloud_controls(self):
        """Add controls for word clouds with +/- buttons and value labels."""
        from PyQt6.QtWidgets import QWidget, QSizePolicy, QToolButton
        self.toolbar.clear()
        
        # Left Spacer for Centering
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

    def add_word_cloud_controls(self):
        """Add controls for word clouds with +/- buttons and value labels."""
        from PyQt6.QtWidgets import QWidget, QSizePolicy, QToolButton
        self.toolbar.clear()
        
        # Left Spacer for Centering
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

        # Helper for slider with controls
        def add_controlled_slider(label_text, min_v, max_v, default_v, js_func, step=5, width=70, bold=True, tooltip=None):
            lbl = QLabel(label_text)
            weight = "bold" if bold else "normal"
            lbl.setStyleSheet(f"font-weight: {weight}; margin-right: 2px;")
            if tooltip:
                lbl.setToolTip(tooltip)
            self.toolbar.addWidget(lbl)
            
            # Value tag
            val_lbl = QLabel(str(default_v))
            val_lbl.setFixedWidth(25)
            val_lbl.setStyleSheet("color: #3B82F6; font-weight: bold; font-family: 'Consolas';")

            # Slider
            sld = QSlider(Qt.Orientation.Horizontal)
            sld.setRange(min_v, max_v)
            sld.setValue(default_v)
            sld.setFixedWidth(width)
            
            def on_change(v):
                val_lbl.setText(str(v))
                self.run_js(f"{js_func}({v})")
            sld.valueChanged.connect(on_change)

            # Plus/Minus buttons
            btn_style = "QToolButton { border: 1px solid #CBD5E1; border-radius: 3px; background: white; font-weight: bold; } QToolButton:hover { background: #F1F5F9; }"
            
            btn_min = QToolButton()
            btn_min.setText("-")
            btn_min.setToolTip(f"{label_text.rstrip(':')} miktarını azalt")
            btn_min.setFixedSize(20, 20)
            btn_min.setStyleSheet(btn_style)
            btn_min.clicked.connect(lambda: sld.setValue(sld.value() - step))
            
            btn_plus = QToolButton()
            btn_plus.setText("+")
            btn_plus.setToolTip(f"{label_text.rstrip(':')} miktarını artır")
            btn_plus.setFixedSize(20, 20)
            btn_plus.setStyleSheet(btn_style)
            btn_plus.clicked.connect(lambda: sld.setValue(sld.value() + step))

            self.toolbar.addWidget(btn_min)
            self.toolbar.addWidget(sld)
            self.toolbar.addWidget(btn_plus)
            self.toolbar.addWidget(val_lbl)
            return sld

        # 1. Word Count Control
        self.count_slider = add_controlled_slider("Sözcükler:", 10, 300, 50, "setWordCount", step=1)
        
        self.toolbar.addSeparator()

        # 2. Scale Control
        self.scale_slider = add_controlled_slider("Boyut:", 30, 200, 80, "setScale", step=5)

        self.toolbar.addSeparator()

        # 3. Min Frequency (Minimum Tekrar) - Now using the same slider pattern
        freq_tip = "Bir kelimenin bulutta görünmesi için sahip olması gereken en az tekrar sayısı."
        self.freq_slider = add_controlled_slider("Min. Tekrar:", 1, 50, 1, "setMinFreq", step=1, width=60, bold=False, tooltip=freq_tip)

        # Style for action buttons
        btn_style = """
            QPushButton { 
                border: 1px solid #D1D5DB; border-radius: 4px; padding: 4px 10px; 
                font-size: 10px; font-weight: 600; color: #374151; background: #F9FAFB;
            }
            QPushButton:hover { background: #F3F4F6; border-color: #9CA3AF; }
        """

        # Action Buttons
        refresh_btn = QPushButton("🔄 Düzenle")
        refresh_btn.setToolTip("Bulutu rastgele yeniden oluşturur")
        refresh_btn.setStyleSheet(btn_style)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(lambda: self.run_js("reshuffle()"))
        self.toolbar.addWidget(refresh_btn)
        
        clear_btn = QPushButton("🧹 Temizle")
        clear_btn.setToolTip("Gizlenen kelimeleri geri getirir")
        clear_btn.setStyleSheet(btn_style)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self.run_js("clearExclusions()"))
        self.toolbar.addWidget(clear_btn)
        
        # Save — artık mavi ribbon'da (setup_header_controls ile)
        # NOTE: export_btn intentionally removed from toolbar; lives on blue ribbon instead.

        # Right Spacer for Centering

    # ── Crosstab Specific Toolbar ─────────────────────────────────────
    def add_crosstab_controls(self):
        """Add controls for crosstab visualizations."""
        from PyQt6.QtWidgets import QWidget, QSizePolicy
        self.toolbar.clear()

        # Left Spacer for centering
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

        # Central button style matching Code Matrix
        btn_style = """
            QPushButton { 
                border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 12px; 
                font-size: 11px; font-weight: 600; color: #1E293B; background: #F8FAFC;
            }
            QPushButton:hover { background: #F1F5F9; border-color: #CBD5E1; }
        """

        # Fit to screen
        fit_btn = QPushButton("📺 Ekrana Sığdır")
        fit_btn.setToolTip("Görselleştirmeyi ekrana sığdır")
        fit_btn.setStyleSheet(btn_style)
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.clicked.connect(lambda: self.run_js("fitToScreen()"))
        self.toolbar.addWidget(fit_btn)

        # Export — artık mavi ribbon'da (setup_header_controls ile)
        # NOTE: save_btn intentionally removed from toolbar; lives on blue ribbon instead.

        # Right Spacer for centering
        spacer_r = QWidget()
        spacer_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_r)
        
        # NOTE: _add_trailing_controls() intentionally NOT called here.
        # Detach icon lives exclusively on the blue PanelHeader ribbon.

    # ── Code Matrix Specific Toolbar ──────────────────────────────────
    def add_code_matrix_controls(self):
        """Restore and center secondary toolbar for Code Matrix; features reverted from header."""
        from PyQt6.QtWidgets import QWidget, QSizePolicy
        self.toolbar.clear()
        self.toolbar.show()

        # Left Spacer for Centering
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

        # Central Button Style matching Summary Table
        btn_style = """
            QPushButton { 
                border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 12px; 
                font-weight: 600; background: #F8FAFC; color: #1E293B; 
            }
            QPushButton:hover { background: #F1F5F9; }
        """

        # Mode Toggle Button
        mode_btn = QPushButton("🔥 Isı Haritası")
        mode_btn.setToolTip("Görünümü değiştir (Daireler / Isı Haritası)")
        mode_btn.setStyleSheet(btn_style)
        mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mode_btn._is_heatmap = False
        
        def toggle_mode():
            mode_btn._is_heatmap = not mode_btn._is_heatmap
            if mode_btn._is_heatmap:
                self.run_js("toggleHeatmap(true)")
                mode_btn.setText("🔘 Daireler")
            else:
                self.run_js("toggleHeatmap(false)")
                mode_btn.setText("🔥 Isı Haritası")
        
        mode_btn.clicked.connect(toggle_mode)
        self.toolbar.addWidget(mode_btn)

        # Zoom/Fit Button
        fit_btn = QPushButton("📺 Sığdır")
        fit_btn.setToolTip("Görselleştirmeyi ekrana sığdır")
        fit_btn.setStyleSheet(btn_style)
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.clicked.connect(lambda: self.run_js("zoomReset()"))
        self.toolbar.addWidget(fit_btn)

        # Save — artık mavi ribbon'da (setup_header_controls ile)
        # NOTE: save_btn intentionally removed from toolbar; lives on blue ribbon instead.

        # Right Spacer for Centering
        spacer_r = QWidget()
        spacer_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_r)

    # ── Graph Specific Toolbar ────────────────────────────────────────
    def add_graph_controls(self, node_count=0, edge_count=0):
        """Add controls for relationship graphs."""
        from PyQt6.QtWidgets import QWidget, QSizePolicy, QToolButton
        self.toolbar.clear()
        
        # Left Spacer
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

        # Stats Label
        stats = QLabel(f"📊 Kod: {node_count} | İlişki: {edge_count}")
        stats.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; padding-right: 15px;")
        self.toolbar.addWidget(stats)

        # Helper for slider (Defining it locally if needed, or we could move it to class level)
        # For now, let's keep the graph specific buttons consistent
        btn_style = """
            QPushButton { 
                border: 1px solid #D1D5DB; border-radius: 4px; padding: 4px 12px; 
                font-size: 11px; font-weight: 600; color: #374151; background: #F9FAFB;
            }
            QPushButton:hover { background: #F3F4F6; }
            QPushButton:checked { background: #E0E7FF; border-color: #3B82F6; color: #1E40AF; }
        """

        # Action Buttons
        restart_btn = QPushButton("🔄 Düzenle")
        restart_btn.setToolTip("Graf yerleşimini yeniden hesaplar")
        restart_btn.setStyleSheet(btn_style)
        restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restart_btn.clicked.connect(lambda: self.run_js("restartSimulation()"))
        self.toolbar.addWidget(restart_btn)

        label_btn = QPushButton("🏷️ Etiketler")
        label_btn.setToolTip("Düğüm isimlerini göster/gizle")
        label_btn.setCheckable(True)
        label_btn.setChecked(True)
        label_btn.setStyleSheet(btn_style)
        label_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        label_btn.toggled.connect(lambda chk: self.run_js(f"toggleLabels({str(chk).lower()})"))
        self.toolbar.addWidget(label_btn)

        fit_btn = QPushButton("📺 Odakla")
        fit_btn.setToolTip("Grafı merkeze odaklar")
        fit_btn.setStyleSheet(btn_style)
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.clicked.connect(lambda: self.run_js("fitToScreen()"))
        self.toolbar.addWidget(fit_btn)

        # Save — artık mavi ribbon'da (setup_header_controls ile)
        # NOTE: save_btn intentionally removed from toolbar; lives on blue ribbon instead.

        # Right Spacer
        spacer_r = QWidget()
        spacer_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_r)

    # ── Simple Visualization Toolbar ──────────────────────────────────
    def add_simple_controls(self, help_anchor=None, help_tooltip=None):
        """Clear toolbar for simple visualizations — Save button lives on blue ribbon."""
        self.toolbar.clear()
        # toolbar boş kalıyor; kaydet butonu setup_header_controls ile mavi ribbon'a eklendi.
        self.toolbar.setVisible(False)

    def run_js(self, code):
        """Helper to execute JS in the browser."""
        if WEBENGINE_AVAILABLE and self.browser.page():
            self.browser.page().runJavaScript(code)

    def _open_encyclopedia(self, anchor=""):
        page = os.path.join(self._base_for_docs, "docs", "encyclopedia", "analysis_tools.html")
        url = QUrl.fromLocalFile(page)
        if anchor:
            url.setFragment(anchor.lstrip('#'))
        QDesktopServices.openUrl(url)

    def add_help(self, anchor=""):
        """Add a help button to the toolbar."""
        help_btn = QToolButton()
        help_btn.setText("❓")
        help_btn.setToolTip("Yardım")
        help_btn.setFixedSize(26, 26)
        help_btn.setStyleSheet("""
            QToolButton { border: none; background: transparent; color: #64748B; font-size: 14px; }
            QToolButton:hover { color: #1E293B; background: #F1F5F9; border-radius: 4px; }
        """)
        help_btn.clicked.connect(lambda: self._open_encyclopedia(anchor))
        self.toolbar.addWidget(help_btn)

    # ── Keyword Analysis Controls ─────────────────────────────────────
    def add_keyword_controls(self, current_settings: dict = None):
        """Add controls for Keyword Analysis (YAKE)."""
        self.toolbar.clear()
        
        settings = current_settings or {'ngram_size': 2, 'top_n': 30, 'dedup_lim': 0.9}

        # N-Gram Size
        self.toolbar.addWidget(QLabel("Kelime Grubu:"))
        self.ngram_combo = QComboBox()
        self.ngram_combo.setToolTip("Analiz edilecek kelime öbeği uzunluğu (N-gram)")
        self.ngram_combo.addItems(["1 (Tek)", "2 (İkili)", "3 (Üçlü)"])
        # Map 1->0, 2->1, 3->2
        self.ngram_combo.setCurrentIndex(settings.get('ngram_size', 2) - 1)
        self.ngram_combo.setFixedWidth(80)
        self.toolbar.addWidget(self.ngram_combo)

        # Top N
        self.toolbar.addWidget(QLabel("Limit:"))
        self.top_spin = QSpinBox()
        self.top_spin.setToolTip("Gösterilecek en önemli anahtar kelime sayısı")
        self.top_spin.setRange(5, 100)
        self.top_spin.setValue(settings.get('top_n', 30))
        self.top_spin.setFixedWidth(60)
        self.toolbar.addWidget(self.top_spin)
        
        self.toolbar.addSeparator()
        
        refresh_btn = QPushButton("⚡ Yenile")
        refresh_btn.setToolTip("Yeni ayarlarla analizi tekrar çalıştır")
        refresh_btn.setStyleSheet("background: #3B82F6; color: white; font-weight: bold;")
        refresh_btn.clicked.connect(self._emit_keyword_settings)
        self.toolbar.addWidget(refresh_btn)

        self.toolbar.addSeparator()

        # Save — artık mavi ribbon'da (setup_header_controls ile)
        # NOTE: export_btn intentionally removed from toolbar; lives on blue ribbon instead.
        
        # Removed trailing controls (detach button) as requested

    def _emit_keyword_settings(self):
        """Collect settings and emit signal."""
        # Index 0->1, 1->2, 2->3
        ngram = self.ngram_combo.currentIndex() + 1
        top_n = self.top_spin.value()
        
        self.keyword_settings_changed.emit({
            'ngram_size': ngram,
            'top_n': top_n,
            'dedup_lim': 0.9 # Default for now
        })

    def _save_visualization_screenshot(self):
        """Capture the web view as a PNG using QWebEngineView.grab() — works for ALL HTML pages."""
        if not WEBENGINE_AVAILABLE:
            return
        
        # Try native JS exportAsImage first (for pages that support it)
        # For the rest, fall back to Python-side screenshot.
        self._try_js_export_then_screenshot()

    def _try_js_export_then_screenshot(self):
        """Try JS-based export first; if JS returns undefined/false, do Python screenshot."""
        if not WEBENGINE_AVAILABLE:
            return

        def on_js_result(result):
            # If JS export was triggered (result is True), download handler will handle it.
            # If result is False/None, the JS function doesn't exist — fall back to screenshot.
            if not result:
                self._do_python_screenshot()

        # Check if exportAsImage is defined AND call it
        self.browser.page().runJavaScript(
            "(function() { if (typeof window.exportAsImage === 'function') { window.exportAsImage(); return true; } return false; })()",
            on_js_result
        )

    def _do_python_screenshot(self):
        """Take a screenshot of the web view widget using Qt and save as PNG."""
        from PyQt6.QtWidgets import QFileDialog, QApplication
        from PyQt6.QtGui import QPixmap
        import os

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Görseli Kaydet",
            "gorsellesirme.png",
            "PNG Dosyası (*.png);;JPEG Dosyası (*.jpg)"
        )
        if not save_path:
            return

        # Use QWebEngineView.grab() to capture the rendered page
        pixmap = self.browser.grab()
        if pixmap.isNull():
            from ..common_ui import show_warning
            show_warning(self, "Hata", "Görsel yakalanırken hata oluştu.")
            return

        if not pixmap.save(save_path):
            from ..common_ui import show_warning
            show_warning(self, "Hata", f"Dosya kaydedilemedi:\n{save_path}")

    def _export_sentiment_excel(self, results, model_type):
        """Export sentiment results to Excel."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            # Check if this is hybrid mode
            is_hybrid = results and 'local' in results[0] and 'online' in results[0]
            
            if is_hybrid:
                from export.sentiment_exporters import export_hybrid_sentiment_to_excel
                default_name = "hibrit_duygu_analizi.xlsx"
            else:
                from export.sentiment_exporters import export_sentiment_to_excel
                default_name = "duygu_analizi.xlsx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Excel olarak kaydet",
                default_name,
                "Excel Dosyaları (*.xlsx)"
            )
            
            if file_path:
                if is_hybrid:
                    success = export_hybrid_sentiment_to_excel(file_path, results)
                else:
                    success = export_sentiment_to_excel(file_path, results, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "Excel export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Excel export için openpyxl kütüphanesi gerekli:\n{e}")

    def _export_sentiment_word(self, results, model_type):
        """Export sentiment results to Word."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            # Check if this is hybrid mode
            is_hybrid = results and 'local' in results[0] and 'online' in results[0]
            
            if is_hybrid:
                from export.sentiment_exporters import export_hybrid_sentiment_to_word
                default_name = "hibrit_duygu_analizi.docx"
            else:
                from export.sentiment_exporters import export_sentiment_to_word
                default_name = "duygu_analizi.docx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Word olarak kaydet",
                default_name,
                "Word Belgeleri (*.docx)"
            )
            
            if file_path:
                if is_hybrid:
                    success = export_hybrid_sentiment_to_word(file_path, results, model_type)
                else:
                    success = export_sentiment_to_word(file_path, results, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "Word export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Word export için python-docx kütüphanesi gerekli:\n{e}")

    def _export_sentiment_html(self, results, model_type):
        """Export sentiment results to HTML."""
        from PyQt6.QtWidgets import QFileDialog
        try:
            # Check if this is hybrid mode
            is_hybrid = results and 'local' in results[0] and 'online' in results[0]
            
            if is_hybrid:
                from export.sentiment_exporters import export_hybrid_sentiment_to_html
                default_name = "hibrit_duygu_analizi.html"
            else:
                from export.sentiment_exporters import export_sentiment_to_html
                default_name = "duygu_analizi.html"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "HTML olarak kaydet",
                default_name,
                "HTML Dosyaları (*.html)"
            )
            
            if file_path:
                if is_hybrid:
                    success = export_hybrid_sentiment_to_html(file_path, results, model_type)
                else:
                    success = export_sentiment_to_html(file_path, results, model_type)
                if success:
                    from ..common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ..common_ui import show_error
                    show_error(self, "Hata", "HTML export sırasında hata oluştu.")
        except ImportError as e:
            from ..common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"HTML export sırasında hata oluştu:\n{e}")


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
        # Dynamic delegation or direct exposure:
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
