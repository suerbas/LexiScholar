"""
Base class for modern, resizable, and draggable dialogs in LexiScholar.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QSizePolicy, QSizeGrip
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor

class ModernBaseDialog(QDialog):
    """
    A base class providing:
    - Frameless window with shadow
    - Draggable header area
    - Bottom-right resize handle
    - Aesthetic gradient background
    """
    
    def __init__(self, parent=None, min_width=350, min_height=150):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(min_width)
        self.setMinimumHeight(min_height)
        
        # Mobility & Resize flags
        self.setMouseTracking(True)
        self._dragging = False
        self._drag_pos = None
        
        # Initial UI Setup (Subclasses should call self._setup_base_ui())
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setContentsMargins(10, 10, 10, 10)
        self.base_layout.setSpacing(0)
        
    def _setup_base_ui(self):
        """Creates the main container with styling and shadow."""
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            #MainContainer {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F8FAFC);
            }
        """)

        # Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        self.base_layout.addWidget(self.container)

        # Content layout inside container
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(16, 16, 16, 16)
        
        # We don't add QSizeGrip here yet, it should be in the footer of subclasses
        # but we can provide a method to add it.

    def build_ribbon_header(self, icon: str, title: str, on_close=None):
        """
        Builds and returns a blue gradient ribbon header widget.
        Identical in style to the Shortcuts dialog header.
        on_close: callable called when X is clicked (defaults to self.reject)
        """
        header = QFrame()
        header.setFixedHeight(54)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2E86AB, stop:1 #34495E);
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 12, 0)
        h_layout.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px; color: white; background: transparent;")
        h_layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 800; color: white; background: transparent;"
        )
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()

        close_fn = on_close if on_close else self.reject
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(close_fn)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover { background: rgba(239,68,68,0.85); }
        """)
        h_layout.addWidget(close_btn)
        return header

    def add_size_grip(self, footer_layout):
        """Adds a size grip to the provided layout (usually a footer)."""
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(16, 16)
        footer_layout.addWidget(self.size_grip, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Allow dragging from the top area (header)
            if event.position().y() < 100:
                self._dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        super().mouseReleaseEvent(event)

    def showEvent(self, event):
        if self.parent() and not self.isVisible():
            parent_rect = self.parent().geometry()
            self.move(parent_rect.center() - self.rect().center())
        super().showEvent(event)
