"""
Step 1: File Selection & Preview Page
"""

from PyQt6.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from ..styles import COLORS, get_color
from processors.excel_survey_processor import get_survey_info
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class PreviewPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard_ref = wizard
        self.setTitle("Adım 1: Veri Önizleme")
        self.setSubTitle("İçe aktarılacak Excel dosyasını seçin ve verilerin doğru yüklendiğini doğrulayın.")
        
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        self.btn_select = QPushButton(" Excel Dosyası Seç ")
        self.btn_select.setStyleSheet(f"QPushButton {{ background-color: {get_color('bg_hover')}; border: 1px solid {get_color('border_hover')}; border-radius: 4px; padding: 6px 16px; font-weight: 600; }} QPushButton:hover {{ background-color: {get_color('border')}; }}")
        self.btn_select.clicked.connect(self._select_file)
        
        self.lbl_file = QLabel("Dosya seçilmedi...")
        self.lbl_file.setStyleSheet(f"color: {get_color('text_secondary')}; font-style: italic;")
        
        top_layout.addWidget(self.btn_select)
        top_layout.addWidget(self.lbl_file, 1)
        layout.addLayout(top_layout)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Anket/Grup Adı:"))
        self.txt_survey_name = QLineEdit("Anket Verisi")
        self.txt_survey_name.setStyleSheet(f"padding: 5px; border: 1px solid {get_color('border_hover')}; border-radius: 4px;")
        self.registerField("survey_name*", self.txt_survey_name)
        name_layout.addWidget(self.txt_survey_name, 1)
        layout.addLayout(name_layout)
        
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("Çalışma Sayfası:"))
        self.cmb_sheets = QComboBox()
        self.cmb_sheets.setEnabled(False)
        self.cmb_sheets.currentIndexChanged.connect(self._on_sheet_changed)
        sheet_layout.addWidget(self.cmb_sheets, 1)
        layout.addLayout(sheet_layout)
        
        self.table = QTableWidget()
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.table)
        
        self.is_valid = False
        
    def isComplete(self):
        return self.is_valid and bool(self.txt_survey_name.text().strip())
        
    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Anket Dosyası Seç (Excel)", "", "Excel Dosyaları (*.xlsx *.xls)")
        if not path: return
        self.wizard_ref.file_path = path
        self.lbl_file.setText(path)
        try:
            self.wizard_ref.sheet_infos = get_survey_info(path)
            if not self.wizard_ref.sheet_infos: raise ValueError("Veri bulunamadı.")
            self.cmb_sheets.blockSignals(True)
            self.cmb_sheets.clear()
            for info in self.wizard_ref.sheet_infos:
                self.cmb_sheets.addItem(f"{info.name} ({info.row_count} satır)", info)
            self.cmb_sheets.blockSignals(False)
            self.cmb_sheets.setEnabled(True)
            self._on_sheet_changed(0)
        except Exception as e:
            show_error(self, "Hata", str(e))
            self.is_valid = False
            self.completeChanged.emit()
            
    def _on_sheet_changed(self, index):
        if index < 0: return
        info = self.wizard_ref.sheet_infos[index]
        self.wizard_ref.selected_sheet_info = info
        self.table.clear()
        self.table.setColumnCount(len(info.headers))
        self.table.setHorizontalHeaderLabels([str(h) for h in info.headers])
        
        import openpyxl, xlrd
        preview_data = []
        try:
            if self.wizard_ref.file_path.endswith('.xlsx'):
                wb = openpyxl.load_workbook(self.wizard_ref.file_path, read_only=True, data_only=True)
                ws = wb[info.name]
                for row in ws.iter_rows(min_row=2, max_row=501, values_only=True):
                    preview_data.append([str(cell) if cell is not None else "" for cell in row])
                wb.close()
            else:
                wb = xlrd.open_workbook(self.wizard_ref.file_path)
                ws = wb.sheet_by_name(info.name)
                for r_idx in range(1, min(ws.nrows, 501)):
                    preview_data.append([str(ws.cell_value(r_idx, c)).strip() for c in range(ws.ncols)])
        except Exception: pass
            
        self.wizard_ref.preview_data = preview_data
        self.table.setRowCount(len(preview_data))
        for r, row_data in enumerate(preview_data):
            for c, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.is_valid = True
        self.completeChanged.emit()
