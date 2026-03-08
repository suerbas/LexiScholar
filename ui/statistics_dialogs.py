"""
Analysis Dialogs for LexiScholar - Statistics
UI for code statistics, word frequency, and co-occurrence analysis.
"""

from typing import List, Dict, Tuple, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QTabWidget, QWidget, QComboBox,
    QSpinBox, QGroupBox, QHeaderView, QMessageBox, QProgressBar, QFrame,
    QScrollArea, QTextEdit, QListWidget, QListWidgetItem, QSplitter, QToolButton,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QFont, QDesktopServices
from .styles import COLORS, TABLE_STYLE, get_color
from .common.modern_dialog import ModernBaseDialog
from .common_ui import show_info, show_warning, show_error, ask_confirmation


class StatisticsWidget(QWidget):
    """Widget showing code statistics for tab integration."""
    
    def __init__(self, analysis_tools, parent=None):
        super().__init__(parent)
        self.analysis = analysis_tools
        self._setup_ui()
        self._load_data()
    
    def _open_help(self, anchor):
        """Open encyclopedia help with correct anchor."""
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        page = os.path.join(base, "docs", "encyclopedia", "analysis_tools.html")
        url = QUrl.fromLocalFile(page)
        if anchor:
            url.setFragment(anchor.lstrip('#'))
        QDesktopServices.openUrl(url)

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Stats table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Kod", "Segment Sayısı", "Belge Sayısı", "Toplam Karakter", "Yoğunluk"
        ])
        
        # Header alignment and sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        
        self.table.verticalHeader().setVisible(False)
        
        # Modern table styling
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {get_color('bg_panel')};
                alternate-background-color: {get_color('bg_main')};
                border: 1px solid {get_color('border')};
                border-radius: 8px;
                gridline-color: {get_color('bg_hover')};
                font-size: 13px;
                color: {get_color('text_primary')};
                selection-background-color: {get_color('primary_50')};
                selection-color: {get_color('text_primary')};
            }}
            QTableWidget::item {{ padding: 10px; outline: none; }}
            QTableWidget::item:hover {{ background-color: {get_color('bg_hover')}; color: {get_color('text_secondary')}; outline: none; }}
            QTableWidget::item:selected {{ background-color: {get_color('primary_50')}; color: {get_color('text_primary')}; outline: none; }}
            QHeaderView::section {{
                background-color: {get_color('bg_main')};
                padding: 12px;
                border: none;
                border-bottom: 1px solid {get_color('border')};
                font-weight: 700;
                color: {get_color('text_secondary')};
                font-size: 11px;
                text-transform: uppercase;
            }}
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table)
        
        # Summary Area
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"background-color: {get_color('bg_main')}; border-radius: 8px; border: 1px solid {get_color('border')};")
        summary_layout = QHBoxLayout(summary_frame)
        
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 13px; font-weight: 600;")
        summary_layout.addWidget(self.summary_label)
        layout.addWidget(summary_frame)
        
        self.setStyleSheet(f"background-color: {get_color('bg_panel')};")
    
    def _load_data(self):
        """Load statistics data."""
        stats = self.analysis.get_code_statistics()
        
        self.table.setRowCount(len(stats))
        total_segments = sum(s['segment_count'] for s in stats)
        
        for i, stat in enumerate(stats):
            # Kod name with color
            name_item = QTableWidgetItem(f"● {stat['name']}")
            name_item.setForeground(QColor(stat['color']))
            name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            
            # Store code info for drill-down
            name_item.setData(Qt.ItemDataRole.UserRole, stat['id'])
            name_item.setData(Qt.ItemDataRole.UserRole + 1, stat['name'])
            name_item.setData(Qt.ItemDataRole.UserRole + 2, stat['color'])
            
            self.table.setItem(i, 0, name_item)
            
            # Segment count
            seg_item = QTableWidgetItem(str(stat['segment_count']))
            seg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, seg_item)
            
            # Document count
            doc_item = QTableWidgetItem(str(stat['document_count']))
            doc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, doc_item)
            
            # Total characters
            char_item = QTableWidgetItem(f"{stat['total_characters']:,}")
            char_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 3, char_item)
            
            # Density (percentage)
            if total_segments > 0:
                density = (stat['segment_count'] / total_segments) * 100
                dens_text = f"{density:.1f}%"
            else:
                dens_text = "0%"
            
            dens_item = QTableWidgetItem(dens_text)
            dens_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 4, dens_item)
        
        self.summary_label.setText(
            f"Toplam: {len(stats)} kod, {total_segments} segment"
        )
        
    def _on_cell_clicked(self, row, col):
        """Handle double-click on a row to show segments."""
        name_item = self.table.item(row, 0)
        if not name_item: return
        
        code_id = name_item.data(Qt.ItemDataRole.UserRole)
        code_name = name_item.data(Qt.ItemDataRole.UserRole + 1)
        code_color = name_item.data(Qt.ItemDataRole.UserRole + 2)
        
        if code_id is None: return
        
        # Dispatch to main window
        parent = self.parent()
        # Navigate up to find MainWindow or an object with the handler
        while parent:
            if hasattr(parent, '_on_coded_segments_requested'):
                parent._on_coded_segments_requested(code_id, code_name, code_color)
                return
            parent = parent.parent()
    
    def _table_style(self):
        return TABLE_STYLE
    
    def _button_style(self):
        return f"""
            QPushButton {{
                background-color: {get_color('primary')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {get_color('primary_dark')};
            }}
        """
    
    def _encyclopedia_path(self, anchor=""):
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        page = os.path.join(base, "docs", "encyclopedia", "analysis_tools.html")
        if anchor:
            return f"{page}{anchor}"
        return page


