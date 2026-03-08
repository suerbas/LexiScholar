"""
Step 2: Data Types (Qualitative/Quantitative) Page
"""

from PyQt6.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QWidget, QRadioButton
)
from PyQt6.QtCore import Qt
import re

class DataTypesPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard_ref = wizard
        self.setTitle("Adım 2: Veri Türleri")
        self.setSubTitle("Hangi sütunlarınızın nitel (metin) veya nicel (değişken) olarak içe aktarılacağını seçin.")
        
        layout = QVBoxLayout(self)
        
        info_layout = QHBoxLayout()
        self.lbl_total = QLabel("<b>Sorular: 0</b>")
        self.lbl_nitel_count = QLabel("<b>Nitel:</b> 0")
        self.lbl_nicel_count = QLabel("<b>Nicel:</b> 0")
        
        self.btn_all_import = QPushButton("☑ Tümünü Seç")
        self.btn_all_import.clicked.connect(lambda: self._set_all_import(True))
        self.btn_none_import = QPushButton("☐ Tümünü Kaldır")
        self.btn_none_import.clicked.connect(lambda: self._set_all_import(False))
        
        self.chk_include_headers = QCheckBox("Soruları belge içeriğine dahil et")
        
        info_layout.addWidget(self.lbl_total)
        info_layout.addWidget(self.lbl_nitel_count)
        info_layout.addWidget(self.lbl_nicel_count)
        info_layout.addStretch()
        info_layout.addWidget(self.chk_include_headers)
        info_layout.addWidget(self.btn_all_import)
        info_layout.addWidget(self.btn_none_import)
        layout.addLayout(info_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["İçe Aktar", "Belge Adı", "Sorular (Sütunlar)", "Veri Önizlemesi", "Nitel (Metin)", "Nicel (Değişken)"])
        layout.addWidget(self.table)
        
        self.controls_map = {}
        
    def initializePage(self):
        info = self.wizard_ref.selected_sheet_info
        if not info: return
        self.table.setRowCount(0)
        self.controls_map.clear()
        from PyQt6.QtWidgets import QButtonGroup, QRadioButton
        self.id_group = QButtonGroup(self)
        preview_data = self.wizard_ref.preview_data
        guessed_id_idx = -1
        for col_idx, header_name in enumerate(info.headers):
            h_low = str(header_name).lower()
            if guessed_id_idx == -1 and any(x in h_low for x in ["katılımcı", "id", "isim", "ad", "no"]):
                guessed_id_idx = col_idx

        for col_idx, header_name in enumerate(info.headers):
            self.table.insertRow(col_idx)
            header_str = str(header_name)
            
            chk_import = QCheckBox(); chk_import.setChecked(True)
            self._set_cell_widget(col_idx, 0, chk_import)
            
            rd_id = QRadioButton(); self.id_group.addButton(rd_id, col_idx)
            self._set_cell_widget(col_idx, 1, rd_id)
            if col_idx == guessed_id_idx: rd_id.setChecked(True)
            
            self.table.setItem(col_idx, 2, QTableWidgetItem(header_str))
            prev_txt = preview_data[0][col_idx] if preview_data else ""
            self.table.setItem(col_idx, 3, QTableWidgetItem(prev_txt))
            
            chk_nitel = QCheckBox()
            self._set_cell_widget(col_idx, 4, chk_nitel)
            
            nc_widget = QWidget(); nc_layout = QHBoxLayout(nc_widget); chk_nicel = QCheckBox(); cmb_type = QComboBox()
            cmb_type.addItems(["Metin", "Tamsayı", "Ondalık", "Tarih/Saat"]); cmb_type.setEnabled(False)
            nc_layout.addWidget(chk_nicel); nc_layout.addWidget(cmb_type)
            self.table.setCellWidget(col_idx, 5, nc_widget)
            
            chk_nicel.toggled.connect(lambda checked, c=cmb_type: c.setEnabled(checked))
            for c in [chk_nitel, chk_nicel, chk_import]: c.toggled.connect(self._update_counts)
            
            h_lower = header_str.lower()
            if col_idx == guessed_id_idx or any(x in h_lower for x in ["yaş", "cinsiyet", "eğitim", "gelir", "gender"]):
                chk_nicel.setChecked(True)
                if "yaş" in h_lower or "puan" in h_lower: cmb_type.setCurrentIndex(1)
            elif "?" in h_lower or any(x in h_lower for x in ["soru", "neden", "öneri"]) or len(header_str) > 50:
                chk_nitel.setChecked(True)
            else: chk_nicel.setChecked(True)
                
            self.controls_map[col_idx] = {"chk": chk_import, "rd_id": rd_id, "chk_nitel": chk_nitel, "chk_nicel": chk_nicel, "cmb_type": cmb_type, "header": header_str}
            
        self._update_counts()

    def _set_cell_widget(self, row, col, widget):
        container = QWidget(); layout = QHBoxLayout(container); layout.addWidget(widget); layout.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.setContentsMargins(0,0,0,0)
        self.table.setCellWidget(row, col, container)

    def _update_counts(self):
        n_nitel = sum(1 for c in self.controls_map.values() if c["chk"].isChecked() and c["chk_nitel"].isChecked())
        n_nicel = sum(1 for c in self.controls_map.values() if c["chk"].isChecked() and c["chk_nicel"].isChecked())
        self.lbl_nitel_count.setText(f"<b>Nitel:</b> {n_nitel}"); self.lbl_nicel_count.setText(f"<b>Nicel:</b> {n_nicel}")

    def get_configurations(self):
        configs = {}
        for col_idx, controls in self.controls_map.items():
            is_doc_name = controls["rd_id"].isChecked()
            if not controls["chk"].isChecked() and not is_doc_name:
                configs[col_idx] = {"type": "IGNORE"}; continue
            
            is_nitel, is_nicel = controls["chk_nitel"].isChecked(), controls["chk_nicel"].isChecked()
            conf = {"is_doc_name": True} if is_doc_name else {}
            header = controls["header"]
            
            if is_nitel and is_nicel: conf.update({"type": "BOTH", "name": self._get_short_name(header, col_idx+1), "org_name": header, "var_type": controls["cmb_type"].currentText()})
            elif is_nitel: conf.update({"type": "CODED_TEXT", "name": self._get_short_name(header, col_idx+1), "org_name": header})
            elif is_nicel: conf.update({"type": "VARIABLE", "name": self._get_short_name(header, col_idx+1, 30), "var_type": controls["cmb_type"].currentText()})
            elif is_doc_name: conf["type"] = "DOC_NAME"
            else: configs[col_idx] = {"type": "IGNORE"}; continue
            configs[col_idx] = conf
        return configs

    def _get_short_name(self, text, index, max_len=55):
        text = text.strip()
        if not text: return f"Sütun {index}"
        if len(text) <= max_len: return text
        match = re.match(r'^(\d+)[\.\-\)]?\s*(.*)', text)
        if match: return f"Soru {match.group(1)} ({match.group(2)[:max_len-15]}...)"
        return f"{text[:max_len-3]}..."

    def _set_all_import(self, checked):
        for c in self.controls_map.values(): c["chk"].setChecked(checked)
