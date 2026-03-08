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

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from .charts.chart_widgets import LexiBarChart, LexiPieChart
from ..styles import COLORS, get_color
from analysis.statistics_engine import StatisticsEngine
from database.variable_dao import VariableDAO


class StepCard(QFrame):
    """Modern card component for a settings step."""
    
    def __init__(self, step_number: int, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("StepCard")
        self.setStyleSheet(f"""
            QFrame#StepCard {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 0px;
            }}
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)
        
        # Header with step number
        header = QHBoxLayout()
        header.setSpacing(8)
        
        step_badge = QLabel(f"{step_number}")
        step_badge.setStyleSheet(f"""
            background-color: {COLORS['primary']};
            color: white;
            border-radius: 10px;
            padding: 2px 8px;
            font-weight: bold;
            font-size: 11px;
        """)
        step_badge.setFixedSize(20, 20)
        step_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {COLORS['primary_900']}; font-weight: 600; font-size: 13px;")
        
        header.addWidget(step_badge)
        header.addWidget(title_lbl)
        header.addStretch()
        
        self.main_layout.addLayout(header)
        
        # Optional description
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; margin-bottom: 4px;")
            desc_lbl.setWordWrap(True)
            self.main_layout.addWidget(desc_lbl)
        
        # Content container
        self.content = QVBoxLayout()
        self.content.setSpacing(8)
        self.main_layout.addLayout(self.content)


class VisualizationGalleryWidget(QWidget):
    """Main visualization dashboard for central tab integration."""
    
    detach_requested = pyqtSignal()

    def __init__(self, db_path: str = "lexischolar.db", parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.engine = StatisticsEngine(db_path)
        self.var_dao = VariableDAO(db_path)
        
    def _create_summary_chip(self, icon: str, text: str, color_key: str = "primary") -> QLabel:
        """Create a summary chip with icon and text."""
        chip = QLabel(f"{icon} {text}")
        chip.setStyleSheet(f"""
            background-color: {COLORS[f'{color_key}_100']};
            color: {COLORS[f'{color_key}_900']};
            border: 1px solid {COLORS[f'{color_key}_200']};
            border-radius: 12px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 500;
        """)
        return chip

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main Splitter: Left Sidebar | Right Content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- Left Control Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_sidebar']};
                border-right: 1px solid {COLORS['border']};
        
        self.summary_layout.addStretch()

    def setup_header_controls(self, layout: QHBoxLayout):
        """Add export buttons to the blue panel header when in tab mode."""
        layout.addSpacing(10)
        btn_export = QToolButton()
        btn_export.setText("💾 Resmi Kaydet")
        btn_export.setToolTip("Mevcut grafiği yüksek çözünürlüklü (300 DPI) olarak kaydet.")
        btn_export.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn_export.setStyleSheet(f"""
            QToolButton {{
                color: white; font-weight: bold; border: 1px solid rgba(255,255,255,0.3); 
                border-radius: 4px; padding: 4px 10px; background: rgba(255,255,255,0.1);
            }}
            QToolButton:hover {{ background: rgba(255,255,255,0.2); }}
        """)
        btn_export.clicked.connect(self._export_current)
        layout.addWidget(btn_export)
        layout.addSpacing(5)

    def _mode_btn_style(self, color_theme: str) -> str:
        """Generate style for mode selection buttons."""
        colors = {
            "primary": (COLORS['primary'], COLORS['primary_100'], COLORS['primary_900']),
            "accent": (COLORS['accent'], COLORS['accent_100'], COLORS['accent_700']),
            "info": (COLORS['info'], COLORS['info_bg'], COLORS['info']),
        }
        base, bg, text = colors.get(color_theme, colors["primary"])
        
        return f"""
            QPushButton {{
                background-color: white;
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 500;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {bg};
                border-color: {base};
            }}
            QPushButton:checked {{
                background-color: {bg};
                border-color: {base};
                color: {text};
                font-weight: 600;
            }}
        """

    def _load_initial_data(self):
        """Initial load: Show all codes for frequency selection."""
        self._on_mode_changed()

    def _on_mode_changed(self):
        self.item_list.clear()
        if self.radio_codes.isChecked():
            self.list_label.setText("Grafik Kapsamı:")
            item = QListWidgetItem("Tüm Proje (Kod Frekansları)")
            item.setData(Qt.ItemDataRole.UserRole, "all_codes")
            self.item_list.addItem(item)
            self.item_list.setCurrentRow(0)
            self.combo_type.setEnabled(True)
        elif self.radio_vars.isChecked():
            self.list_label.setText("Değişken Seçin:")
            vars = self.var_dao.get_all()
            for v in vars:
                item = QListWidgetItem(f"📊 {v['name']}")
                item.setData(Qt.ItemDataRole.UserRole, v['id'])
                self.item_list.addItem(item)
            if vars:
                self.item_list.setCurrentRow(0)
            self.combo_type.setEnabled(True)
        elif self.radio_heatmap.isChecked():
            self.list_label.setText("Görünüm:")
            item = QListWidgetItem("Tüm Proje Yoğunluğu")
            item.setData(Qt.ItemDataRole.UserRole, "heatmap")
            self.item_list.addItem(item)
            self.item_list.setCurrentRow(0)
            self.combo_type.setEnabled(False) # Heatmap has its own view

    def _refresh_chart(self):
        selected_items = self.item_list.selectedItems()
        if not selected_items: return
        
        selected_data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # --- Handle Heatmap (Plotly/HTML Integration) ---
        if self.radio_heatmap.isChecked():
            self._show_heatmap_view()
            return

        chart_type = self.combo_type.currentText()
        is_horizontal = self.radio_h.isChecked()
        
        # ... rest of refresh ...
        
        # 1. Fetch Data
        labels = []
        values = []
        colors = []
        title = ""
        
        if self.radio_codes.isChecked():
            # Project wide code frequencies
            data = self.engine.get_code_frequencies()
            labels = [d['name'] for d in data]
            values = [d['count'] for d in data]
            colors = [d['color'] for d in data]
            title = "Proje Geneli Kod Frekansları"
        else:
            # Variable distribution
            var_id = selected_data
            data = self.engine.get_variable_distribution(var_id)
            labels = [d['value'] for d in data]
            values = [d['count'] for d in data]
            title = f"{selected_items[0].text()} Dağılımı"

        self.chart_title_label.setText(title)
        
        # 2. Swap Chart Widget if needed
        is_pie = "Pasta" in chart_type or "Halka" in chart_type
        is_donut = "Halka" in chart_type
        
        # Clean current layout
        for i in reversed(range(self.chart_layout.count())): 
            self.chart_layout.itemAt(i).widget().setParent(None)
            
        if is_pie:
            self.current_chart = LexiPieChart(title=title)
            self.current_chart.update_data(labels, values, colors if self.radio_codes.isChecked() else None, is_donut=is_donut)
        else:
            self.current_chart = LexiBarChart(title=title)
            self.current_chart.update_data(labels, values, colors if self.radio_codes.isChecked() else None, horizontal=is_horizontal)
            
        self.chart_layout.addWidget(self.current_chart)

    def _show_heatmap_view(self):
        """Generates and displays the interactive Heatmap via WebEngine."""
        self.chart_title_label.setText("Kod Yoğunluk Haritası (Isı Haritası)")
        
        # 1. Clear current layout
        for i in reversed(range(self.chart_layout.count())): 
            w = self.chart_layout.itemAt(i).widget()
            if w: w.setParent(None)
            
        if not WEBENGINE_AVAILABLE:
            err = QLabel("Isı haritası için PyQt6-WebEngine kütüphanesi yüklü değil.")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.chart_layout.addWidget(err)
            return

        # 2. Get Data & Map to existing viz generator
        # Note: We reuse 'VisualizationActions' logic or direct generator
        from ui.visualizations.project_analytics import generate_coverage_heatmap_html
        
        # We need to bridge StatisticsEngine data to generate_coverage_heatmap_html format
        matrix_data = self.engine.get_document_code_matrix()
        
        if not matrix_data or not matrix_data['documents']:
            err = QLabel("Isı haritası oluşturmak için yeterli veri (belge/kod) yok.")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.chart_layout.addWidget(err)
            return

        # Prepare Z values for the generator
        # generator expects: { 'documents': [], 'codes': [], 'z_values': [[..]] }
        z_values = [[0] * len(matrix_data['documents']) for _ in range(len(matrix_data['codes']))]
        
        # Map indices
        doc_map = {id: idx for idx, id in enumerate(matrix_data['doc_ids'])}
        code_map = {id: idx for idx, id in enumerate(matrix_data['code_ids'])}
        
        for entry in matrix_data['matrix']:
            d_idx = doc_map.get(entry['document_id'])
            c_idx = code_map.get(entry['code_id'])
            if d_idx is not None and c_idx is not None:
                z_values[c_idx][d_idx] = entry['count']

        data = {
            'documents': matrix_data['documents'],
            'codes': matrix_data['codes'],
            'z_values': z_values
        }
        
        html_path = generate_coverage_heatmap_html(data)
        
        # 3. Embed Browser
        browser = QWebEngineView()
        browser.setUrl(QUrl.fromLocalFile(os.path.abspath(html_path)))
        self.chart_layout.addWidget(browser)

    def _export_current(self):
        if hasattr(self, 'current_chart'):
            self.current_chart.export_image('png')
