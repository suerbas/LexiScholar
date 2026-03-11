"""
Word Frequency Widget and Dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QSpinBox, QHeaderView, QFrame, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from ..styles import TABLE_STYLE, get_color
from ..common.modern_dialog import ModernBaseDialog
from ..common_ui import show_error

class WordFrequencyWidget(QWidget):
    """Widget showing word frequency analysis for tab integration."""
    
    def __init__(self, analysis_tools, documents, parent=None):
        super().__init__(parent)
        self.analysis = analysis_tools
        self.documents = documents
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setMinimumWidth(680)

        options_group = QFrame()
        options_group.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('bg_main')};
                border: 1px solid {get_color('border')};
                border-radius: 12px;
            }}
            QLabel {{ color: {get_color('text_secondary')}; font-weight: 700; font-size: 12px; border: none; }}
            QComboBox, QSpinBox {{
                padding: 6px 10px;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                color: #1E293B;
                font-size: 13px;
                min-height: 32px;
            }}
            QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {{ border: none; }}
        """)
        
        main_opts_layout = QVBoxLayout(options_group)
        main_opts_layout.setContentsMargins(16, 12, 16, 12)
        main_opts_layout.setSpacing(10)

        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(15)
        
        filters_layout.addWidget(QLabel("BELGE:"))
        self.doc_combo = QComboBox()
        self.doc_combo.addItem("Tüm Belgeler", None)
        for doc in self.documents:
            self.doc_combo.addItem(doc['title'], doc['id'])
        
        self.doc_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.doc_combo.setMinimumWidth(150)
        self.doc_combo.setMaximumWidth(300)
        filters_layout.addWidget(self.doc_combo)
        
        filters_layout.addWidget(QLabel("MİN. UZUNLUK:"))
        self.len_spin = QSpinBox()
        self.len_spin.setRange(2, 10)
        self.len_spin.setValue(3)
        self.len_spin.setFixedWidth(60)
        filters_layout.addWidget(self.len_spin)
        
        filters_layout.addWidget(QLabel("GÖSTER:"))
        self.top_spin = QSpinBox()
        self.top_spin.setRange(10, 200)
        self.top_spin.setValue(50)
        self.top_spin.setFixedWidth(70)
        filters_layout.addWidget(self.top_spin)
        
        filters_layout.addStretch()
        main_opts_layout.addLayout(filters_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        self.analyze_btn = QPushButton("Analiz Et")
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.setMinimumWidth(100)
        self.analyze_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.analyze_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('success')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {get_color('success_dark')}; }}
        """)
        self.analyze_btn.clicked.connect(self._analyze)
        button_layout.addWidget(self.analyze_btn)
        
        self.viz_btn = QPushButton("Görselleştir")
        self.viz_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.viz_btn.setMinimumWidth(100)
        self.viz_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.viz_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('primary')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {get_color('primary_dark')}; }}
            QPushButton:disabled {{ background-color: {get_color('border')}; color: {get_color('text_muted')}; }}
        """)
        self.viz_btn.clicked.connect(self._visualize)
        self.viz_btn.setEnabled(False)
        button_layout.addWidget(self.viz_btn)
        
        main_opts_layout.addLayout(button_layout)
        layout.addWidget(options_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Kelime", "Frekans"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF;
                alternate-background-color: {get_color('bg_main')};
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                gridline-color: #E2E8F0;
                font-size: 13px;
                color: #1E293B;
                selection-background-color: #EEF2FF;
                selection-color: #1E293B;
            }}
            QTableWidget::item {{ padding: 10px; }}
            QTableWidget::item:hover {{ background-color: {get_color('bg_main')}; color: #1E293B; }}
            QTableWidget::item:selected {{ background-color: #EEF2FF; color: #1E293B; }}
            QHeaderView::section {{
                background-color: {get_color('bg_main')};
                padding: 12px;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                font-weight: 700;
                color: #475569;
                font-size: 11px;
                text-transform: uppercase;
            }}
            QHeaderView::section:vertical {{
                background-color: #F1F5F9;
                color: #1E293B;
                font-weight: 600;
                font-size: 11px;
                padding: 6px 10px;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                border-right: 2px solid #CBD5E1;
                min-width: 36px;
            }}
        """)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.setStyleSheet("background-color: #FFFFFF;")
        self._analyze()
    
    def _analyze(self):
        """Run word frequency analysis."""
        doc_id = self.doc_combo.currentData()
        min_len = self.len_spin.value()
        top_n = self.top_spin.value()
        
        results = self.analysis.get_word_frequency(doc_id, min_len, top_n)
        
        self.table.setRowCount(len(results))
        for i, (word, count) in enumerate(results):
            self.table.setItem(i, 0, QTableWidgetItem(word))
            self.table.setItem(i, 1, QTableWidgetItem(str(count)))
        
        self.viz_btn.setEnabled(len(results) > 0)
        self.results = results
        self.analyzed_doc_title = self.doc_combo.currentText()

    def _visualize(self):
        """Show word frequency visualization."""
        if not hasattr(self, 'results') or not self.results:
            return
            
        doc_title = self.doc_combo.currentText()
        try:
            from ..visualizations.text_analytics import generate_word_frequency_html
            file_path = generate_word_frequency_html(self.results, doc_title)
            
            parent = self.parent()
            while parent:
                if hasattr(parent, '_open_visualization'):
                    break
                parent = parent.parent()
                
            if parent and hasattr(parent, '_open_visualization'):
                title = "Kelime Frekansı"
                subtitle = f"{doc_title} • {len(self.results)} kelime"
                
                widget = parent._open_visualization(title, file_path, subtitle=subtitle)
                
                if widget:
                    widget.set_toolbar_visible(True)
                    container = widget.parent()
                    if container:
                        from ..panel_header import PanelHeader
                        header = container.findChild(PanelHeader)
                        if header and header.custom_layout:
                            from PyQt6.QtWidgets import QPushButton
                            save_btn = QPushButton("📷 Kaydet")
                            save_btn.setToolTip("Görseli Kaydet")
                            save_btn.setStyleSheet("""
                                QPushButton {
                                    background-color: rgba(255, 255, 255, 0.15);
                                    color: white;
                                    border: 1px solid rgba(255, 255, 255, 0.3);
                                    border-radius: 4px;
                                    font-weight: bold;
                                    padding: 4px 12px;
                                }
                                QPushButton:hover {
                                    background-color: rgba(255, 255, 255, 0.25);
                                    border-color: white;
                                }
                            """)
                            save_btn.clicked.connect(lambda: widget.run_js("if (typeof window.exportAsImage === 'function') { window.exportAsImage(); } else { window.print(); }"))
                            header.custom_layout.addWidget(save_btn)

                    widget.add_simple_controls() 
                    widget.toolbar.clear()
                    
                    from PyQt6.QtWidgets import QPushButton
                    excel_btn = QPushButton("📄 Excel Olarak Kaydet")
                    excel_btn.setToolTip("Verileri CSV/Excel formatında kaydet")
                    excel_btn.clicked.connect(lambda: self._export_csv(widget))
                    widget.toolbar.addWidget(excel_btn)
                    widget._add_trailing_controls()

                if isinstance(self.window(), QDialog):
                    self.window().accept()
            else:
                import webbrowser
                webbrowser.open(f"file://{file_path}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            show_error(self, "Hata", f"Görselleştirme başarısız: {e}")

    def _export_csv(self, widget):
        """Export results to CSV."""
        from ..common_ui import get_save_file
        path = get_save_file(widget, "CSV Olarak Kaydet", "CSV Dosyası (*.csv)")
        if path:
            import csv
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Sıra", "Kelime", "Frekans"])
                    for i, (word, count) in enumerate(self.results):
                        writer.writerow([i+1, word, count])
                from ..common_ui import show_info
                show_info(widget, "Başarılı", "Veriler başarıyla kaydedildi.")
            except Exception as e:
                from ..common_ui import show_error
                show_error(widget, "Hata", f"Kaydetme başarısız: {e}")
    
    def _table_style(self):
        return TABLE_STYLE


class WordFrequencyDialog(ModernBaseDialog):
    """Standalone dialog wrapper for WordFrequencyWidget."""
    def __init__(self, analysis_tools, documents, parent=None):
        super().__init__(parent, min_width=800, min_height=600)
        self._setup_ui(analysis_tools, documents)

    def _setup_ui(self, analysis_tools, documents):
        self._setup_base_ui()
        
        header_layout = QHBoxLayout()
        icon = QLabel("📈")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel("Kelime Frekansı")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        close_btn_top = QPushButton("✕")
        close_btn_top.setFixedSize(32, 32)
        close_btn_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_top.clicked.connect(self.reject)
        close_btn_top.setStyleSheet("""
            QPushButton { background: transparent; color: #64748B; font-size: 18px; font-weight: bold; border: none; border-radius: 16px; }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; }
        """)
        header_layout.addWidget(close_btn_top)
        self.layout.addLayout(header_layout)

        self.widget = WordFrequencyWidget(analysis_tools, documents, self)
        self.layout.addWidget(self.widget)
        
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: {get_color('primary')}; color: white; border: none; border-radius: 10px; padding: 10px 40px; font-weight: 800; font-size: 13px; }}
            QPushButton:hover {{ background: {get_color('primary_dark')}; }}
        """)
        footer_layout.addWidget(close_btn)
        
        footer_layout.addStretch()
        self.layout.addLayout(footer_layout)
