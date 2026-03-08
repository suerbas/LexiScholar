"""
Reusable Chart Widgets for LexiScholar
Uses Matplotlib with PyQt6 integration.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMenu, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from .modern_charts import generate_modern_chart_html

class LexiChartPage(QWebEnginePage):
    """Custom WebEnginePage to intercept console messages for data export."""
    export_ready = pyqtSignal(str)
    
    def javaScriptConsoleMessage(self, level, message, line, source):
        if message.startswith("CHART_EXPORT_READY:"):
            img_data = message.replace("CHART_EXPORT_READY:", "")
            self.export_ready.emit(img_data)
        # Call the default implementation to print to real console for debugging
        super().javaScriptConsoleMessage(level, message, line, source)

class LexiChartWidget(QWidget):
    """Base Chart Widget using QWebEngineView for modern interactive charts."""
    
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.title = title
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = QWebEngineView()
        self.page = LexiChartPage(self.browser)
        self.browser.setPage(self.page)
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.browser.customContextMenuRequested.connect(self._show_context_menu)
        
        # Connect to custom signal from page
        self.page.export_ready.connect(self._save_exported_image)
        
        self.layout.addWidget(self.browser)
        
    def _show_context_menu(self, pos):
        menu = QMenu(self)
        
        export_png = menu.addAction("Resmi Kaydet (.png)")
        export_png.triggered.connect(self.export_image)
        
        menu.exec(self.browser.mapToGlobal(pos))
        

    def export_image(self):
        """Trigger the JS export function."""
        self.browser.page().runJavaScript("window.exportImage();")

    def _save_exported_image(self, data_uri):
        """Save the base64 data URI to a file."""
        import base64
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Grafiği Kaydet", "lexischolar_grafik.png", "PNG Files (*.png)"
            )
            if path:
                # data:image/png;base64,...
                header, encoded = data_uri.split(",", 1)
                with open(path, "wb") as f:
                    f.write(base64.b64decode(encoded))
                QMessageBox.information(self, "Başarılı", f"Grafik başarıyla kaydedildi:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Grafik kaydedilemedi:\n{e}")

class LexiBarChart(LexiChartWidget):
    """Vertical or Horizontal Bar Chart using ApexCharts."""
    def update_data(self, labels, values, colors=None, horizontal=False, show_labels=True, show_legend=True):
        data = []
        for i, (label, val) in enumerate(zip(labels, values)):
            item = {"name": label, "value": val}
            if colors and i < len(colors):
                item["color"] = colors[i]
            data.append(item)
            
        options = {
            "title": self.title,
            "horizontal": horizontal,
            "show_labels": show_labels,
            "show_legend": show_legend
        }
        
        file_path = generate_modern_chart_html(data, "bar", options)
        self.browser.setUrl(QUrl.fromLocalFile(file_path))

class LexiPieChart(LexiChartWidget):
    """Pie or Donut Chart using ApexCharts."""
    def update_data(self, labels, values, colors=None, is_donut=False, show_labels=True, show_legend=True):
        data = []
        for i, (label, val) in enumerate(zip(labels, values)):
            item = {"name": label, "value": val}
            if colors and i < len(colors):
                item["color"] = colors[i]
            data.append(item)
            
        options = {
            "title": self.title,
            "show_labels": show_labels,
            "show_legend": show_legend
        }
        
        file_path = generate_modern_chart_html(data, "donut" if is_donut else "pie", options)
        self.browser.setUrl(QUrl.fromLocalFile(file_path))
