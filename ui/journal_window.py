from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QToolBar, QWidget, 
    QMessageBox, QScrollArea, QFrame, QLabel, QSizePolicy,
    QTextEdit, QHBoxLayout, QFontComboBox, QComboBox, QColorDialog,
    QMenu, QToolButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import (
    QAction, QIcon, QFont, QTextCharFormat, QColor, 
    QTextListFormat, QTextCursor, QActionGroup
)

from database.schema import ProjectJournalDAO
from ui.styles import MEMO_DIALOG_STYLE
from ui.icons import IconProvider
from .common_ui import show_info, show_warning, show_error, ask_confirmation
from ui.common.modern_dialog import ModernBaseDialog
from ui.styles import get_color

class JournalWindow(ModernBaseDialog):
    """
    Dialog for the Project Journal (Günlük).
    Provides a powerful rich text editor for a single project-wide journal entry.
    Features: Fonts, Colors, Alignments, Lists, Date Insertion.
    Modernized with frameless design and ribbon header.
    """
    
    def __init__(self, journal_dao: ProjectJournalDAO, parent=None):
        super().__init__(parent, min_width=1000, min_height=700)
        self.setWindowTitle("Proje Günlüğü")
        
        self.dao = journal_dao
        
        self._setup_ui()
        self._load_journal()

    def _setup_ui(self):
        """Modern setup with ribbon header and frameless design."""
        self._setup_base_ui()
        
        # Header
        header = self.build_ribbon_header("📖", "Proje Günlüğü")
        self.base_layout.addWidget(header)
        
        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self._setup_toolbar_actions()
        self.base_layout.addWidget(self.toolbar)
        
        # Editor
        self.editor = QTextEdit()
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {get_color('bg_main')};
                padding: 30px;
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: {get_color('text_secondary')};
            }}
        """)
        self.base_layout.addWidget(self.editor, 1)
        
        # Footer buttons
        footer = QHBoxLayout()
        footer.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_journal)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('primary')};
                color: {get_color('text_inverse')};
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {get_color('primary_dark')};
            }}
        """)
        footer.addWidget(save_btn)
        
        self.base_layout.addLayout(footer)
        
    def _setup_toolbar_actions(self):
        """Setup toolbar actions with modern styling."""
        self.toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {get_color('bg_panel')};
                border-bottom: 1px solid {get_color('border')};
                padding: 6px;
                spacing: 6px;
            }}
            QToolButton {{
                border-radius: 4px;
                padding: 4px;
                color: {get_color('text_secondary')};
                font-size: 11px;
            }}
            QToolButton:hover {{
                background-color: {get_color('bg_hover')};
            }}
            QComboBox {{
                padding: 4px;
                border: 1px solid {get_color('border')};
                border-radius: 4px;
                background: {get_color('bg_main')};
            }}
        """)
        
        # Save action
        save_action = QAction(IconProvider.get_icon("💾", get_color('success')), "Kaydet", self)
        save_action.triggered.connect(self._save_journal)
        self.toolbar.addAction(save_action)
        self.toolbar.addSeparator()
        
        # Font controls (simplified for modern dialog)
        # Additional toolbar actions can be added here as needed

class JournalWidget(QWidget):
    """
    Widget version of Project Journal for tabbed interface.
    """
    def __init__(self, journal_dao: ProjectJournalDAO, parent=None):
        super().__init__(parent)
        self.dao = journal_dao
        self._setup_ui()
        self._load_journal()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- Toolbar ---
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon) # text labels
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                padding: 6px;
                spacing: 6px;
            }
            QToolButton {
                border-radius: 4px;
                padding: 4px;
                color: #334155;
                font-size: 11px;
            }
            QToolButton:hover {
                background-color: #e2e8f0;
            }
            QComboBox {
                padding: 4px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background: white;
            }
        """)
        
        # 1. Save
        save_action = QAction(IconProvider.get_icon("💾", "#16a34a"), "Kaydet", self)
        save_action.triggered.connect(self._save_journal)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 2. Font Family
        self.combo_font = QFontComboBox()
        self.combo_font.setFixedWidth(150)
        self.combo_font.currentFontChanged.connect(self._set_font_family)
        toolbar.addWidget(self.combo_font)
        
        # 3. Font Size
        self.combo_size = QComboBox()
        self.combo_size.setFixedWidth(60)
        sizes = [8, 9, 10, 11, 12, 14, 16, 18, 24, 36, 48, 72]
        self.combo_size.addItems([str(s) for s in sizes])
        self.combo_size.setCurrentText("14") # Default
        self.combo_size.currentTextChanged.connect(self._set_font_size)
        toolbar.addWidget(self.combo_size)
        
        toolbar.addSeparator()
        
        # 4. Text Format (Bold, Italic, Underline)
        bold_action = QAction(IconProvider.get_icon("𝐁", "#334155"), "Kalın", self)
        bold_action.setCheckable(True)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(lambda: self._format_text("bold"))
        toolbar.addAction(bold_action)
        
        italic_action = QAction(IconProvider.get_icon("𝑰", "#334155"), "İtalik", self)
        italic_action.setCheckable(True)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(lambda: self._format_text("italic"))
        toolbar.addAction(italic_action)
        
        underline_action = QAction(IconProvider.get_icon("U̲", "#334155"), "Altı Çizili", self)
        underline_action.setCheckable(True)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(lambda: self._format_text("underline"))
        toolbar.addAction(underline_action)
        
        # 5. Colors
        color_action = QAction(IconProvider.get_icon("🎨", "#ec4899"), "Renk", self) # Pink palette
        color_action.triggered.connect(self._set_text_color)
        toolbar.addAction(color_action)
         
        bg_color_action = QAction(IconProvider.get_icon("🖍️", "#facc15"), "Vurgula", self) # Yellow highlighter
        bg_color_action.triggered.connect(self._set_bg_color)
        toolbar.addAction(bg_color_action)

        toolbar.addSeparator()

        # 6. Alignment
        align_group = QActionGroup(self)
        
        align_left = QAction(IconProvider.get_icon("⬅️", "#64748b"), "Sola", self)
        align_left.setCheckable(True)
        align_left.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignLeft))
        align_group.addAction(align_left)
        toolbar.addAction(align_left)
        
        align_center = QAction(IconProvider.get_icon("↔️", "#64748b"), "Ortala", self)
        align_center.setCheckable(True)
        align_center.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignCenter))
        align_group.addAction(align_center)
        toolbar.addAction(align_center)
        
        align_right = QAction(IconProvider.get_icon("➡️", "#64748b"), "Sağa", self)
        align_right.setCheckable(True)
        align_right.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignRight))
        align_group.addAction(align_right)
        toolbar.addAction(align_right)

        # 7. Lists
        list_bullet = QAction(IconProvider.get_icon("•", "#64748b"), "Liste", self)
        list_bullet.triggered.connect(lambda: self._set_list_style(QTextListFormat.Style.ListDisc))
        toolbar.addAction(list_bullet)
        
        list_number = QAction(IconProvider.get_icon("1.", "#64748b"), "Sıralı", self)
        list_number.triggered.connect(lambda: self._set_list_style(QTextListFormat.Style.ListDecimal))
        toolbar.addAction(list_number)
        
        toolbar.addSeparator()
        
        # 8. Date
        date_action = QAction(IconProvider.get_icon("📅", "#3b82f6"), "Tarih", self)
        date_action.triggered.connect(self._insert_date)
        toolbar.addAction(date_action)
        
        layout.addWidget(toolbar)
        
        # Info Header (Smaller now)
        header = QFrame()
        header.setStyleSheet("background-color: #f1f5f9; padding: 6px 12px; border-bottom: 1px solid #e2e8f0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        subtitle = QLabel("💡 Bu günlük projenize aittir ve tek bir dosya olarak saklanır. Dilediğiniz gibi biçimlendirebilirsiniz.")
        subtitle.setStyleSheet("color: #64748b; font-size: 12px; font-style: italic;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # Editor
        self.editor = QTextEdit()
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                padding: 30px;
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #334155;
            }
        """)
        self.editor.currentCharFormatChanged.connect(self._update_format_actions) # Sync toolbar with cursor
        layout.addWidget(self.editor)
        
    def _load_journal(self):
        content = self.dao.get_content()
        if "<html>" in content or "<p>" in content:
             self.editor.setHtml(content)
        else:
             self.editor.setText(content)
             
    def _save_journal(self):
        content = self.editor.toHtml()
        if self.dao.save_content(content):
            self.setWindowTitle("Proje Günlüğü - Kaydedildi ✔")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.setWindowTitle("Proje Günlüğü"))
        else:
            show_warning(self, "Hata", "Günlük kaydedilemedi.")

    def _format_text(self, fmt_type):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        
        if fmt_type == "bold":
            fmt.setFontWeight(QFont.Weight.Bold if not cursor.charFormat().fontWeight() == QFont.Weight.Bold else QFont.Weight.Normal)
        elif fmt_type == "italic":
            fmt.setFontItalic(not cursor.charFormat().fontItalic())
        elif fmt_type == "underline":
            fmt.setFontUnderline(not cursor.charFormat().fontUnderline())
            
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def _set_font_family(self, font):
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self._merge_format(fmt)

    def _set_font_size(self, size_str):
        if not size_str: return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(size_str))
        self._merge_format(fmt)

    def _set_text_color(self):
        color = QColorDialog.getColor(self.editor.textColor(), self, "Yazı Rengi Seç")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._merge_format(fmt)

    def _set_bg_color(self):
        color = QColorDialog.getColor(Qt.GlobalColor.white, self, "Vurgu Rengi Seç")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            self._merge_format(fmt)

    def _set_alignment(self, align):
        self.editor.setAlignment(align)
        self.editor.setFocus()

    def _set_list_style(self, style):
        cursor = self.editor.textCursor()
        cursor.createList(style)
        self.editor.setFocus()

    def _merge_format(self, fmt):
        cursor = self.editor.textCursor()
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def _insert_date(self):
        from datetime import datetime
        cursor = self.editor.textCursor()
        TURKISH_MONTHS = {1:'Ocak', 2:'Şubat', 3:'Mart', 4:'Nisan', 5:'Mayıs', 6:'Haziran',
                          7:'Temmuz', 8:'Ağustos', 9:'Eylül', 10:'Ekim', 11:'Kasım', 12:'Aralık'}
        now = datetime.now()
        date_str = f"{now.day} {TURKISH_MONTHS[now.month]} {now.year} {now.strftime('%H:%M:%S')}"
        
        # Insert as a stylized header
        cursor.insertBlock()
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold)
        fmt.setForeground(QColor("#2563eb"))
        fmt.setFontPointSize(12)
        
        cursor.insertText(f"📅 {date_str}", fmt)
        cursor.insertBlock()
        
        # Reset format
        fmt = QTextCharFormat()
        fmt.setFontPointSize(10) # defaultish
        fmt.setForeground(QColor("#334155"))
        cursor.setCharFormat(fmt)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        
    def _update_format_actions(self, fmt):
        # Optional: update toolbar states based on cursor format
        # This would require keeping references to actions
        pass