class StatisticsDialog(ModernBaseDialog):
    """Standalone dialog wrapper for StatisticsWidget."""
    def __init__(self, analysis_tools, parent=None):
        super().__init__(parent, min_width=800, min_height=600)
        self._setup_ui(analysis_tools)
        
    def _setup_ui(self, analysis_tools):
        self._setup_base_ui()
        
        # Header Area
        header_layout = QHBoxLayout()
        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel("Kod İstatistikleri")
        title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {get_color('text_primary')};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Red X Close Button
        close_btn_top = QPushButton("✕")
        close_btn_top.setFixedSize(32, 32)
        close_btn_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_top.clicked.connect(self.reject)
        close_btn_top.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {get_color('text_secondary')}; font-size: 18px; font-weight: bold; border: none; border-radius: 16px; }}
            QPushButton:hover {{ background: {get_color('error_bg')}; color: {get_color('error')}; }}
        """)
        header_layout.addWidget(close_btn_top)
        self.layout.addLayout(header_layout)

        # Widget Content
        self.widget = StatisticsWidget(analysis_tools, self)
        self.layout.addWidget(self.widget)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton { background: {get_color('primary')}; color: white; border: none; border-radius: 10px; padding: 10px 40px; font-weight: 800; font-size: 13px; }
            QPushButton:hover { background: {get_color('primary_dark')}; }
        """)
        footer_layout.addWidget(close_btn)
        
        footer_layout.addStretch()
        self.layout.addLayout(footer_layout)


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

        
        # Options Toolbar
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
        
        # Main layout for options group - Vertical to ensure buttons don't get squashed
        main_opts_layout = QVBoxLayout(options_group)
        main_opts_layout.setContentsMargins(16, 12, 16, 12)
        main_opts_layout.setSpacing(10)

        # Top row: Filters
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(15)
        
        # Document selector
        filters_layout.addWidget(QLabel("BELGE:"))
        self.doc_combo = QComboBox()
        self.doc_combo.addItem("Tüm Belgeler", None)
        for doc in self.documents:
            self.doc_combo.addItem(doc['title'], doc['id'])
        
        # Give combo box a flexible size policy but limit max width
        self.doc_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.doc_combo.setMinimumWidth(150)
        self.doc_combo.setMaximumWidth(300)
        filters_layout.addWidget(self.doc_combo)
        
        # Min length
        filters_layout.addWidget(QLabel("MİN. UZUNLUK:"))
        self.len_spin = QSpinBox()
        self.len_spin.setRange(2, 10)
        self.len_spin.setValue(3)
        self.len_spin.setFixedWidth(60)
        filters_layout.addWidget(self.len_spin)
        
        # Top N
        filters_layout.addWidget(QLabel("GÖSTER:"))
        self.top_spin = QSpinBox()
        self.top_spin.setRange(10, 200)
        self.top_spin.setValue(50)
        self.top_spin.setFixedWidth(70)
        filters_layout.addWidget(self.top_spin)
        
        filters_layout.addStretch()
        main_opts_layout.addLayout(filters_layout)

        # Bottom row: Action Buttons (Right aligned)
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
        
        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Kelime", "Frekans"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Modern table styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: {get_color('bg_main')};
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                gridline-color: #E2E8F0;
                font-size: 13px;
                color: #1E293B;
                selection-background-color: #EEF2FF;
                selection-color: #1E293B;
            }
            QTableWidget::item { padding: 10px; }
            QTableWidget::item:hover { background-color: {get_color('bg_main')}; color: #1E293B; }
            QTableWidget::item:selected { background-color: #EEF2FF; color: #1E293B; }
            QHeaderView::section {
                background-color: {get_color('bg_main')};
                padding: 12px;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                font-weight: 700;
                color: #475569;
                font-size: 11px;
                text-transform: uppercase;
            }
            QHeaderView::section:vertical {
                background-color: #F1F5F9;
                color: #1E293B;
                font-weight: 600;
                font-size: 11px;
                padding: 6px 10px;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                border-right: 2px solid #CBD5E1;
                min-width: 36px;
            }
        """)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.setStyleSheet("background-color: #FFFFFF;")
        
        # Initial analysis
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
        self.results = results # Store for visualization
        self.analyzed_doc_title = self.doc_combo.currentText()

    def _visualize(self):
        """Show word frequency visualization."""
        if not hasattr(self, 'results') or not self.results:
            return
            
        doc_title = self.doc_combo.currentText()
        try:
            from .visualizations.text_analytics import generate_word_frequency_html
            file_path = generate_word_frequency_html(self.results, doc_title)
            
            # Use parent's visualization opener if available
            parent = self.parent()
            # We need to find the MainWindow or AnalysisDialog instance
            while parent:
                if hasattr(parent, '_open_visualization'):
                    break
                parent = parent.parent()
                
            if parent and hasattr(parent, '_open_visualization'):
                # _open_visualization will add help controls automatically for "Frekans" title
                title = "Kelime Frekansı"
                subtitle = f"{doc_title} • {len(self.results)} kelime"
                
                widget = parent._open_visualization(title, file_path, subtitle=subtitle)
                
                if widget:
                    # 1. Hide default toolbar (we will add custom toolbar below header)
                    widget.set_toolbar_visible(True) # Keep visible for custom controls
                    
                    # 2. Add 'Save' button to the blue header bar
                    container = widget.parent()
                    if container:
                        from .panel_header import PanelHeader
                        header = container.findChild(PanelHeader)
                        if header and header.custom_layout:
                            # Add Save Button
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
                            # Use widget's JS runner
                            save_btn.clicked.connect(lambda: widget.run_js("if (typeof window.exportAsImage === 'function') { window.exportAsImage(); } else { window.print(); }"))
                            header.custom_layout.addWidget(save_btn)

                    # 3. Add Custom Controls to the Toolbar (below blue header)
                    widget.add_simple_controls() 
                    # Note: add_simple_controls clears the toolbar and adds Export button.
                    # Since we added Export to blue header, let's customize the toolbar.
                    widget.toolbar.clear()
                    
                    # Add Refresh/Analyze Again button?
                    # Since this is a static visualization from previous dialog, maybe just "Close"?
                    # Or maybe "Export as Excel" (csv)?
                    
                    from PyQt6.QtWidgets import QPushButton
                    
                    # Excel Export
                    excel_btn = QPushButton("📄 Excel Olarak Kaydet")
                    excel_btn.setToolTip("Verileri CSV/Excel formatında kaydet")
                    excel_btn.clicked.connect(lambda: self._export_csv(widget))
                    widget.toolbar.addWidget(excel_btn)
                    
                    widget._add_trailing_controls() # Add Detach button if needed (though header has it)

                # Close the settings dialog if it's a standalone window
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
        from .common_ui import get_save_file
        path = get_save_file(widget, "CSV Olarak Kaydet", "CSV Dosyası (*.csv)")
        if path:
            import csv
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Sıra", "Kelime", "Frekans"])
                    for i, (word, count) in enumerate(self.results):
                        writer.writerow([i+1, word, count])
                from .common_ui import show_info
                show_info(widget, "Başarılı", "Veriler başarıyla kaydedildi.")
            except Exception as e:
                from .common_ui import show_error
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
        
        # Header Area
        header_layout = QHBoxLayout()
        icon = QLabel("📈")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel("Kelime Frekansı")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Red X Close Button
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

        # Widget Content
        self.widget = WordFrequencyWidget(analysis_tools, documents, self)
        self.layout.addWidget(self.widget)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton { background: {get_color('primary')}; color: white; border: none; border-radius: 10px; padding: 10px 40px; font-weight: 800; font-size: 13px; }
            QPushButton:hover { background: {get_color('primary_dark')}; }
        """)
        footer_layout.addWidget(close_btn)
        
        footer_layout.addStretch()
        self.layout.addLayout(footer_layout)


class CooccurrenceWidget(QWidget):
    """Widget showing code co-occurrence matrix for tab integration."""
    
    def __init__(self, analysis_tools, parent=None):
        super().__init__(parent)
        self.analysis = analysis_tools
        self._setup_ui()
        self._load_data()
    
    def _open_help(self, anchor):
        """Open encyclopedia help with correct anchor."""
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        page = os.path.join(base, "docs", "encyclopedia", "analysis_tools.html")
        url = QUrl.fromLocalFile(page)
        if anchor:
            url.setFragment(anchor.lstrip('#'))
        QDesktopServices.openUrl(url)

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header = QHBoxLayout()
        title = QLabel("🔗 Kod Birlikte Oluşumu (Co-occurrence)")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #1E293B;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Info
        info = QLabel("Aynı belgede birlikte görünen kod çiftlerini gösterir.")
        info.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(info)
        
        # Matrix table
        self.table = QTableWidget()
        self.table.setStyleSheet(self._table_style() + """
            QTableWidget {
                selection-background-color: #EEF2FF;
                selection-color: #1E293B;
            }
            QTableWidget::item:hover { background-color: {get_color('bg_main')}; color: #1E293B; }
            QTableWidget::item:selected { background-color: #EEF2FF; color: #1E293B; }
        """)
        layout.addWidget(self.table)
        
        # Buttons layout
        btns_layout = QHBoxLayout()
        btns_layout.addStretch()
        
        self.viz_btn = QPushButton("📊 Grafiği Göster")
        self.viz_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.viz_btn.clicked.connect(self._visualize)
        self.viz_btn.setEnabled(False)
        btns_layout.addWidget(self.viz_btn)
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #94A3B8;
                color: #1E293B;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        close_btn.clicked.connect(self.accept)
        btns_layout.addWidget(close_btn)
        
        layout.addLayout(btns_layout)
        
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
    
    def _load_data(self):
        """Load co-occurrence data."""
        codes, matrix = self.analysis.get_cooccurrence_matrix()
        self.codes = codes
        self.matrix = matrix
        
        if not codes:
            return
        
        self.viz_btn.setEnabled(len(codes) > 0)
        
        n = len(codes)
        self.table.setRowCount(n)
        self.table.setColumnCount(n)
        
        # Set headers
        headers = [c['name'] for c in codes]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setVerticalHeaderLabels(headers)
        
        # Fill matrix
        for i in range(n):
            for j in range(n):
                value = matrix[i][j]
                item = QTableWidgetItem(str(value) if value > 0 else "")
                
                # Color based on value
                if value > 0:
                    intensity = min(255, 50 + value * 30)
                    item.setBackground(QColor(79, 70, 229, intensity))
                    if intensity > 150:
                        item.setForeground(QColor(255, 255, 255))
                
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)

    def _visualize(self):
        """Show co-occurrence graph."""
        if not hasattr(self, 'codes') or not self.codes:
            return
            
        try:
            from visualizations import generate_cooccurrence_graph
            file_path = generate_cooccurrence_graph(self.codes, self.matrix)
            
            # Use parent's visualization opener if available
            parent = self.parent()
            if hasattr(parent, '_open_visualization'):
                dlg = parent._open_visualization("Kod İlişki Grafiği", file_path)
                if dlg:
                    # Calculate edges
                    edge_count = sum(1 for i in range(len(self.matrix)) for j in range(i + 1, len(self.matrix[i])) if self.matrix[i][j] > 0)
                    dlg.add_graph_controls(node_count=len(self.codes), edge_count=edge_count)
                    
                    # Update help for the tab
                    for i in range(parent.central_tabs.count()):
                        if parent.central_tabs.tabText(i) == "Kod İlişki Grafiği":
                            container = parent.central_tabs.widget(i)
                            from .panel_header import PanelHeader
                            header = container.findChild(PanelHeader)
                            if header:
                                header.set_help("Kod İlişki Grafiği hakkında bilgi", "analysis_tools.html", "graph")
                            break
                            
                self.accept() # Close dialog
            else:
                import webbrowser
                webbrowser.open(f"file://{file_path}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            show_error(self, "Hata", f"Grafik oluşturulamadı: {e}")
    
    def _table_style(self):
        return TABLE_STYLE


class CooccurrenceDialog(ModernBaseDialog):
    """Standalone dialog wrapper for CooccurrenceWidget."""
    def __init__(self, analysis_tools, parent=None):
        super().__init__(parent, min_width=850, min_height=650)
        self._setup_ui(analysis_tools)

    def _setup_ui(self, analysis_tools):
        self._setup_base_ui()
        
        # Header Area
        header_layout = QHBoxLayout()
        icon = QLabel("🔗")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel("Kod Birlikte Oluşumu")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Red X Close Button
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

        # Widget Content
        self.widget = CooccurrenceWidget(analysis_tools, self)
        self.layout.addWidget(self.widget)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton { background: {get_color('primary')}; color: white; border: none; border-radius: 10px; padding: 10px 40px; font-weight: 800; font-size: 13px; }
            QPushButton:hover { background: {get_color('primary_dark')}; }
        """)
        footer_layout.addWidget(close_btn)
        
        footer_layout.addStretch()
        self.layout.addLayout(footer_layout)
