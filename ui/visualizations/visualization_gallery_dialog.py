"""
Visualization Gallery Widget for LexiScholar
Central dashboard for creating and exporting charts.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, 
    QListWidgetItem, QGroupBox, QComboBox, QRadioButton, 
    QPushButton, QLabel, QFrame, QHeaderView, QSizePolicy, QToolButton,
    QButtonGroup, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QColor

from .charts.chart_widgets import LexiBarChart, LexiPieChart
from ..styles import COLORS, get_color
from analysis.statistics_engine import StatisticsEngine
from database.variable_dao import VariableDAO


class VisualizationGalleryWidget(QWidget):
    """Main visualization dashboard for central tab integration."""
    
    detach_requested = pyqtSignal()

    def __init__(self, db_path: str = "lexischolar.db", parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.engine = StatisticsEngine(db_path)
        self.var_dao = VariableDAO(db_path)
        
        self._setup_ui()
        self._load_initial_data()

    def _mode_btn_style(self, checked: bool = False) -> str:
        """Generate style for mode selection buttons."""
        if checked:
            return f"""
                QPushButton {{
                    background-color: white;
                    color: {COLORS['primary_700']};
                    border: 1px solid {COLORS['primary_400']};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 12px;
                    font-weight: 600;
                    text-align: center;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 12px;
                    font-weight: 500;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: #F1F5F9;
                    border-color: {COLORS['border_hover']};
                }}
            """

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- TOP TOOLBAR ---
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(48)
        self.toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-bottom: 1px solid #CBD5E1;
            }}
        """)
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 0, 8, 0)
        toolbar_layout.setSpacing(4)
        
        # Divider
        div = QFrame()
        div.setFixedSize(1, 24)
        div.setStyleSheet("background-color: #CBD5E1; margin: 0 8px;")
        toolbar_layout.addWidget(div)
        
        # Export Button
        self.btn_export = QPushButton("📥 Dışa Aktarma")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 6px 12px;
                color: #334155;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { 
                background-color: #F1F5F9; 
                border-color: #E2E8F0;
            }
        """)
        toolbar_layout.addWidget(self.btn_export)
        
        toolbar_layout.addStretch()
        
        # Header Info (Right)
        header_info = QLabel("📊 Grafik Görüntüleyici")
        header_info.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500; margin-right: 12px;")
        toolbar_layout.addWidget(header_info)
        
        main_layout.addWidget(self.toolbar)
        
        # --- MAIN SPLITTER ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{ background-color: #CBD5E1; }}
        """)
        
        # --- LEFT: CHART AREA ---
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #F0F2F5;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 32, 32, 32)
        
        # Main Chart Container (The white card)
        self.chart_container = QFrame()
        self.chart_container.setObjectName("ChartContainer")
        self.chart_container.setStyleSheet("""
            QFrame#ChartContainer {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(16, 16, 16, 16)
        self.chart_layout.setSpacing(0)
        
        self.current_chart = LexiBarChart(title="Kod Frekansları")
        self.chart_layout.addWidget(self.current_chart)
        
        content_layout.addWidget(self.chart_container, 1)
        self.splitter.addWidget(content_widget)

        # --- RIGHT: SETTINGS SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-left: 1px solid #CBD5E1;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Sidebar Header
        sb_header = QFrame()
        sb_header.setFixedHeight(40)
        sb_header.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E2E8F0;")
        sb_h_layout = QHBoxLayout(sb_header)
        sb_h_layout.setContentsMargins(12, 0, 12, 0)
        
        sb_title = QLabel("⚙️ GRAFİK AYARLARI")
        sb_title.setStyleSheet("color: #475569; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        sb_h_layout.addWidget(sb_title)
        sidebar_layout.addWidget(sb_header)
        
        # Sidebar Content (Scrollable)
        sb_scroll = QScrollArea()
        sb_scroll.setWidgetResizable(True)
        sb_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        sb_inner = QWidget()
        sb_inner_layout = QVBoxLayout(sb_inner)
        sb_inner_layout.setContentsMargins(16, 16, 16, 16)
        sb_inner_layout.setSpacing(24)
        
        # Section 1: Data Source
        ds_layout = QVBoxLayout()
        ds_layout.setSpacing(8)
        ds_lbl = QLabel("Veri Kaynağı")
        ds_lbl.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 600;")
        ds_layout.addWidget(ds_lbl)
        
        self.scope_combo = QComboBox()
        self.scope_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px; border: 1px solid #CBD5E1; border-radius: 4px;
                font-size: 12px; background-color: white; color: #1E293B;
            }
            QComboBox:hover { border-color: #94A3B8; }
        """)
        ds_layout.addWidget(self.scope_combo)
        
        # Section 1.1: Variable Selection (Context aware)
        self.var_selection_lbl = QLabel("Değişken Seçimi")
        self.var_selection_lbl.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 600;")
        self.var_selection_lbl.hide()
        ds_layout.addWidget(self.var_selection_lbl)
        
        self.var_combo = QComboBox()
        self.var_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px; border: 1px solid #CBD5E1; border-radius: 4px;
                font-size: 12px; background-color: white; color: #1E293B;
            }
            QComboBox:hover { border-color: #94A3B8; }
        """)
        self.var_combo.hide()
        ds_layout.addWidget(self.var_combo)
        
        sb_inner_layout.addLayout(ds_layout)
        
        # Section 2: Chart Type Select (2x2 Icons)
        typ_layout = QVBoxLayout()
        typ_layout.setSpacing(8)
        typ_lbl = QLabel("Grafik Tipi")
        typ_lbl.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 600;")
        typ_layout.addWidget(typ_lbl)
        
        grid_layout = QHBoxLayout() # We'll just use the toolbar group for now, or match it
        grid = QFrame()
        grid_grid = QVBoxLayout(grid)
        grid_grid.setContentsMargins(0, 0, 0, 0)
        grid_grid.setSpacing(8)
        
        row1 = QHBoxLayout()
        self.sb_btn_v = QPushButton("📊 Dikey")
        self.sb_btn_h = QPushButton("📑 Yatay")
        row2 = QHBoxLayout()
        self.sb_btn_pie = QPushButton("🥧 Pasta")
        self.sb_btn_donut = QPushButton("⭕ Donut")
        
        for btn in [self.sb_btn_v, self.sb_btn_h, self.sb_btn_pie, self.sb_btn_donut]:
            btn.setCheckable(True)
            btn.setStyleSheet(self._mode_btn_style(False))
            
        row1.addWidget(self.sb_btn_v)
        row1.addWidget(self.sb_btn_h)
        row2.addWidget(self.sb_btn_pie)
        row2.addWidget(self.sb_btn_donut)
        
        grid_grid.addLayout(row1)
        grid_grid.addLayout(row2)
        typ_layout.addWidget(grid)
        sb_inner_layout.addLayout(typ_layout)
        
        self.sb_type_group = QButtonGroup(self)
        self.sb_type_group.addButton(self.sb_btn_v)
        self.sb_type_group.addButton(self.sb_btn_h)
        self.sb_type_group.addButton(self.sb_btn_pie)
        self.sb_type_group.addButton(self.sb_btn_donut)
        self.sb_btn_v.setChecked(True)
        
        # Section 3: View Options
        opt_layout = QVBoxLayout()
        opt_layout.setSpacing(8)
        opt_lbl = QLabel("Görünüm Seçenekleri")
        opt_lbl.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 600;")
        opt_layout.addWidget(opt_lbl)
        
        self.chk_labels = QRadioButton("Veri Etiketlerini Göster")
        self.chk_legend = QRadioButton("Açıklamaları (Legend) Göster")
        # Use simple checkboxes style even if they are radio buttons or just real checkboxes
        cb_style = """
            QCheckBox { spacing: 8px; color: #334155; font-size: 12px; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #CBD5E1; }
            QCheckBox::indicator:checked { background-color: #2563EB; border-color: #2563EB; }
        """
        # Let's use real checkboxes for these
        from PyQt6.QtWidgets import QCheckBox
        self.chk_labels = QCheckBox("Veri Etiketlerini Göster")
        self.chk_legend = QCheckBox("Açıklamaları (Legend) Göster")
        self.chk_labels.setChecked(True)
        self.chk_legend.setChecked(True)
        self.chk_labels.setStyleSheet(cb_style)
        self.chk_legend.setStyleSheet(cb_style)
        
        opt_layout.addWidget(self.chk_labels)
        opt_layout.addWidget(self.chk_legend)
        sb_inner_layout.addLayout(opt_layout)
        
        sb_inner_layout.addStretch()
        sb_scroll.setWidget(sb_inner)
        sidebar_layout.addWidget(sb_scroll)
        
        self.splitter.addWidget(self.sidebar)
        self.splitter.setSizes([740, 260]) # Standard ratios
        main_layout.addWidget(self.splitter)
        
        # Connections
        self.btn_export.clicked.connect(self._export_current)
        
        # Sync toolbar and sidebar chart types - REMOVED since toolbar buttons were deleted
        
        # Trigger updates
        self.scope_combo.currentIndexChanged.connect(self._on_mode_selection_changed)
        self.var_combo.currentIndexChanged.connect(self._on_selection_changed)
        self.sb_type_group.buttonClicked.connect(self._on_chart_type_changed)
        self.chk_labels.stateChanged.connect(self._on_selection_changed)
        self.chk_legend.stateChanged.connect(self._on_selection_changed)

    def _load_initial_data(self):
        """Initial load: Show all codes for frequency selection."""
        self.scope_combo.clear()
        self.scope_combo.addItem("🎯 Kod Frekansları", "all_codes")
        self.scope_combo.addItem("📊 Belge Değişkenleri", "variables")
        self.scope_combo.setCurrentIndex(0)
        self._on_mode_selection_changed()

    def _on_mode_selection_changed(self):
        """Handle top-level data source selection."""
        mode = self.scope_combo.currentData()
        if mode == "variables":
            self.var_selection_lbl.show()
            self.var_combo.show()
            self._populate_variables()
        else:
            self.var_selection_lbl.hide()
            self.var_combo.hide()
            self._refresh_chart()

    def _populate_variables(self):
        """Fill var_combo with available document variables."""
        self.var_combo.clear()
        vars = self.var_dao.get_all()
        for v in vars:
            self.var_combo.addItem(f"📊 {v['name']}", v['id'])
        if vars:
            self.var_combo.setCurrentIndex(0)
        self._refresh_chart()

    def _on_selection_changed(self):
        """Update chart when selection or options change."""
        self._refresh_chart()

    def _on_chart_type_changed(self, button=None):
        """Update chart type based on toolbar or sidebar selection."""
        # Update button styles
        for btn in [self.sb_btn_v, self.sb_btn_h, self.sb_btn_pie, self.sb_btn_donut]:
            btn.setStyleSheet(self._mode_btn_style(btn.isChecked()))
        self._refresh_chart()

    def _refresh_chart(self):
        """Refresh the chart based on current settings."""
        if self.scope_combo.currentIndex() < 0:
            return
        
        mode = self.scope_combo.currentData()
        
        # Determine chart type
        if self.sb_btn_v.isChecked(): chart_type, horizontal = "bar", False
        elif self.sb_btn_h.isChecked(): chart_type, horizontal = "bar", True
        elif self.sb_btn_pie.isChecked(): chart_type, horizontal = "pie", False
        else: chart_type, horizontal = "donut", False
        
        show_labels = self.chk_labels.isChecked()
        show_legend = self.chk_legend.isChecked()

        # Fetch Data
        labels, values, colors, title = [], [], [], ""

        if mode == "all_codes":
            data = self.engine.get_code_frequencies()
            labels = [d['name'] for d in data]
            values = [d['count'] for d in data]
            colors = [d['color'] for d in data]
            title = "Kod Frekansları"
        else:
            # Document variables selection
            var_id = self.var_combo.currentData()
            if var_id:
                data = self.engine.get_variable_distribution(var_id)
                labels = [d['value'] for d in data]
                values = [d['count'] for d in data]
                title = f"{self.var_combo.currentText().replace('📊 ', '')} Dağılımı"
            else:
                return # No variable selected

        # Clean and rebuild chart
        for i in reversed(range(self.chart_layout.count())):
            w = self.chart_layout.itemAt(i).widget()
            if w: w.setParent(None)

        if "pie" in chart_type or "donut" in chart_type:
            self.current_chart = LexiPieChart(title=title)
            self.current_chart.update_data(
                labels, values, 
                colors if mode == "all_codes" else None, 
                is_donut="donut" in chart_type,
                show_labels=show_labels,
                show_legend=show_legend
            )
        else:
            self.current_chart = LexiBarChart(title=title)
            self.current_chart.update_data(
                labels, values, 
                colors if mode == "all_codes" else None, 
                horizontal=horizontal,
                show_labels=show_labels,
                show_legend=show_legend
            )
        
        # Force options to chart via direct JS if needed or just pass them to update_data (to be updated)
        # For now, let's update modern_charts.py to handle these.
        
        self.chart_layout.addWidget(self.current_chart)

    
    def _export_current(self):
        """Export current chart image."""
        if hasattr(self, 'current_chart') and self.current_chart:
            self.current_chart.export_image()
