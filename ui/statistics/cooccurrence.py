"""
Code Co-occurrence Widget and Dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices
from ..styles import TABLE_STYLE, get_color
from ..common.modern_dialog import ModernBaseDialog
from ..common_ui import show_error

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
        
        info = QLabel("Aynı belgede birlikte görünen kod çiftlerini gösterir.")
        info.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(info)
        
        self.table = QTableWidget()
        self.table.setStyleSheet(self._table_style() + f"""
            QTableWidget {{
                selection-background-color: #EEF2FF;
                selection-color: #1E293B;
            }}
            QTableWidget::item:hover {{ background-color: {get_color('bg_main')}; color: #1E293B; }}
            QTableWidget::item:selected {{ background-color: #EEF2FF; color: #1E293B; }}
        """)
        layout.addWidget(self.table)
        
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
        
        headers = [c['name'] for c in codes]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setVerticalHeaderLabels(headers)
        
        for i in range(n):
            for j in range(n):
                value = matrix[i][j]
                item = QTableWidgetItem(str(value) if value > 0 else "")
                
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
            from ..visualizations import generate_cooccurrence_graph
            file_path = generate_cooccurrence_graph(self.codes, self.matrix)
            
            parent = self.parent()
            if hasattr(parent, '_open_visualization'):
                dlg = parent._open_visualization("Kod İlişki Grafiği", file_path)
                if dlg:
                    edge_count = sum(1 for i in range(len(self.matrix)) for j in range(i + 1, len(self.matrix[i])) if self.matrix[i][j] > 0)
                    dlg.add_graph_controls(node_count=len(self.codes), edge_count=edge_count)
                    
                    for i in range(parent.central_tabs.count()):
                        if parent.central_tabs.tabText(i) == "Kod İlişki Grafiği":
                            container = parent.central_tabs.widget(i)
                            from ..panel_header import PanelHeader
                            header = container.findChild(PanelHeader)
                            if header:
                                header.set_help("Kod İlişki Grafiği hakkında bilgi", "analysis_tools.html", "graph")
                            break
                            
                from PyQt6.QtWidgets import QDialog
                if isinstance(self.window(), QDialog):
                    self.window().accept()
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
        
        header_layout = QHBoxLayout()
        icon = QLabel("🔗")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel("Kod Birlikte Oluşumu")
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

        self.widget = CooccurrenceWidget(analysis_tools, self)
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
