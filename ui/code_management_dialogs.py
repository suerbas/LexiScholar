"""
Analysis Dialogs for LexiScholar - Code Management
UI for code merging, document search, and choosing variables for crosstabs.
"""

from typing import List, Dict, Tuple, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QTabWidget, QWidget, QComboBox,
    QSpinBox, QGroupBox, QHeaderView, QMessageBox, QProgressBar, QFrame,
    QScrollArea, QTextEdit, QListWidget, QListWidgetItem, QLineEdit,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from .common.modern_dialog import ModernBaseDialog
from .common_ui import show_info, show_warning, show_error, ask_confirmation
# from .styles import COLORS # This import was not in the original file, adding it might break things if styles.py doesn't exist or COLORS is not defined. Keeping it commented out as per "without making any unrelated edits" rule.


class CodeMergeDialog(ModernBaseDialog):
    """Dialogue to select two codes and merge them."""
    def __init__(self, codes: list, parent=None):
        super().__init__(parent, min_width=500, min_height=420)
        self.codes = codes
        self.source_code = None
        self.target_code = None
        self._setup_ui()

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("🔗", "Kodları Birleştir")
        self.layout.addWidget(header)

        desc = QLabel("İki kodu birleştirerek tüm segmentleri tek bir kod altında toplayın. Bu işlem geri alınamaz.")
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        self.layout.addWidget(desc)
        
        # Warning
        warning = QLabel("⚠️ Kaynak kod silinecek, tüm segmentleri hedef koda aktarılacak.")
        warning.setStyleSheet("""
            QLabel {
                background-color: #FEF3C7;
                color: #92400E;
                padding: 12px;
                border-radius: 8px;
                font-size: 12px;
            }
        """)
        warning.setWordWrap(True)
        self.layout.addWidget(warning)
        
        # Source code
        source_layout = QHBoxLayout()
        source_label = QLabel("Kaynak Kod:")
        source_label.setFixedWidth(100)
        self.source_combo = QComboBox()
        for code in self.codes:
            self.source_combo.addItem(f"● {code['name']}", code)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_combo)
        self.layout.addLayout(source_layout)
        
        # Arrow
        arrow = QLabel("↓ birleştirilecek ↓")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setStyleSheet("color: #64748B; font-size: 14px;")
        self.layout.addWidget(arrow)
        
        # Target code
        target_layout = QHBoxLayout()
        target_label = QLabel("Hedef Kod:")
        target_label.setFixedWidth(100)
        self.target_combo = QComboBox()
        for code in self.codes:
            self.target_combo.addItem(f"● {code['name']}", code)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_combo)
        self.layout.addLayout(target_layout)
        
        self.layout.addStretch()
        
        # Buttons
        btns = QHBoxLayout()
        btns.addStretch() # Center the buttons

        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        btns.addWidget(cancel_btn)

        self.btn_merge = QPushButton("Kodları Birleştir")
        self.btn_merge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_merge.clicked.connect(self._merge)
        self.btn_merge.setStyleSheet("""
            QPushButton {
                background: #DC2626;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 32px;
                font-weight: 800;
                font-size: 14px;
            }
            QPushButton:hover { background: #B91C1C; }
        """)
        btns.addWidget(self.btn_merge)
        
        btns.addStretch() # Center the buttons
        self.layout.addLayout(btns)
    
    def _merge(self):
        """Validate and perform merge."""
        self.source_code = self.source_combo.currentData()
        self.target_code = self.target_combo.currentData()
        
        if self.source_code['id'] == self.target_code['id']:
            show_warning(self, "Hata", "Kaynak ve hedef kod aynı olamaz.")
            return
        
        reply = ask_confirmation(
            self,
            "Birleştirmeyi Onayla",
            f"'{self.source_code['name']}' kodunu '{self.target_code['name']}' koduna birleştirmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz."
        )
        
        if reply :
            self.accept()
    
    def get_merge_data(self):
        """Get the selected codes for merge."""
        return self.source_code, self.target_code


