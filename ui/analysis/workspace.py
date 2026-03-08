"""
Workspace and management actions for LexiScholar (Variables, Memos, IRR, etc).
"""

from PyQt6.QtWidgets import QMessageBox, QInputDialog
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class WorkspaceActionsMixin:
    """Methods for managing the research workspace."""

    def _show_variable_manager(self):
        """Show global variable management dialog."""
        from ..variable_dialogs import VariableManagerDialog
        VariableManagerDialog(self.var_dao, self).exec()
        
    def _show_data_editor(self):
        """Show the spreadsheet-like Data Editor in a tab."""
        tab_name = "📝 Veri Editörü"
        # Activate if already open
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return

        from ..variable_dialogs import DataEditorWidget
        widget = DataEditorWidget(self.doc_dao, self.var_dao, self.var_value_dao, self)
        
        help_txt = ("<b>Veri Editörü (Değişkenler):</b> Projedeki tüm belgelerin değişken değerlerini "
                    "(Yaş, Cinsiyet vb.) bir Excel tablosu gibi topluca görmenizi ve düzenlemenizi sağlar. "
                    "Hücrelere çift tıklayarak verileri güncelleyebilirsiniz.")
        
        self.add_analysis_tab(widget, tab_name, 
                              help_tooltip=help_txt, 
                              help_page="data_management.html", 
                              help_anchor="variable-editor")
        self.statusbar.showMessage("Veri Editörü açıldı.")

    def _show_memo_manager(self, focus_search=False):
        """Show the Memo Manager in a central tab."""
        from ..memo_manager import MemoManagerWidget
        
        tab_name = "📝 Memo Yöneticisi"
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return

        widget = MemoManagerWidget(self, self.memo_dao, focus_search=focus_search)
        
        help_txt = ("<b>Memo Yöneticisi:</b> Proje boyunca aldığınız tüm notları (memoları) tek bir yerden "
                    "yönetmenizi, aramanızı ve etiketlemenizi sağlar. Teorik notlarınızı veya metodolojik "
                    "kararlarınızı burada saklayabilirsiniz.")
        
        self.add_analysis_tab(widget, tab_name, 
                              help_tooltip=help_txt, 
                              help_page="data_management.html", 
                              help_anchor="memos")
        self.statusbar.showMessage("Memo Yöneticisi açıldı.")
        
    def _create_free_memo(self):
        """Create a new free memo."""
        from ..modern_dialogs import ModernInputDialog
        title, ok = ModernInputDialog.get_input(self, "Yeni Serbest Memo", "Memo Başlığı:")
        if ok and title:
            self.memo_dao.create(content="", title=title)
            self._show_memo_manager()


    def _show_merge_dialog(self):
        """Show code merge dialog."""
        from ..analysis_dialogs import CodeMergeDialog
        codes = self.code_dao.get_all()
        if len(codes) < 2: return
        dialog = CodeMergeDialog(codes, self)
        if dialog.exec():
            src_c, tgt_c = dialog.get_merge_data()
            src_id = src_c['id'] if src_c else None
            tgt_id = tgt_c['id'] if tgt_c else None
            if src_id and tgt_id and src_id != tgt_id:
                source_segments = self.segment_dao.get_by_code(src_id)
                for seg in source_segments: self.segment_dao.update_code(seg['id'], tgt_id)
                self.code_dao.delete(src_id)
                codes = self.code_dao.get_all()
                self.code_tree.populate_codes(codes)
                if self.retrieved_segments._current_code_id == tgt_id:
                    self.retrieved_segments.set_code(tgt_id, tgt_c['name'], self.segment_dao.get_by_code(tgt_id))
                self.statusbar.showMessage(f"✅ {len(source_segments)} segment birleştirildi")

    def _show_irr_analysis(self):
        """Show the Inter-Rater Reliability analysis dialog."""
        from ..irr_dialogs import IRRSelectionDialog, IRRResultDialog
        from analysis import IRREngine
        from ..common_ui import show_info
        coders = self.coder_dao.get_all()
        if len(coders) < 2:
            show_info(
                self, 
                "Analist Uyumu", 
                "Güvenirlik analizi (IRR) yapabilmek için projede en az 2 farklı kodlayıcının tanımlanmış ve kodlama yapmış olması gerekir.\n\n"
                "Giriş sekmesinden 'Kodlayıcı Yönetimi'ne girerek yeni kodlayıcı ekleyebilir veya başkalarının yaptığı kodlamaları projeye dâhil edebilirsiniz."
            )
            return
        documents = self.doc_dao.get_all(); codes = self.code_dao.get_all()
        dialog = IRRSelectionDialog(coders, documents, codes, self)
        if dialog.exec():
            sel = dialog.get_selection()
            engine = IRREngine(self.doc_dao, self.segment_dao)
            res = engine.calculate_reliability(sel['doc_ids'], sel['coder1_id'], sel['coder2_id'], sel['code_ids'])
            
            tab_name = f"🤝 IRR: {sel['coder1_name']} vs {sel['coder2_name']}"
            for i in range(self.central_tabs.count()):
                if self.central_tabs.tabText(i) == tab_name:
                    self.central_tabs.setCurrentIndex(i)
                    return

            from ..irr_dialogs import IRRResultWidget
            widget = IRRResultWidget(res, sel, {c['id']: c for c in codes}, self)
            self.add_analysis_tab(widget, tab_name, help_tooltip="Uzlaşma (IRR): İki kodlayıcının metinleri ne derece benzer kodladığını Cohen's Kappa ve örtüşme oranıyla ölçer.", help_page="teamwork_reliability.html", help_anchor="irr-analysis")

    def _show_comparison(self):
        """Show Document Comparison Tool."""
        from ..comparison_tool import ComparisonToolWidget
        # Check if tab already exists
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == "Karşılaştırma":
                self.central_tabs.setCurrentIndex(i)
                return

        widget = ComparisonToolWidget(self.db_path)
        self.add_analysis_tab(widget, "Karşılaştırma", help_tooltip="Belge Karşılaştırma: Farklı belgelerdeki kodlamaları yan yana getirerek tematik farkları ve benzerlikleri detaylıca incelemenizi sağlar.", help_page="analysis_tools.html", help_anchor="comparison")
        
    def _show_summary_grid(self):
        """Show Summary Grid for analysis."""
        from ..summary_grid import SummaryGridWidget
        
        tab_name = "Özet Tablosu"
        # Check if tab exists
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return
            
        widget = SummaryGridWidget(self.db_path)
        self.add_analysis_tab(widget, tab_name, help_tooltip="Özet Tablosu: Araştırmadaki belgeler ve kodlara ait özetleri çapraz matris üzerinden okuyarak bulguları sentezlemenizi sağlar.", help_page="analysis_tools.html", help_anchor="summary-grid")

    def _on_query_requested(self):
        """Show Advanced Boolean Query Builder."""
        from ..query_builder import QueryBuilderDialog
        codes = self.code_dao.get_all()
        if not codes: return
        dialog = QueryBuilderDialog(codes, self)
        if dialog.exec():
            params = dialog.get_query_parameters()
            results = self.segment_dao.get_by_boolean_query(params['and_ids'], params['or_ids'], params['not_ids'], doc_scope=params['doc_scope'])
            if results:
                self.retrieved_segments.header.title_label.setText(f"🔍 Sorgu Sonucu ({len(results)} segment)")
                self.retrieved_segments.populate_segments(results)
                self.statusbar.showMessage(f"✅ Sorgu tamamlandı: {len(results)} sonuç")
            else:
                show_info(self, "Sonuç", "Kriterlere uygun segment bulunamadı.")
