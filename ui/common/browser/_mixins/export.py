"""
Export Mixin for BrowserWidget.
Handles Excel, Word, HTML, and Screenshot exports for visualizer data.
"""

from PyQt6.QtWidgets import QPushButton, QMenu, QFileDialog
    
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class BrowserExportMixin:
    """Handles external exports for the BrowserWidget."""
    
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
                    from ...common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ...common_ui import show_error
                    show_error(self, "Hata", "Excel export sırasında hata oluştu.")
        except ImportError as e:
            from ...common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Excel export için openpyxl kütüphanesi gerekli:\n{e}")

    def _export_topics_html(self, topic_data, hybrid=False):
        """Export topic modeling results to HTML."""
        try:
            if hybrid:
                from ...visualizations.semantic_analytics import generate_hybrid_topics_html
                model_name = topic_data.get("online", {}).get("model_name", "AI")
                generated_html_path = generate_hybrid_topics_html(topic_data, model_name=model_name)
                default_name = "hibrit_konu_modelleme.html"
            else:
                mode = topic_data.get("mode", "local")
                if mode == "online":
                    from ...visualizations.semantic_analytics import generate_online_topics_html
                    generated_html_path = generate_online_topics_html(topic_data, model_name=topic_data.get("model_name", "AI"))
                else:
                    from ...visualizations.semantic_analytics import generate_topics_html
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
                from ...common_ui import show_info
                show_info(self, "Başarılı", f"HTML kaydedildi:\n{file_path}")
        except Exception as e:
            from ...common_ui import show_error
            show_error(self, "Hata", f"HTML export sırasında hata oluştu:\n{str(e)}")

    def _export_topics_word(self, topic_data, hybrid=False):
        """Export topic modeling results to Word."""
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
                    from ...common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ...common_ui import show_error
                    show_error(self, "Hata", "Word export sırasında hata oluştu.")
        except ImportError as e:
            from ...common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Word export için python-docx kütüphanesi gerekli:\n{e}")

    def _export_sentiment_excel(self, results, model_type):
        """Export sentiment results to Excel."""
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
                    from ...common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ...common_ui import show_error
                    show_error(self, "Hata", "Excel export sırasında hata oluştu.")
        except ImportError as e:
            from ...common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Excel export için openpyxl kütüphanesi gerekli:\n{e}")

    def _export_sentiment_word(self, results, model_type):
        """Export sentiment results to Word."""
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
                    from ...common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ...common_ui import show_error
                    show_error(self, "Hata", "Word export sırasında hata oluştu.")
        except ImportError as e:
            from ...common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Word export için python-docx kütüphanesi gerekli:\n{e}")

    def _export_sentiment_html(self, results, model_type):
        """Export sentiment results to HTML."""
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
                    from ...common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ...common_ui import show_error
                    show_error(self, "Hata", "HTML export sırasında hata oluştu.")
        except ImportError as e:
            from ...common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"HTML export sırasında hata oluştu:\n{e}")

    def _export_ner_word(self, ner_data, model_type):
        """Export NER results to Word."""
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
                    from ...common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ...common_ui import show_error
                    show_error(self, "Hata", "Word export sırasında hata oluştu.")
        except ImportError as e:
            from ...common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"Word export için python-docx kütüphanesi gerekli:\n{e}")

    def _export_ner_html(self, ner_data, model_type):
        """Export NER results to HTML."""
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
                    from ...common_ui import show_info
                    show_info(self, "Başarılı", f"Rapor kaydedildi:\n{file_path}")
                else:
                    from ...common_ui import show_error
                    show_error(self, "Hata", "HTML export sırasında hata oluştu.")
        except ImportError as e:
            from ...common_ui import show_error
            show_error(self, "Eksik Kütüphane", f"HTML export sırasında hata oluştu:\n{e}")

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
            from ...common_ui import show_warning
            show_warning(self, "Hata", "Görsel yakalanırken hata oluştu.")
            return

        if not pixmap.save(save_path):
            from ...common_ui import show_warning
            show_warning(self, "Hata", f"Dosya kaydedilemedi:\n{save_path}")
