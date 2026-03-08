"""
Survey Import Wizard Sub-package for LexiScholar
Assembled from modular wizard pages.
"""

from PyQt6.QtWidgets import QWizard, QMessageBox
from PyQt6.QtCore import pyqtSignal
from .preview_page import PreviewPage
from .data_types_page import DataTypesPage
from .ids_page import DocumentIDsPage
from ..styles import get_color
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class SurveyImportWizard(QWizard):
    """
    3-Step Wizard to import Excel data.
    """
    import_requested = pyqtSignal(str, str, dict, str, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anket İçe Aktar (Excel)")
        self.resize(1000, 700)
        self.setStyleSheet(f"QWizard {{ background-color: {get_color('bg_panel')}; }} QLabel {{ color: {get_color('text_primary')}; }}")
        
        # Shared Data
        self.file_path = ""
        self.sheet_infos = []
        self.selected_sheet_info = None
        self.preview_data = []
        
        # Setup Pages
        self.page_preview = PreviewPage(self)
        self.page_types = DataTypesPage(self)
        self.page_ids = DocumentIDsPage(self)
        
        self.addPage(self.page_preview)
        self.addPage(self.page_types)
        self.addPage(self.page_ids)
        
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveCustomButton1, False)
        
        # Translations
        self.setButtonText(QWizard.WizardButton.NextButton, "İleri >")
        self.setButtonText(QWizard.WizardButton.BackButton, "< Geri")
        self.setButtonText(QWizard.WizardButton.FinishButton, "İçe Aktar")
        self.setButtonText(QWizard.WizardButton.CancelButton, "İptal")
        
    def accept(self):
        configs = self.page_types.get_configurations()
        doc_name_col_idx = self.page_ids.get_doc_name_column()
        group_col_idx = self.page_ids.get_group_column()
        
        has_doc_name = False
        has_data = False
        final_config = {}
        
        for col_idx, conf in configs.items():
            if conf["type"] == "IGNORE": continue
            has_data = True
            if conf.get("is_doc_name"): has_doc_name = True
            if self.page_ids.use_column_for_id() and col_idx == doc_name_col_idx:
                conf["is_doc_name"] = True
                has_doc_name = True
            if self.page_ids.use_grouping() and col_idx == group_col_idx:
                conf["is_group_name"] = True
            final_config[col_idx] = conf
            
        if not has_data:
            show_warning(self, "Uyarı", "İçe aktarılacak hiçbir veri seçmediniz!")
            return
        if not has_doc_name and not self.page_ids.use_auto_ids():
             show_warning(self, "Uyarı", "Geçerli bir belge adlandırma yöntemi seçilmedi.")
             return
             
        survey_name = self.page_preview.txt_survey_name.text() or "Anket Verisi"
        include_headers = self.page_types.chk_include_headers.isChecked()
        self.import_requested.emit(self.file_path, self.selected_sheet_info.name, final_config, survey_name, include_headers)
        super().accept()
