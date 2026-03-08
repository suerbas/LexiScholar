"""
Search and auto-coding actions for LexiScholar.
"""

from PyQt6.QtWidgets import QMessageBox
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class SearchActionsMixin:
    """Methods for searching and auto-coding."""

    def _show_search_dialog(self):
        """Show the search and auto-coding dialog."""
        from ..search import SearchDialog
        
        codes = self.code_dao.get_all()
        documents = self.doc_dao.get_all()
        
        doc_list = [{'id': doc['id'], 'title': doc['title'], 'text': doc.get('extracted_text', '') or ''} for doc in documents]
        dialog = SearchDialog(doc_list, codes, self)
        dialog.visualize_requested.connect(self._handle_search_visualization)
        
        if dialog.exec():
            coding_data = dialog.get_coding_data()
            results = coding_data.get('results', [])
            code = coding_data.get('code')
            
            if results and code:
                for result in results:
                    coder_id = getattr(self, 'current_coder_id', 1)
                    self.segment_dao.create(
                        result['doc_id'], code['id'], result['start_pos'], result['end_pos'],
                        result['matched_text'], 3, coder_id=coder_id
                    )
                self.statusbar.showMessage(f"✅ {len(results)} segment kodlandı")
                if self.document_browser._current_doc_id: self._on_document_selected(self.document_browser._current_doc_id)
                # Refresh logic...
                target = self
                if not hasattr(target, 'code_tree') and hasattr(self, 'parent'): target = self.parent
                if hasattr(target, 'code_tree') and hasattr(target, '_on_code_selected'):
                    selected = target.code_tree.get_selected_code()
                    if selected and selected.get('id') == code['id']: target._on_code_selected(code['id'])

    def _handle_search_visualization(self, results, search_term):
        """Handle signal from search dialog to visualize results."""
        try:
            from ..visualizations import generate_search_results_html
            file_path = generate_search_results_html(results, search_term)
            self._open_visualization(f"Arama: {search_term}", file_path)
        except Exception as e:
            show_error(self, "Hata", f"Arama görselleştirmesi oluşturulamadı:\n{str(e)}")

    def _show_document_search(self):
        """Show in-document search as a tab."""
        from ..code_management_dialogs import DocumentSearchWidget
        if not self.document_browser._current_doc_id:
            show_info(self, "Bilgi", "Lütfen önce bir belge seçin.")
            return
            
        # Check if tab already exists
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == "Belge İçi Arama":
                self.central_tabs.setCurrentIndex(i)
                return

        widget = DocumentSearchWidget(self)
        self.add_analysis_tab(widget, "Belge İçi Arama", help_tooltip="Belge İçi Arama: Aktif metinde odaklanmış kelime aramaları (ör. regex) yapıp, bulguları seçtiğiniz koda hızlıca atamanızı sağlar.", help_page="analysis_tools.html", help_anchor="document-search")
