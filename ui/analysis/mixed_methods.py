"""
Mixed methods analysis actions for LexiScholar.
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

class MixedMethodsActionsMixin:
    """Methods for crosstabs, quote matrices, and variable activations."""

    def _show_crosstabs(self):
        """Show crosstab analysis dialog and visualization."""
        from ..analysis_dialogs import CrosstabDialog
        from analysis import AnalysisTools
        from ..visualizations import generate_crosstab_html
        variables = self.var_dao.get_all()
        if not variables: return
        dialog = CrosstabDialog(variables, self)
        if dialog.exec():
            var_id, var_name = dialog.get_selected_variable()
            if var_id:
                analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao, var_dao=self.var_dao, var_value_dao=self.var_value_dao)
                codes, groups, matrix = analysis.get_crosstab_matrix(var_id)
                if not groups: return
                file_path = generate_crosstab_html(codes, groups, matrix)
                self._open_visualization(f"Çapraz Tablo: {var_name}", file_path)

    def _show_quotes_by_variables(self):
        """Show Quotes by Variables (Mixed Methods) analysis."""
        from ..mixed_methods import QuotesByVariablesDialog, QuotesByVariablesResultWidget
        from analysis import AnalysisTools
        codes = self.code_dao.get_all(); vars = self.var_dao.get_all()
        if not codes or not vars: return
        dialog = QuotesByVariablesDialog(codes, vars, self)
        if dialog.exec():
            c_ids, c_names, v_id, v_name = dialog.get_selection()
            if not c_ids: return
            analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao, var_dao=self.var_dao, var_value_dao=self.var_value_dao)
            grouped_data = analysis.get_quotes_by_variables(c_ids, v_id)
            
            # Use Tabbed Interface
            tab_name = f"Alıntılar: {v_name}"
            for i in range(self.central_tabs.count()):
                if self.central_tabs.tabText(i) == tab_name:
                    self.central_tabs.setCurrentIndex(i)
                    return

            widget = QuotesByVariablesResultWidget(c_names, v_name, grouped_data)
            subtitle = f"{v_name} • {grouped_data.get('total_segments', 0)} alıntı"
            self.add_analysis_tab(widget, tab_name, subtitle=subtitle, help_tooltip="Değişkenlere Göre Alıntılar: Katılımcıların cinsiyet, yaş gibi değişken özelliklerine göre alıntıları filtreler ve aynı kod bağlamında alt alta listeler.", help_page="mixed_methods.html", help_anchor="quotes-by-variables")

    def _show_activate_by_variables(self):
        """Show variable-based document activation wizard."""
        from ..mixed_methods import ActivateByVariablesDialog
        vars = self.var_dao.get_all()
        if not vars: return
        dialog = ActivateByVariablesDialog(vars, self.var_value_dao, self)
        if dialog.exec():
            v_id, op, val = dialog.get_rule()
            all_vals = self.var_value_dao.get_all_document_values()
            matches = set()
            for v in all_vals:
                if v['variable_id'] == v_id:
                    v_str = str(v['value']).strip()
                    if (op == "=" and v_str == val) or (op == "≠" and v_str != val) or (op == "∋" and val.lower() in v_str.lower()):
                        matches.add(v['document_id'])
            if hasattr(self, 'document_tree'):
                self.document_tree._set_all_active(False)
                for d_id in matches:
                    self.doc_dao.set_active(d_id, True)
                    if d_id in self.document_tree._doc_items:
                        it = self.document_tree._doc_items[d_id]
                        it.setCheckState(Qt.CheckState.Checked)
                        it.setForeground(QColor("#DC2626"))
                self.document_tree.document_activation_changed.emit(-1, True)

    def _show_quote_matrix(self):
        """Show the multi-code multi-variable Quote Matrix."""
        from ..mixed_methods import QuoteMatrixDialog, QuoteMatrixResultWidget
        from analysis import AnalysisTools
        codes = self.code_dao.get_all(); vars = self.var_dao.get_all()
        if not codes or not vars: return
        dialog = QuoteMatrixDialog(codes, vars, self)
        if dialog.exec():
            c_ids, v_id, v_name = dialog.get_selection()
            if not c_ids: return
            analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao, var_dao=self.var_dao, var_value_dao=self.var_value_dao)
            matrix_data = analysis.get_quote_matrix(c_ids, v_id)
            
            # Use Tabbed Interface
            tab_name = f"Matris: {v_name}"
            for i in range(self.central_tabs.count()):
                if self.central_tabs.tabText(i) == tab_name:
                    self.central_tabs.setCurrentIndex(i)
                    return

            widget = QuoteMatrixResultWidget(v_name, matrix_data)
            group_count = len(matrix_data.get("groups", []))
            subtitle = f"{v_name} • {len(c_ids)} kod • {group_count} grup"
            self.add_analysis_tab(widget, tab_name, subtitle=subtitle, help_tooltip="Alıntı Matrisi: Satırlarda kodlar, sütunlarda koşullar veya belgeler olacak şekilde alıntıları bir çapraz matris tablosu içinde görüntüler.", help_page="mixed_methods.html", help_anchor="quote-matrix")

    def _show_side_by_side(self):
        """Show Side-by-Side group comparison tool."""
        from ..mixed_methods import SideBySideWidget
        codes = self.code_dao.get_all(); vars = self.var_dao.get_all()
        if not codes or not vars: return
        
        # Check if tab already exists
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == "Yan Yana Görüntüleme":
                self.central_tabs.setCurrentIndex(i)
                return

        widget = SideBySideWidget(codes, vars, self.var_value_dao, self)
        if hasattr(self, '_on_segment_clicked'):
            widget.segment_clicked.connect(self._on_segment_clicked)
            
        self.add_analysis_tab(widget, "Yan Yana Görüntüleme", help_tooltip="Yan Yana Karşılaştırma: İki farklı analizi, belgeyi veya gruplanmış veriyi ekranda aynı hizada yan yana tutarak doğrudan kıyaslamanızı olanaklı kılar.", help_page="mixed_methods.html", help_anchor="side-by-side")

    def _show_variance_analysis(self):
        """Show One-Way ANOVA analysis dialog."""
        from ..mixed_methods import VarianceAnalysisDialog, VarianceResultWidget
        from analysis import AnalysisTools
        from ..common_ui import show_warning, show_error
        codes = self.code_dao.get_all(); vars = self.var_dao.get_all()
        if not codes or not vars: 
            show_warning(self, "Uyarı", "Analiz için en az bir kod ve bir değişken gereklidir.")
            return
            
        dialog = VarianceAnalysisDialog(codes, vars, self)
        if dialog.exec():
            c_id, v_id, c_name, v_name = dialog.get_selection()
            if not c_id: return
            
            analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao, var_dao=self.var_dao, var_value_dao=self.var_value_dao)
            result = analysis.get_variance_analysis(c_id, v_id)
            
            if 'error' in result:
                show_error(self, "Analiz Hatası", result['error'])
            else:
                # Use Tabbed Interface
                tab_name = f"ANOVA: {c_name} x {v_name}"
                for i in range(self.central_tabs.count()):
                    if self.central_tabs.tabText(i) == tab_name:
                        self.central_tabs.setCurrentIndex(i)
                        return

                widget = VarianceResultWidget(result, c_name, v_name)
                subtitle = f"Kod: {c_name} • Değişken: {v_name}"
                self.add_analysis_tab(widget, tab_name, subtitle=subtitle, help_tooltip="Varyans Analizi (ANOVA): Bir nitel temanın dağılım sıklığının, kategorik değişken sınıfları arasında istatistiksel bir anlam taşıyıp taşımadığını test eder.", help_page="mixed_methods.html", help_anchor="variance-analysis")
