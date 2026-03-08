"""
Modern Progress Dialog for LexiScholar
An aesthetic replacement for QProgressDialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from .common.modern_dialog import ModernBaseDialog

from .styles import COLORS

class ModernProgressDialog(QDialog):
    """A beautiful, modern progress dialog."""
    
    canceled = pyqtSignal()
    
    def __init__(self, text, cancel_text="İptal", minimum=0, maximum=100, parent=None):
        super().__init__(parent)
        self.text = text
        self.cancel_text = cancel_text
        self.min = minimum
        self.max = maximum
        self._is_canceled = False
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Build the aesthetic UI."""
        self.setFixedSize(400, 220)
        
        # Main Container (with shadow and rounded corners)
        container = QFrame(self)
        container.setObjectName("MainContainer")
        container.setFixedSize(380, 200)
        
        # Center in the dialog (offset for shadow)
        container.move(10, 10)
        
        container.setStyleSheet(f"""
            #MainContainer {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F8FAFC);
            }}
        """)
        
        # Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Title/Icon Row
        header_layout = QHBoxLayout()
        icon_label = QLabel("⚡")
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        self.title_label = QLabel("Analiz Devam Ediyor...")
        self.title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: 700;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Status Text
        self.status_label = QLabel(self.text)
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(self.min, self.max)
        self.progress_bar.setValue(self.min)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_hover']};
                border: none;
                border-radius: 6px;
                text-align: center;
                color: {COLORS['text_primary']};
                font-size: 10px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Cancel Button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        self.cancel_btn = QPushButton(self.cancel_text)
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self._handle_cancel)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: white;
                border-color: {COLORS['error']};
            }}
        """)
        close_layout.addWidget(self.cancel_btn)
        layout.addLayout(close_layout)
        
    def _handle_cancel(self):
        """Handle cancellation."""
        self._is_canceled = True
        self.canceled.emit()
        self.reject()
        
    def wasCanceled(self):
        """Compatibility with QProgressDialog."""
        return self._is_canceled
        
    def setValue(self, value):
        """Update progress value."""
        self.progress_bar.setValue(value)
        if value >= self.max:
            self.title_label.setText("Tamamlandı!")
        
    def setLabelText(self, text):
        """Update status text."""
        self.status_label.setText(text)
        
    def setWindowTitle(self, title):
        """Update title (not visible but for completeness)."""
        super().setWindowTitle(title)

    def setMinimumDuration(self, ms):
        """Compatibility with QProgressDialog (No-op)."""
        pass
        
    def setCancelButtonText(self, text):
        """Update cancel button text."""
        self.cancel_btn.setText(text)
        
    def show(self):
        """Show the dialog centered on parent."""
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(parent_rect.center() - self.rect().center())
        super().show()

class ModernComboboxDialog(ModernBaseDialog):
    """A modern replacement for QInputDialog.getItem, using ModernBaseDialog."""
    
    def __init__(self, title, label_text, items, parent=None):
        super().__init__(parent, min_width=400, min_height=250)
        self._title_text = title
        self._label_text = label_text
        self.items = items
        self.selected_item = None
        self._setup_ui()

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("📄", self._title_text)
        self.layout.addWidget(header)

        # Description
        msg_label = QLabel(self._label_text)
        msg_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; line-height: 1.4;")
        msg_label.setWordWrap(True)
        self.layout.addWidget(msg_label)
        
        # Combobox
        from PyQt6.QtWidgets import QComboBox
        self.combo = QComboBox()
        self.combo.addItems(self.items)
        self.combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px 12px;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background: white;
                color: {COLORS['text_primary']};
                font-size: 13px;
                min-height: 32px;
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background-color: white;
                selection-background-color: {COLORS['primary']};
                selection-color: white;
                color: #0F172A;
                font-size: 13px;
                border: 1px solid #E2E8F0;
                outline: none;
                padding: 2px;
            }}
        """)
        self.layout.addWidget(self.combo)
        self.layout.addStretch()
        
        # Footer Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 6px 20px;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {COLORS['bg_hover']}; }}
        """)
        
        ok_btn = QPushButton("Tamam")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 6px 24px;
                font-weight: 800;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
        """)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        self.layout.addLayout(btn_layout)

    def get_selected(self):
        return self.combo.currentText()
        
    @staticmethod
    def get_item(parent, title, label, items):
        dlg = ModernComboboxDialog(title, label, items, parent)
        if dlg.exec():
            return dlg.get_selected(), True
        return None, False

class ModernInputDialog(ModernBaseDialog):
    """A modern replacement for QInputDialog.getText, using ModernBaseDialog."""
    
    def __init__(self, title, label_text, parent=None):
        super().__init__(parent, min_width=400, min_height=240)
        self._title_text = title
        self._label_text = label_text
        self.text_value = ""
        self._setup_ui()

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("📝", self._title_text)
        self.layout.addWidget(header)

        # Description
        msg_label = QLabel(self._label_text)
        msg_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; line-height: 1.4;")
        msg_label.setWordWrap(True)
        self.layout.addWidget(msg_label)
        
        # Line Edit
        from PyQt6.QtWidgets import QLineEdit
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Buraya yazın...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px 12px;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background: white;
                color: {COLORS['text_primary']};
                font-size: 14px;
                min-height: 32px;
            }}
            QLineEdit:focus {{ border: 2px solid {COLORS['primary']}; }}
        """)
        self.input_field.returnPressed.connect(self.accept)
        self.layout.addWidget(self.input_field)
        self.input_field.setFocus()
        self.layout.addStretch()
        
        # Footer Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 6px 20px;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {COLORS['bg_hover']}; }}
        """)
        
        ok_btn = QPushButton("Tamam")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 6px 24px;
                font-weight: 800;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
        """)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        self.layout.addLayout(btn_layout)

    def get_text(self):
        return self.input_field.text()
        
    @staticmethod
    def get_input(parent, title, label):
        dlg = ModernInputDialog(title, label, parent)
        if dlg.exec():
            return dlg.get_text(), True
        return None, False
