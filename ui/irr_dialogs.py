"""IRR analysis dialogs for LexiScholar."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QWidget,
    QMessageBox, QToolButton
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class IRRSelectionDialog(QDialog):
    """Dialog to select coders, documents, and codes for IRR analysis."""
    def __init__(self, coders, documents, codes, parent=None):
        super().__init__(parent)
        self.coders = coders
        self.documents = documents
        self.codes = codes
        
        self.setWindowTitle("Güvenirlik Analizi (IRR) Seçimi")
        self.setMinimumWidth(500)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with Title and Help
        header_layout = QHBoxLayout()
        header_lbl = QLabel("Analiz Kapsamı:")
        header_lbl.setStyleSheet("font-weight: bold; color: #1e293b;")
        
        # Help Button - Emoji for maximum compatibility
        self.btn_help = QPushButton("💡")
        self.btn_help.setToolTip("Analist Uyumu (IRR) hakkında yardım")
        self.btn_help.setFixedSize(28, 28)
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setStyleSheet("QPushButton { border: none; background: transparent; font-size: 14px; } QPushButton:hover { background: #f1f5f9; border-radius: 4px; }")
        self.btn_help.clicked.connect(self._show_help)
        
        header_layout.addWidget(header_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_help)
        layout.addLayout(header_layout)
        
        # Coders Selection
        layout.addWidget(QLabel("Karşılaştırılacak Kodlayıcılar:"))
        coder_layout = QHBoxLayout()
        
        self.coder1_combo = QComboBox()
        self.coder2_combo = QComboBox()
        
        for c in self.coders:
            self.coder1_combo.addItem(c['name'], c['id'])
            self.coder2_combo.addItem(c['name'], c['id'])
            
        if self.coder2_combo.count() > 1:
            self.coder2_combo.setCurrentIndex(1)
            
        coder_layout.addWidget(self.coder1_combo)
        coder_layout.addWidget(QLabel("vs"))
        coder_layout.addWidget(self.coder2_combo)
        layout.addLayout(coder_layout)
        
        # Documents Selection
        layout.addWidget(QLabel("Belgeler (Hepsini seçmek için CTRL+A):"))
        self.doc_list = QListWidget()
        self.doc_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for d in self.documents:
            self.doc_list.addItem(d['title'])
            self.doc_list.item(self.doc_list.count()-1).setData(Qt.ItemDataRole.UserRole, d['id'])
            self.doc_list.item(self.doc_list.count()-1).setSelected(True)
        layout.addWidget(self.doc_list)
        
        # Codes Selection
        layout.addWidget(QLabel("Kodlar (Opsiyonel - Filtrelemek için seçin):"))
        self.code_list = QListWidget()
        self.code_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for c in self.codes:
            self.code_list.addItem(c['name'])
            self.code_list.item(self.code_list.count()-1).setData(Qt.ItemDataRole.UserRole, c['id'])
            self.code_list.item(self.code_list.count()-1).setSelected(True)
        layout.addWidget(self.code_list)
        
        # Buttons
        btns = QHBoxLayout()
        
        btn_run = QPushButton("Analizi Çalıştır")
        btn_run.clicked.connect(self._validate_and_accept)
        btn_run.setStyleSheet("font-weight: bold; padding: 6px 24px;")
        
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_run)
        layout.addLayout(btns)
        
    def _show_help(self):
        """Show contextual help for IRR analysis."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        help_path = os.path.join(base_dir, "docs", "encyclopedia", "teamwork_reliability.html")
        if os.path.exists(help_path):
            url = QUrl.fromLocalFile(help_path)
            url.setFragment("irr-analysis")
            QDesktopServices.openUrl(url)
        
    def _validate_and_accept(self):
        if self.coder1_combo.currentData() == self.coder2_combo.currentData():
            show_warning(self, "Hata", "Lütfen iki farklı kodlayıcı seçin.")
            return
        
        if not self.doc_list.selectedItems():
            show_warning(self, "Hata", "Lütfen en az bir belge seçin.")
            return
            
        self.accept()
        
    def get_selection(self):
        return {
            'coder1_id': self.coder1_combo.currentData(),
            'coder1_name': self.coder1_combo.currentText(),
            'coder2_id': self.coder2_combo.currentData(),
            'coder2_name': self.coder2_combo.currentText(),
            'doc_ids': [item.data(Qt.ItemDataRole.UserRole) for item in self.doc_list.selectedItems()],
            'code_ids': [item.data(Qt.ItemDataRole.UserRole) for item in self.code_list.selectedItems()]
        }

