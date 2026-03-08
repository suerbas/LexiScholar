"""
Step 3: Document IDs & Groups Page
"""

from PyQt6.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QRadioButton, 
    QCheckBox, QFrame, QTreeWidget, QTreeWidgetItem, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ..styles import get_color

class DocumentIDsPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard_ref = wizard
        self.setTitle("Adım 3: Vaka ID'leri ve Gruplar")
        self.setSubTitle("Vakalarınıza nasıl isim vereceğinizi ve bunları belge grupları halinde sınıflandırıp sınıflandırmayacağınızı seçin.")
        
        main_layout = QHBoxLayout(self)
        
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel); left_layout.setAlignment(Qt.AlignmentFlag.AlignTop); left_layout.setSpacing(25)
        
        id_group = QWidget(); id_layout = QVBoxLayout(id_group); id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.addWidget(QLabel("<b>Vaka ID'leri (Belge Adı)</b>"))
        
        self.rd_use_col = QRadioButton("Sütundaki vaka ID'lerini kullan:")
        self.cmb_id_col = QComboBox(); self.cmb_id_col.setEnabled(False); self.cmb_id_col.setMinimumWidth(150)
        col_layout = QHBoxLayout(); col_layout.addWidget(self.rd_use_col); col_layout.addWidget(self.cmb_id_col); col_layout.addStretch()
        id_layout.addLayout(col_layout)
        
        self.rd_auto = QRadioButton("Benzersiz vaka ID'leri oluşturun (Katılımcı 1, Katılımcı 2 vb.)"); self.rd_auto.setChecked(True)
        id_layout.addWidget(self.rd_auto); left_layout.addWidget(id_group)
        
        group_group = QWidget(); group_layout = QVBoxLayout(group_group); group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.addWidget(QLabel("<b>Gruplar (Klasörler)</b>"))
        self.chk_group = QCheckBox("Vakaları şu sütuna göre gruplandır:")
        self.cmb_group_col = QComboBox(); self.cmb_group_col.setEnabled(False); self.cmb_group_col.setMinimumWidth(150)
        g_col_layout = QHBoxLayout(); g_col_layout.addWidget(self.chk_group); g_col_layout.addWidget(self.cmb_group_col); g_col_layout.addStretch()
        group_layout.addLayout(g_col_layout); left_layout.addWidget(group_group)
        
        right_panel = QFrame(); right_panel.setStyleSheet(f"QFrame {{ background-color: {get_color('bg_main')}; border: 1px solid {get_color('border')}; border-radius: 6px; }}")
        right_layout = QVBoxLayout(right_panel); right_layout.addWidget(QLabel("<b>Ağaç Ön İzleme</b>"))
        self.tree_preview = QTreeWidget(); self.tree_preview.setHeaderHidden(True); right_layout.addWidget(self.tree_preview)
        
        main_layout.addWidget(left_panel, 6); main_layout.addWidget(right_panel, 4)
        
        self.rd_use_col.toggled.connect(lambda c: self.cmb_id_col.setEnabled(c))
        self.chk_group.toggled.connect(lambda c: self.cmb_group_col.setEnabled(c))
        for w in [self.rd_use_col, self.rd_auto, self.chk_group]: w.toggled.connect(self._update_preview)
        self.cmb_id_col.currentIndexChanged.connect(self._update_preview)
        self.cmb_group_col.currentIndexChanged.connect(self._update_preview)
        
    def initializePage(self):
        info = self.wizard_ref.selected_sheet_info
        if not info: return
        self.cmb_id_col.blockSignals(True); self.cmb_group_col.blockSignals(True)
        self.cmb_id_col.clear(); self.cmb_group_col.clear()
        for i, h in enumerate(info.headers):
            self.cmb_id_col.addItem(str(h), i); self.cmb_group_col.addItem(str(h), i)
        configs = self.wizard_ref.page_types.get_configurations()
        found = False
        for col_idx, conf in configs.items():
            if conf.get("is_doc_name"): self.cmb_id_col.setCurrentIndex(col_idx); self.rd_use_col.setChecked(True); found = True; break
        if not found:
            for i, h in enumerate(info.headers):
                if any(x in str(h).lower() for x in ["id", "no", "ad", "isim"]): self.cmb_id_col.setCurrentIndex(i); self.rd_use_col.setChecked(True); break
        self.cmb_id_col.blockSignals(False); self.cmb_group_col.blockSignals(False)
        self._update_preview()
        
    def _update_preview(self):
        self.tree_preview.clear()
        survey_name = self.wizard_ref.page_preview.txt_survey_name.text() or "Anket Verisi"
        root = QTreeWidgetItem([survey_name]); self.tree_preview.addTopLevelItem(root)
        if not self.wizard_ref.preview_data: return
        use_id, id_idx = self.rd_use_col.isChecked(), self.cmb_id_col.currentData()
        use_grp, grp_idx = self.chk_group.isChecked(), self.cmb_group_col.currentData()
        nodes = {survey_name: root}
        for idx, row in enumerate(self.wizard_ref.preview_data[:15]):
            doc_name = str(row[id_idx]).strip() if use_id and id_idx < len(row) else f"Katılımcı {idx+1}"
            if not doc_name: doc_name = f"Belge {idx+1}"
            parent = root
            if use_grp and grp_idx < len(row):
                grp = str(row[grp_idx]).strip() or "Belirsiz"
                if grp not in nodes:
                    nodes[grp] = QTreeWidgetItem([grp]); root.addChild(nodes[grp])
                parent = nodes[grp]
            parent.addChild(QTreeWidgetItem([doc_name]))
        self.tree_preview.expandAll()

    def use_column_for_id(self): return self.rd_use_col.isChecked()
    def use_auto_ids(self): return self.rd_auto.isChecked()
    def get_doc_name_column(self): return self.cmb_id_col.currentData() if self.rd_use_col.isChecked() else -1
    def use_grouping(self): return self.chk_group.isChecked()
    def get_group_column(self): return self.cmb_group_col.currentData() if self.chk_group.isChecked() else -1
