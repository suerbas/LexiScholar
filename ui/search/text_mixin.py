"""
Text and Regex search logic mixin.
"""

import re
from PyQt6.QtWidgets import QMessageBox, QTextEdit, QListWidgetItem
from PyQt6.QtCore import Qt
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class TextSearchMixin:
    """Methods for text and regex based searching."""

    def _perform_text_search(self):
        """Perform standard text/regex search."""
        search_term = self.search_input.text().strip()
        if not search_term:
            show_warning(self, "Uyarı", "Lütfen aranacak metni girin.")
            return
        
        self.search_results = []
        self.results_list.clear()
        
        if self.use_regex.isChecked():
            pattern = search_term
        else:
            raw_term = search_term.replace('.', '').replace(',', '').replace(' ', '')
            if raw_term.isdigit() and len(raw_term) >= 3:
                pattern = re.sub(r'(?<=\d)(?=\d)', r'[.,\\s]?', raw_term)
            else:
                pattern = re.escape(search_term)
            if self.whole_word.isChecked():
                pattern = r'\b' + pattern + r'\b'
        
        flags = 0 if self.case_sensitive.isChecked() else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
            self._execute_search(regex, self.context_spin.value())
        except re.error as e:
            show_warning(self, "Regex Hatası", f"Geçersiz regex: {e}")

    def _execute_search(self, regex, context_size):
        """Execute the regex search on all documents."""
        helper_edit = QTextEdit()
        for doc in self.documents:
            original_text = doc.get('text', '') or ''
            if not original_text: continue
            helper_edit.setPlainText(original_text)
            text = helper_edit.toPlainText()
            
            for match in regex.finditer(text):
                start, end = match.start(), match.end()
                c_start, c_end = max(0, start - context_size), min(len(text), end + context_size)
                ctx = text[c_start:c_end]
                if c_start > 0: ctx = "..." + ctx
                if c_end < len(text): ctx = ctx + "..."
                
                result = {
                    'doc_id': doc['id'], 'doc_title': doc['title'],
                    'start_pos': start, 'end_pos': end,
                    'matched_text': match.group(), 'context': ctx
                }
                self.search_results.append(result)
                item = QListWidgetItem(f"📄 {doc['title']}: \"{ctx}\"")
                item.setData(Qt.ItemDataRole.UserRole, len(self.search_results) - 1)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.results_list.addItem(item)
        self._update_results_ui()
