"""
Auto-coding and UI interaction logic mixin.
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class AutomationMixin:
    """Methods for applying coding and updating UI state."""

    def _update_results_ui(self):
        count = len(self.search_results)
        self.results_label.setText(f"✅ {count} sonuç bulundu" if count > 0 else "❌ Sonuç bulunamadı")
        self.apply_btn.setEnabled(count > 0 and self.code_combo.count() > 0)
        self.viz_btn.setEnabled(count > 0)
    
    def _toggle_select_all(self, state):
        """Toggle selection of all results."""
        check_state = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        for i in range(self.results_list.count()):
            self.results_list.item(i).setCheckState(check_state)
    
    def _apply_auto_coding(self):
        """Apply the selected code to checked results."""
        if self.code_combo.currentIndex() < 0: return
        code = self.code_combo.currentData()
        selected_results = []
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                res_idx = item.data(Qt.ItemDataRole.UserRole)
                result = self.search_results[res_idx].copy()
                if self.scope_combo.currentIndex() == 1:
                    doc_text = next((d['text'] for d in self.documents if d['id'] == result['doc_id']), "")
                    if doc_text:
                        s = doc_text.rfind('\n', 0, result['start_pos'])
                        s = s + 1 if s != -1 else 0
                        e = doc_text.find('\n', result['end_pos'])
                        e = e if e != -1 else len(doc_text)
                        result['start_pos'], result['end_pos'], result['matched_text'] = s, e, doc_text[s:e].strip()
                selected_results.append(result)
        
        if not selected_results:
            show_info(self, "Bilgi", "Lütfen kodlanacak sonuçları işaretleyin.")
            return
        self.selected_results, self.selected_code = selected_results, code
        self.accept()

    def _on_visualize_clicked(self):
        """Handle visualization request."""
        term = self.search_input.text().strip() if self.tabs.currentIndex() == 0 else f"{self.term_a_input.text().strip()} NEAR {self.term_b_input.text().strip()}"
        self.visualize_requested.emit(self.search_results, term)
