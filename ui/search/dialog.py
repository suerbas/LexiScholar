"""
Search and Auto-Coding Dialog for LexiScholar.
Modularized assembly.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QComboBox, QListWidget,
    QGroupBox, QSpinBox, QTabWidget, QWidget, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from .styles import input_style, button_style, group_style
from .text_mixin import TextSearchMixin
from .proximity_mixin import ProximitySearchMixin
from .automation_mixin import AutomationMixin
from ..common.modern_dialog import ModernBaseDialog

class SearchDialog(ModernBaseDialog, TextSearchMixin, ProximitySearchMixin, AutomationMixin):
    """Dialog for searching text and auto-coding matches."""
    
    auto_coded = pyqtSignal(int)
    visualize_requested = pyqtSignal(list, str)
    
    def __init__(self, documents: list, codes: list, parent=None):
        super().__init__(parent, min_width=750, min_height=650)
        self.documents = documents
        self.codes = codes
        self.search_results = []
        self._setup_ui()
    
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("🔍", "Ara ve Otomatik Kodla")
        self.layout.addWidget(header)
        
        self.tabs = QTabWidget(); self.tabs.setMaximumHeight(200)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; border-radius: 8px; background: #FFFFFF; top: -1px; }
            QTabBar::tab { background: #F1F5F9; border: 1px solid #E2E8F0; padding: 10px 20px; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; color: #64748B; font-weight: 600; }
            QTabBar::tab:selected { background: #FFFFFF; border-bottom-color: #FFFFFF; color: #4F46E5; }
        """)
        
        self._setup_text_search_tab(); self.tabs.addTab(self.text_search_tab, "Metin ve Regex")
        self._setup_proximity_search_tab(); self.tabs.addTab(self.proximity_search_tab, "Yakınlık Araması")
        self.layout.addWidget(self.tabs)
        
        search_btn = QPushButton("🔍 Aramayı Başlat")
        search_btn.setStyleSheet(button_style("#4F46E5", hover_color="#4338CA"))
        search_btn.clicked.connect(self._perform_search)
        btn_lo = QHBoxLayout(); btn_lo.addStretch(); btn_lo.addWidget(search_btn); btn_lo.addStretch(); self.layout.addLayout(btn_lo)
        
        res_group = QGroupBox("Sonuçlar"); res_group.setStyleSheet(group_style())
        res_lo = QVBoxLayout(res_group)
        self.results_label = QLabel("Henüz arama yapılmadı"); self.results_label.setStyleSheet("color: #64748B;"); res_lo.addWidget(self.results_label)
        self.results_list = QListWidget(); self.results_list.setMinimumHeight(150)
        self.results_list.setStyleSheet("QListWidget { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; } QListWidget::item:selected { background: #EEF2FF; }")
        res_lo.addWidget(self.results_list); self.layout.addWidget(res_group)
        
        code_group = QGroupBox("Otomatik Kodlama"); code_group.setStyleSheet(group_style())
        code_lo = QVBoxLayout(code_group)
        lo1 = QHBoxLayout(); lo1.addWidget(QLabel("Uygulanacak Kod:"), 0); self.code_combo = QComboBox(); self.code_combo.setStyleSheet(input_style())
        for c in self.codes: self.code_combo.addItem(f"● {c['name']}", c)
        lo1.addWidget(self.code_combo, 1); code_lo.addLayout(lo1)
        lo2 = QHBoxLayout(); lo2.addWidget(QLabel("Kodlama Kapsamı:"), 0); self.scope_combo = QComboBox(); self.scope_combo.setStyleSheet(input_style())
        self.scope_combo.addItem("Sadece Bulunan Metni Kodla"); self.scope_combo.addItem("İçinde Bulunduğu Cümleyi/Paragrafı Kodla")
        lo2.addWidget(self.scope_combo, 1); code_lo.addLayout(lo2)
        self.select_all_cb = QCheckBox("Tüm sonuçları seç"); self.select_all_cb.stateChanged.connect(self._toggle_select_all); code_lo.addWidget(self.select_all_cb)
        self.layout.addWidget(code_group)
        
        btns = QHBoxLayout()
        self.viz_btn = QPushButton("📊 Görselleştir", clicked=self._on_visualize_clicked); self.viz_btn.setStyleSheet(button_style("#3B82F6", "#2563EB")); self.viz_btn.setEnabled(False)
        self.apply_btn = QPushButton("🏷️ Seçili Sonuçları Kodla", clicked=self._apply_auto_coding); self.apply_btn.setStyleSheet(button_style("#10B981", "#059669")); self.apply_btn.setEnabled(False)
        btns.addStretch(); btns.addWidget(self.viz_btn); btns.addWidget(self.apply_btn); btns.addStretch()
        self.layout.addLayout(btns)

    def _setup_text_search_tab(self):
        self.text_search_tab = QWidget(); lo = QVBoxLayout(self.text_search_tab)
        lo1 = QHBoxLayout(); lo1.addWidget(QLabel("Aranacak Metin:"), 0); self.search_input = QLineEdit(); self.search_input.setStyleSheet(input_style()); lo1.addWidget(self.search_input, 1); lo.addLayout(lo1)
        lo2 = QHBoxLayout(); self.case_sensitive = QCheckBox("Büyük/küçük harf duyarlı"); self.whole_word = QCheckBox("Tam kelime eşleşmesi"); self.use_regex = QCheckBox("Regex kullan"); lo2.addWidget(self.case_sensitive); lo2.addWidget(self.whole_word); lo2.addWidget(self.use_regex); lo2.addStretch(); lo.addLayout(lo2)
        lo3 = QHBoxLayout(); lo3.addWidget(QLabel("Bağlam (karakter):"), 0); self.context_spin = QSpinBox(); self.context_spin.setRange(0, 500); self.context_spin.setValue(50); self.context_spin.setStyleSheet(input_style()); lo3.addWidget(self.context_spin, 1); lo3.addStretch(); lo.addLayout(lo3); lo.addStretch()

    def _setup_proximity_search_tab(self):
        self.proximity_search_tab = QWidget()
        lo = QVBoxLayout(self.proximity_search_tab)
        lo.setSpacing(15)
        
        info = QLabel("İki terimin birbirine belirli bir mesafede geçtiği yerleri bulun.")
        info.setStyleSheet("color: #64748B; font-style: italic;")
        lo.addWidget(info)
        
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(10, 0, 10, 0)
        
        lbl_a = QLabel("Terim A:")
        lbl_a.setStyleSheet("font-weight: 600; color: #475569;")
        self.term_a_input = QLineEdit()
        self.term_a_input.setStyleSheet(input_style())
        grid.addWidget(lbl_a, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self.term_a_input, 0, 1)
        
        prox_lo = QHBoxLayout()
        prox_lo.setSpacing(10)
        prox_lo.addWidget(QLabel("ile", styleSheet="color: #64748B;"))
        self.distance_spin = QSpinBox()
        self.distance_spin.setRange(1, 100)
        self.distance_spin.setValue(10)
        self.distance_spin.setStyleSheet(input_style())
        prox_lo.addWidget(self.distance_spin)
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Kelime", "Paragraf"])
        self.unit_combo.setStyleSheet(input_style())
        prox_lo.addWidget(self.unit_combo)
        
        prox_lo.addWidget(QLabel("mesafe içinde", styleSheet="color: #64748B;"))
        prox_lo.addStretch()
        grid.addLayout(prox_lo, 1, 1)
        
        lbl_b = QLabel("Terim B:")
        lbl_b.setStyleSheet("font-weight: 600; color: #475569;")
        self.term_b_input = QLineEdit()
        self.term_b_input.setStyleSheet(input_style())
        grid.addWidget(lbl_b, 2, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self.term_b_input, 2, 1)
        
        grid.setColumnStretch(1, 1)
        lo.addLayout(grid)
        lo.addStretch()

    def _perform_search(self):
        if self.tabs.currentIndex() == 0: self._perform_text_search()
        else: self._perform_proximity_search()

    def get_coding_data(self):
        return {'results': getattr(self, 'selected_results', []), 'code': getattr(self, 'selected_code', None)}
