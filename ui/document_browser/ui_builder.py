"""
UI Construction for Document Browser
Handles layout, toolbars, and styling.
"""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QToolButton, QLabel, QToolBar, QFontComboBox, QSpinBox, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from ..styles import COLORS, TEXT_EDIT_STYLE
from ..browser_widgets import CodingStripesWidget, CodableTextEdit
# from ..panel_header import PanelHeader # Removed

class DocumentBrowserUIBuilder:
    """Methods for building the DocumentBrowser interface."""

    def _setup_ui(self):
        self.text_edit = CodableTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self._show_context_menu)
        self.text_edit.selectionChanged.connect(self._on_selection_changed)
        self.text_edit.verticalScrollBar().valueChanged.connect(self._sync_stripes)
        self.text_edit.code_dropped.connect(self._on_code_dropped)
        self.text_edit.mouse_moved.connect(self._on_mouse_moved)
        self.text_edit.setOpenLinks(False)
        self.text_edit.anchorClicked.connect(self._handle_link_click)
        self.text_edit.resized.connect(self._sync_stripes)
        self.text_edit.textChanged.connect(self._sync_stripes)
        
        self._setup_text_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Setup Toolbar (Merged Header functionality)
        self._setup_formatting_toolbar(layout)
        
        self.code_indicator = QLabel("")
        self.code_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['browser_toolbar_bg']};
                color: {COLORS['action_help']};
                font-size: 11px;
                padding: 6px 16px;
                border-bottom: 2px solid {COLORS['browser_toolbar_border']};
                font-weight: 500;
            }}
        """)
        self.code_indicator.hide()
        layout.addWidget(self.code_indicator)
        
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.coding_stripes = CodingStripesWidget()
        self.coding_stripes.setStyleSheet(f"""
            QWidget {{
                border-right: 1px solid {COLORS['border']};
                background-color: {COLORS['bg_panel']};
            }}
        """)
        content_layout.addWidget(self.coding_stripes)
        content_layout.addWidget(self.text_edit)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget)

    def _setup_formatting_toolbar(self, layout):
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        # Reduce spacing/padding for tighter layout
        toolbar.setStyleSheet(f"""
            QToolBar {{ 
                background-color: {COLORS['browser_toolbar_bg']}; 
                border-bottom: 1px solid {COLORS['browser_toolbar_border']}; 
                spacing: 2px; 
                padding: 2px 4px; 
            }}
            QToolButton {{ 
                background-color: transparent; 
                border: 1px solid transparent; 
                border-radius: 4px; 
                padding: 2px 4px; 
                color: {COLORS['primary_700']}; 
                font-family: 'Segoe UI';
                font-size: 9pt;
            }}
            QToolButton:hover {{ 
                background-color: {COLORS['primary_200']}; 
                border: 1px solid {COLORS['primary_300']}; 
                color: {COLORS['primary_800']};
            }}
            QToolButton:checked {{
                background-color: {COLORS['primary_200']};
                border: 1px solid {COLORS['primary_600']};
                color: {COLORS['primary_800']};
            }}
        """)
        
        # --- AI Chat Button (Small) ---
        btn_chat = QToolButton()
        btn_chat.setText("🤖 AI") 
        btn_chat.setToolTip("Bu belgeyle sohbet et (RAG)")
        btn_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_chat.setStyleSheet(f"QToolButton {{ font-weight: bold; color: {COLORS['action_help']}; background: {COLORS['browser_toolbar_bg']}; border: 1px solid {COLORS['browser_toolbar_border']}; border-radius: 4px; padding: 2px 6px; }} QToolButton:hover {{ background: {COLORS['primary_200']}; }}")
        
        if hasattr(self, '_chat_with_document'):
            btn_chat.clicked.connect(self._chat_with_document)
            
        toolbar.addWidget(btn_chat)
        toolbar.addSeparator()

        # --- Font Controls ---
        self.font_combo = QFontComboBox()
        self.font_combo.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        self.font_combo.setCurrentFont(QFont("Times New Roman"))
        self.font_combo.currentFontChanged.connect(lambda f: self.text_edit.setFontFamily(f.family()))
        self.font_combo.setMinimumWidth(110) # Reduced to save space
        self.font_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.font_combo.setToolTip("Yazı Tipi")
        toolbar.addWidget(self.font_combo)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(12)
        self.size_spin.setToolTip("Yazı Boyutu")
        self.size_spin.valueChanged.connect(lambda s: self.text_edit.setFontPointSize(s))
        toolbar.addWidget(self.size_spin)
        
        toolbar.addSeparator()
        
        # --- Formatting (Classic Word Style) ---
        # Bold
        btn_bold = QToolButton()
        btn_bold.setText("B")
        btn_bold.setFont(QFont("Times New Roman", 11, QFont.Weight.Bold))
        btn_bold.setToolTip("Kalın (Bold)")
        btn_bold.setCheckable(True)
        btn_bold.clicked.connect(lambda c: self.text_edit.setFontWeight(QFont.Weight.Bold if c else QFont.Weight.Normal))
        toolbar.addWidget(btn_bold)
        
        # Italic
        btn_italic = QToolButton()
        btn_italic.setText("I")
        btn_italic.setFont(QFont("Times New Roman", 11, italic=True))
        btn_italic.setToolTip("İtalik (Italic)")
        btn_italic.setCheckable(True)
        btn_italic.clicked.connect(self.text_edit.setFontItalic)
        toolbar.addWidget(btn_italic)
        
        # Underline
        btn_underline = QToolButton()
        btn_underline.setText("U")
        font_u = QFont("Times New Roman", 11)
        font_u.setUnderline(True)
        btn_underline.setFont(font_u)
        btn_underline.setToolTip("Altı Çizili (Underline)")
        btn_underline.setCheckable(True)
        btn_underline.clicked.connect(self.text_edit.setFontUnderline)
        toolbar.addWidget(btn_underline)
        
        # Color
        self.btn_color = QToolButton()
        self.btn_color.setText("A")
        self.btn_color.setToolTip("Metin Rengi")
        # Use a cleaner style that doesn't break hover
        self.btn_color.setStyleSheet(f"QToolButton {{ color: #DC2626; font-weight: bold; border-bottom: 2px solid #DC2626; }} QToolButton:hover {{ background-color: {COLORS['bg_hover']}; }}")
        self.btn_color.clicked.connect(self._choose_color)
        toolbar.addWidget(self.btn_color)

        toolbar.addSeparator()

        # --- Alignment ---
        # Using standard alignment icons
        btn_left = QToolButton(); btn_left.setText("≡"); btn_left.setToolTip("Sola Hizala"); btn_left.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignmentFlag.AlignLeft))
        toolbar.addWidget(btn_left)
        btn_center = QToolButton(); btn_center.setText("≚"); btn_center.setToolTip("Ortala"); btn_center.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignmentFlag.AlignCenter))
        toolbar.addWidget(btn_center)
        btn_right = QToolButton(); btn_right.setText("≣"); btn_right.setToolTip("Sağa Hizala"); btn_right.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignmentFlag.AlignRight))
        toolbar.addWidget(btn_right)
        btn_justify = QToolButton(); btn_justify.setText("|||"); btn_justify.setToolTip("İki Yana Yasla"); btn_justify.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignmentFlag.AlignJustify))
        toolbar.addWidget(btn_justify)
        
        toolbar.addSeparator()
        
        # --- Read Only Toggle ---
        self.btn_edit = QToolButton()
        self.btn_edit.setText("🔒")
        self.btn_edit.setToolTip("Salt Okunur / Düzenle")
        self.btn_edit.setCheckable(True)
        self.btn_edit.setStyleSheet("font-size: 13px;")
        self.btn_edit.clicked.connect(self._toggle_edit_mode)
        toolbar.addWidget(self.btn_edit)
        
        # --- Save Button ---
        self.btn_save_text = QToolButton()
        self.btn_save_text.setText("💾")
        self.btn_save_text.setToolTip("Kaydet")
        self.btn_save_text.setStyleSheet("color: #16a34a; font-size: 13px;")
        self.btn_save_text.clicked.connect(self._save_content)
        self.btn_save_text.hide()
        toolbar.addWidget(self.btn_save_text)

        # --- Spacer ---
        # Using an Expanding spacer to push window controls (minimize/detach) to the absolute right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # --- Window Controls (Consistent Icons) ---
        # Using Underscore and Arrow icons as requested
        toolbar.addSeparator()
        
        btn_minimize = QToolButton()
        btn_minimize.setText("—")
        btn_minimize.setToolTip("Paneli Durum Çubuğuna Küçült")
        btn_minimize.setFixedSize(28, 28)
        btn_minimize.clicked.connect(self.minimize_requested.emit)
        toolbar.addWidget(btn_minimize)

        self.btn_detach = QToolButton()
        self.btn_detach.setText("↗") # NE Arrow (Docked state)
        self.btn_detach.setToolTip("Paneli Ayır")
        self.btn_detach.clicked.connect(self.detach_requested.emit)
        toolbar.addWidget(self.btn_detach)

        self.btn_maximize = QToolButton()
        self.btn_maximize.setText("◻")
        self.btn_maximize.setToolTip("Pencereyi Tam Ekran Yap / Küçült")
        self.btn_maximize.clicked.connect(self.maximize_requested.emit)
        self.action_maximize = toolbar.addWidget(self.btn_maximize)
        self.action_maximize.setVisible(False) # Only visible when detached

        layout.addWidget(toolbar)

    def _setup_text_style(self):
        self.text_edit.setStyleSheet(TEXT_EDIT_STYLE)
        font = QFont("Georgia", 11)
        font.setStyleHint(QFont.StyleHint.Serif)
        self.text_edit.setFont(font)
