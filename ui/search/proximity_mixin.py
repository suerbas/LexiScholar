"""
Proximity search logic mixin.
"""

import re
from PyQt6.QtWidgets import QMessageBox
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class ProximitySearchMixin:
    """Methods for finding terms near each other."""

    def _perform_proximity_search(self):
        """Perform proximity search."""
        term_a = self.term_a_input.text().strip()
        term_b = self.term_b_input.text().strip()
        distance = self.distance_spin.value()
        unit = self.unit_combo.currentText()
        if not term_a or not term_b:
            show_warning(self, "Uyarı", "Lütfen her iki terimi de girin.")
            return

        self.search_results = []
        self.results_list.clear()
        term_a_esc, term_b_esc = re.escape(term_a), re.escape(term_b)
        
        if unit == "Kelime":
            mid_pattern = r'(?:\W+(?:\w+)?){0,' + str(distance) + r'}\W+'
        else:
            mid_pattern = r'(?:[^\n]*\n){0,' + str(distance) + r'}[^\n]*'

        full_pattern = f"({term_a_esc}){mid_pattern}({term_b_esc})|({term_b_esc}){mid_pattern}({term_a_esc})"
        try:
            regex = re.compile(full_pattern, re.IGNORECASE)
            self._execute_search(regex, context_size=50)
        except re.error as e:
            show_warning(self, "Hata", f"Regex oluşturulamadı: {e}")