class IRRResultWidget(QWidget):
    """Widget to display IRR results in a tabbed interface."""
    def __init__(self, results, selection, code_map, parent=None):
        super().__init__(parent)
        self.results = results
        self.selection = selection
        self.code_map = code_map
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Summary
        summary = QWidget()
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(8)
        
        title_lbl = QLabel("📈 Analist Uyumu (IRR) Sonuçları")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        summary_layout.addWidget(title_lbl)
        
        comparison_lbl = QLabel(f"<b>Karşılaştırma:</b> {self.selection['coder1_name']} vs {self.selection['coder2_name']}")
        comparison_lbl.setStyleSheet("font-size: 13px; color: #334155;")
        summary_layout.addWidget(comparison_lbl)
        
        # Kappa Interpretation
        kappa = self.results.get('kappa', 0)
        interpretation = "Zayıf"
        k_color = "#EF4444" # Red
        if kappa > 0.8: interpretation = "Mükemmel"; k_color = "#10B981" # Green
        elif kappa > 0.6: interpretation = "Önemli (Substantial)"; k_color = "#059669"
        elif kappa > 0.4: interpretation = "Orta (Moderate)"; k_color = "#F59E0B"
        elif kappa > 0.2: interpretation = "Düşük"; k_color = "#D97706"
        
        kappa_label = QLabel(f"<b>Cohen's Kappa:</b> <span style='color: {k_color};'>{kappa:.2f} ({interpretation})</span>")
        kappa_label.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(kappa_label)
        
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel(f"<b>Genel Yüzde Uyum:</b> %{self.results['overall_percent']:.2f}"))
        stats_layout.addWidget(QLabel(f"<b>Toplam Kodlama Olayı:</b> {self.results['total_instances']}"))
        stats_layout.addWidget(QLabel(f"<b>Toplam Uzlaşı:</b> {self.results['total_agreements']}"))
        stats_layout.addStretch()
        summary_layout.addLayout(stats_layout)
        
        layout.addWidget(summary)
        
        # Tabs for details
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #E2E8F0; border-radius: 4px; }")
        
        # Per-Code Table
        code_tab = QWidget()
        code_layout = QVBoxLayout(code_tab)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Kod Adı", "Olay Sayısı", "Uzlaşı", "Uyum %"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { border: none; }")
        
        per_code = self.results['per_code']
        self.table.setRowCount(len(per_code))
        
        for i, (code_id, stats) in enumerate(per_code.items()):
            code_name = self.code_map.get(code_id, {}).get('name', f'ID: {code_id}')
            self.table.setItem(i, 0, QTableWidgetItem(code_name))
            self.table.setItem(i, 1, QTableWidgetItem(str(stats['instances'])))
            self.table.setItem(i, 2, QTableWidgetItem(str(stats['agreements'])))
            self.table.setItem(i, 3, QTableWidgetItem(f"%{stats['percent']:.2f}"))
            
        code_layout.addWidget(self.table)
        tabs.addTab(code_tab, "Kod Bazlı Detaylar")
        
        layout.addWidget(tabs)
        self.setStyleSheet("background-color: #FFFFFF;")

class IRRResultDialog(QDialog):
    """Standalone dialog wrapper for IRRResultWidget."""
    def __init__(self, results, selection, code_map, parent=None):
        super().__init__(parent)
        self.setWindowTitle("IRR Analiz Sonuçları")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.widget = IRRResultWidget(results, selection, code_map, self)
        layout.addWidget(self.widget)
        
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