class DocumentSearchWidget(QWidget):
    """Widget version of Document Search for tabbed interface."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Header
        header = QLabel("🔍 Belge İçi Arama")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        self.layout.addWidget(header)
        
        # Search Bar
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Aranacak metni girin...")
        self.search_input.returnPressed.connect(self._perform_search)
        
        btn_search = QPushButton("Ara")
        btn_search.clicked.connect(self._perform_search)
        
        search_bar.addWidget(self.search_input)
        search_bar.addWidget(btn_search)
        self.layout.addLayout(search_bar)
        
        # Results List
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._on_result_clicked)
        self.layout.addWidget(self.results_list)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #64748B; font-size: 11px;")
        self.layout.addWidget(self.status_label)

    def _perform_search(self):
        query = self.search_input.text().strip()
        if not query: return
        
        # Find MainWindow to access DAOs and current doc
        window = self.window()
        if not hasattr(window, 'document_browser') or not hasattr(window, 'doc_dao'):
            return
            
        doc_id = window.document_browser._current_doc_id
        if not doc_id:
            self.status_label.setText("Lütfen önce bir belge açın.")
            return
            
        from analysis import AnalysisTools
        # We need segment_dao and code_dao too, usually available in window
        if hasattr(window, 'segment_dao') and hasattr(window, 'code_dao'):
            analysis = AnalysisTools(window.doc_dao, window.code_dao, window.segment_dao)
            matches = analysis.search_in_document(doc_id, query)
            self._display_results(matches)
        else:
            self.status_label.setText("Analiz araçlarına erişilemedi.")

    def _display_results(self, matches):
        self.results_list.clear()
        if not matches:
            self.status_label.setText("Eşleşme bulunamadı.")
            return
            
        self.status_label.setText(f"{len(matches)} eşleşme bulundu.")
        for m in matches:
            item = QListWidgetItem(f"...{m['context']}...")
            item.setData(Qt.ItemDataRole.UserRole, m)
            item.setToolTip(f"Konum: {m['position']}")
            self.results_list.addItem(item)

    def _on_result_clicked(self, item):
        match = item.data(Qt.ItemDataRole.UserRole)
        if match:
            window = self.window()
            if hasattr(window, 'document_browser'):
                cursor = window.document_browser.text_edit.textCursor()
                cursor.setPosition(match['position'])
                cursor.setPosition(match['end_position'], cursor.MoveMode.KeepAnchor)
                window.document_browser.text_edit.setTextCursor(cursor)
                window.document_browser.text_edit.ensureCursorVisible()
                # Switch to browser tab
                window.central_tabs.setCurrentIndex(0)

class DocumentSearchDialog(ModernBaseDialog):
    """Dialog for searching within the current document."""
    
    search_requested = None  # Signal would be defined here
    
    def __init__(self, parent=None):
        super().__init__(parent, min_width=500, min_height=300)
        self.search_text = ""
        self._setup_ui()
    
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("🔍", "Belgelerde Ara")
        self.layout.addWidget(header)

        desc = QLabel("Projenizdeki tüm belgeler içinde metin araması yapın.")
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        self.layout.addWidget(desc)

        # Search Input and Button
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #4F46E5; }
        """)
        self.search_input.returnPressed.connect(self._search)
        search_bar.addWidget(self.search_input)
        
        # Result label
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("color: #64748B; font-size: 12px;")
        self.layout.addWidget(self.result_label)

        self.layout.addLayout(search_bar)
        self.layout.addStretch()
        
        # Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.addStretch() # Center the button
        
        search_btn = QPushButton("Belgelerde Ara")
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.clicked.connect(self._search) # Connect to _search method
        search_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 40px;
                font-weight: 800;
                font-size: 14px;
            }
            QPushButton:hover { background: #4338CA; }
        """)
        footer_layout.addWidget(search_btn)
        
        footer_layout.addStretch() # Center the button
        self.layout.addLayout(footer_layout)
        
    def _search(self):
        """Emit search request."""
        self.search_text = self.search_input.text().strip()
        if self.search_text:
            self.accept()
    
    def get_search_text(self):
        """Get the search text."""
        return self.search_text


class CrosstabDialog(ModernBaseDialog):
    """Dialog for selecting a variable for Crosstab analysis."""
    
    def __init__(self, variables, parent=None):
        super().__init__(parent, min_width=520, min_height=350)
        self.variables = variables
        self.selected_var_id = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI using ModernBaseDialog."""
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("📊", "Değişken Bazlı Çapraz Tablo")
        self.layout.addWidget(header)

        desc = QLabel("Seçilen bir değişkenin değerlerine göre kodların dağılımını analiz edin.")
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        self.layout.addWidget(desc)

        # Form Group for Parameters
        form_group = QGroupBox("Analiz Parametreleri")
        form_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                margin-top: 14px;
                background: rgba(255,255,255,0.7);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #334155;
                font-weight: 700;
                font-size: 13px;
            }
            QLabel { color: #334155; font-size: 12px; font-weight: 600; margin-bottom: 2px; border: none; }
            QComboBox {
                min-height: 42px;
                padding: 0px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #0F172A;
            }
            QComboBox::drop-down { border: none; width: 30px; }
        """)
        form_layout = QVBoxLayout(form_group)
        form_layout.setContentsMargins(18, 28, 18, 18)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Analiz edilecek değişkeni seçin:"))
        self.var_combo = QComboBox()
        self.var_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for var in self.variables:
            type_label = {"text": "Metin", "integer": "Sayı", "boolean": "Mantıksal"}.get(var.get('data_type'), "Metin")
            self.var_combo.addItem(f"{var['name']} ({type_label})", var['id'])
        form_layout.addWidget(self.var_combo)

        if not self.variables:
            warn = QLabel("Henüz değişken tanımlanmamış!")
            warn.setStyleSheet("color: #DC2626; font-weight: 700; font-size: 12px;")
            form_layout.addWidget(warn)
            self.var_combo.setEnabled(False)

        self.layout.addWidget(form_group)
        self.layout.addStretch()

        # Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.analyze_btn = QPushButton("Analiz Et")
        self.analyze_btn.setEnabled(len(self.variables) > 0)
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 40px;
                font-weight: 800;
                font-size: 14px;
            }
            QPushButton:hover { background: #4338CA; }
            QPushButton:disabled { background: #A5B4FC; }
        """)
        self.analyze_btn.clicked.connect(self._on_analyze)
        footer_layout.addWidget(self.analyze_btn)
        
        footer_layout.addStretch()
        
        # Add resizing support
        self.add_size_grip(footer_layout)
        
        self.layout.addLayout(footer_layout)
        
    def _on_analyze(self):
        """Select the variable and close."""
        self.selected_var_id = self.var_combo.currentData()
        self.accept()
        
    def get_selected_variable(self):
        """Returns (id, name)"""
        idx = self.var_combo.currentIndex()
        if idx >= 0:
            return self.variables[idx]['id'], self.variables[idx]['name']
        return None, None
