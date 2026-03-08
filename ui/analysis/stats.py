"""
Statistical analysis actions for LexiScholar.
"""

from PyQt6.QtWidgets import QMessageBox
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class StatsActionsMixin:
    """Methods for triggering statistical analysis dialogs."""

    def _show_statistics(self):
        """Show code statistics in a central tab."""
        from ..statistics_dialogs import StatisticsWidget
        from analysis import AnalysisTools
        
        tab_name = "📊 Kod İstatistikleri"
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return

        analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao)
        widget = StatisticsWidget(analysis, self)
        self.add_analysis_tab(widget, tab_name, help_tooltip="Kod İstatistikleri: Kodların frekansı, yüzde yoğunluğu ve belge yayılımlarını nicel olarak analiz eder.", help_anchor="code-stats")
    
    def _show_word_frequency(self):
        """Show word frequency analysis in a central tab."""
        from ..statistics_dialogs import WordFrequencyWidget
        from analysis import AnalysisTools
        
        tab_name = "📈 Kelime Frekansı"
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return

        documents = self.doc_dao.get_all()
        analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao)
        widget = WordFrequencyWidget(analysis, documents, self)
        self.add_analysis_tab(widget, tab_name, help_tooltip="Kelime Frekansı: Metinlerde en çok tekrar eden sözcüklerin sayımını yaparak anahtar kelimeleri bulmanızı destekler.", help_anchor="word-frequency")
    
    def _show_cooccurrence(self):
        """Show code co-occurrence matrix in a central tab."""
        from ..statistics_dialogs import CooccurrenceWidget
        from analysis import AnalysisTools
        
        tab_name = "🔗 Birlikte Oluşum"
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return

        analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao)
        widget = CooccurrenceWidget(analysis, self)
        self.add_analysis_tab(widget, tab_name, help_tooltip="Birlikte Oluşum: Aynı belge içinde kodların ne sıklıkla birlikte geçtiğini matris biçiminde sergileyip olası tematik örüntüleri ortaya çıkarır.", help_anchor="cooccurrence")

    def _show_variable_statistics(self):
        """Show variable frequency distribution dialog."""
        from ..analysis_dialogs import VariableStatisticsDialog, VariableStatisticsResultDialog
        from analysis import AnalysisTools
        variables = self.var_dao.get_all()
        if not variables:
            show_info(self, "Bilgi", "Analiz için önce değişken tanımlamalısınız.")
            return
        dialog = VariableStatisticsDialog(variables, self)
        if dialog.exec():
            var_id, var_name = dialog.get_selected_variable()
            if var_id is not None:
                tab_name = f"📊 Değişken: {var_name}"
                for i in range(self.central_tabs.count()):
                    if self.central_tabs.tabText(i) == tab_name:
                        self.central_tabs.setCurrentIndex(i)
                        return

                analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao, var_dao=self.var_dao, var_value_dao=self.var_value_dao)
                stats_data = analysis.get_variable_statistics(var_id)
                from ..variable_dialogs_ext import VariableStatisticsResultWidget
                widget = VariableStatisticsResultWidget(var_name, stats_data, self)
                self.add_analysis_tab(widget, tab_name, help_tooltip="Değişken İstatistikleri: Katılımcılara atanan demografik özellikler gibi değişkenlerin istatistiksel dağılımlarını frekans tablolarıyla gösterir.", help_page="analysis_tools.html", help_anchor="variable-statistics")
