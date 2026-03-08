"""
Standard Header for UI Panels in LexiScholar.
Includes window management controls (Minimize, Detach, Dock).
"""

import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QToolButton
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QSize
from PyQt6.QtGui import QDesktopServices
from .styles import PANEL_HEADER_CONTAINER_STYLE, PANEL_HEADER_LABEL_STYLE, WINDOW_CONTROL_BTN_STYLE
from .icons import IconProvider

class PanelHeader(QFrame):
    """
    Standard panel header with title and window controls.
    """
    minimize_requested = pyqtSignal()
    detach_requested = pyqtSignal()
    dock_requested = pyqtSignal()
    maximize_requested = pyqtSignal()
    close_requested = pyqtSignal()
    
    def __init__(self, title: str, parent=None, is_detached=False, has_minimize=True, has_close=True):
        super().__init__(parent)
        self.setObjectName("PanelHeader")
        self.setStyleSheet(PANEL_HEADER_CONTAINER_STYLE)
        self.is_detached = is_detached
        self.has_minimize = has_minimize
        self.has_close = has_close
        self.title_text = title
        self.subtitle_text = ""
        self.is_analysis = False
        self._drag_pos = None
        self.setFixedHeight(36)
        self._persistent_widgets = []  # Persistent custom header widgets (survive set_detached)
        
        # Help storage
        self.help_tooltip = ""
        self.help_page = "analysis_tools.html"
        self.help_anchor = None
        
        self._setup_ui()
        
    def set_detached(self, detached: bool):
        """Update state and rebuild UI buttons."""
        self.is_detached = detached
        self._setup_ui()

    def set_analysis_mode(self, enabled: bool, subtitle: str = ""):
        """Switch to a specialized blue gradient header for analysis results."""
        self.is_analysis = enabled
        self.subtitle_text = subtitle
        if enabled:
            # Increase height for subtitle
            self.setFixedHeight(65 if subtitle else 55)
            self.setStyleSheet("""
                QFrame#PanelHeader {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2E86AB, stop:1 #34495E);
                    border-bottom: 1px solid #34495E;
                    border-radius: 4px;
                }
            """)
        else:
            self.setFixedHeight(36)
            from .styles import PANEL_HEADER_CONTAINER_STYLE
            self.setStyleSheet(PANEL_HEADER_CONTAINER_STYLE)
        self._setup_ui()

    def mousePressEvent(self, event):
        """Enable dragging the parent window if it's a detached dialog."""
        if self.is_detached and event.button() == Qt.MouseButton.LeftButton:
            # We want to move the top-level parent (the QDialog)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_detached and self._drag_pos is not None:
            # Calculate movement
            delta = event.globalPosition().toPoint() - self._drag_pos
            # Find the top-level window (the QDialog)
            window = self.window()
            if window:
                window.move(window.pos() + delta)
                self._drag_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _setup_ui(self):
        # 1. Reuse existing layout or create new one
        layout = self.layout()
        if not layout:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(10 if self.is_analysis else 0, 0, 4, 0)
            layout.setSpacing(0)
        else:
            # Recursive helper to clear everything (persistent widgets are preserved)
            def clear_layout(l):
                while l.count():
                    child = l.takeAt(0)
                    if child.widget():
                        w = child.widget()
                        if w in self._persistent_widgets:
                            # Don't destroy persistent widgets — detach from layout only
                            w.setParent(None)
                        else:
                            w.deleteLater()
                    elif child.layout():
                        clear_layout(child.layout())
            clear_layout(layout)
        
        if self.is_analysis:
            # Lightbulb icon as a button for hover/interaction
            icon_btn = QToolButton()
            icon_btn.setIcon(IconProvider.get_action_icon("help", "#FFFFFF"))
            icon_btn.setIconSize(QSize(20, 20))
            icon_btn.setStyleSheet("QToolButton { padding-right: 15px; background: transparent; border: none; font-size: 22pt; }")
            icon_btn.setAccessibleName("Analiz Yardımı")
            icon_btn.setAccessibleDescription("Analiz kartı için ilgili yardım kaynağını açar.")
            icon_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            if self.help_tooltip:
                icon_btn.setToolTip(self.help_tooltip)
                icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                # Re-apply help link if exists
                if self.help_tooltip:
                    icon_btn.clicked.connect(self._open_help)
            layout.addWidget(icon_btn)
            self.icon_label = icon_btn # Store reference
            
            # Text container
            text_container = QWidget()
            text_container.setStyleSheet("background: transparent;")
            text_vbox = QVBoxLayout(text_container)
            text_vbox.setContentsMargins(0, 5, 0, 5)
            text_vbox.setSpacing(2)
            
            # Title
            title_lbl = QLabel(self.title_text)
            title_lbl.setStyleSheet("color: white; font-size: 14pt; font-weight: bold; border: none;")
            text_vbox.addWidget(title_lbl)
            
            # Subtitle
            if self.subtitle_text:
                sub_lbl = QLabel(self.subtitle_text)
                sub_lbl.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 9pt; border: none;")
                text_vbox.addWidget(sub_lbl)
            
            layout.addWidget(text_container)
        else:
            # Help Button (Hidden by default)
            self.btn_help = QToolButton()
            self.btn_help.setIcon(IconProvider.get_action_icon("help", "#64748B"))
            self.btn_help.setIconSize(QSize(14, 14))
            self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_help.setAccessibleName("Yardım")
            self.btn_help.setAccessibleDescription("İlgili panel yardım sayfasını açar.")
            self.btn_help.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.btn_help.setStyleSheet("QToolButton { font-size: 14px; border: none; background: transparent; padding: 2px; } QToolButton:hover { background: #F1F5F9; border-radius: 4px; }")
            self.btn_help.hide()
            layout.addWidget(self.btn_help)
            
            # Title Label
            self.label = QLabel(self.title_text)
            from .styles import PANEL_HEADER_LABEL_STYLE
            self.label.setStyleSheet(PANEL_HEADER_LABEL_STYLE)
            layout.addWidget(self.label)
        
        # Extra spacing and custom actions layout
        # Modified: Always allow custom layout, even in analysis mode
        layout.addStretch()
        
        layout.addSpacing(10)
        self.custom_layout = QHBoxLayout()
        self.custom_layout.setSpacing(4)
        layout.addLayout(self.custom_layout)

        # Restore persistent widgets (survive detach/dock rebuilds)
        for widget in self._persistent_widgets:
            if widget is not None:
                widget.setParent(self)
                # Enforce matching height for analysis mode
                if self.is_analysis:
                    widget.setFixedHeight(32)
                self.custom_layout.addWidget(widget)
                widget.show()
        
        # Window Controls Container
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(2)
        
        # Style for buttons in analysis mode vs normal mode
        if self.is_analysis:
            btn_style = """
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            """
        else:
            # "Kibar" style for normal panels (Belgeler, Kodlar etc)
            btn_style = """
                QPushButton {
                    background-color: transparent;
                    color: #64748B;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                    color: #1E293B;
                }
            """

        def configure_control_button(button: QPushButton, name: str, desc: str, symbol: str):
            button.setAccessibleName(name)
            button.setAccessibleDescription(desc)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.setText(symbol)
            button.setIconSize(QSize(0, 0))
            
            # Enforce 32x32 for analysis mode to match persistent custom widgets (like Export btn)
            size = 32 if self.is_analysis else 24
            button.setFixedSize(size, size)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        # Add separator for normal mode
        if not self.is_analysis:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setFixedSize(1, 14)
            sep.setStyleSheet("background-color: rgba(0, 0, 0, 0.1); margin: 0 4px;")
            controls_layout.addWidget(sep)

        # Minimize Button
        if self.has_minimize:
            self.btn_minimize = QPushButton()
            self.btn_minimize.setToolTip("Paneli Durum Çubuğuna Küçült")
            self.btn_minimize.setStyleSheet(btn_style)
            configure_control_button(self.btn_minimize, "Paneli Küçült", "Paneli durum çubuğuna küçültür.", "—")
            self.btn_minimize.clicked.connect(self.minimize_requested.emit)
            controls_layout.addWidget(self.btn_minimize)

        if not self.is_detached:
            # Detach Button
            self.btn_detach = QPushButton()
            self.btn_detach.setToolTip("Paneli Ayrı Pencerede Aç")
            self.btn_detach.setStyleSheet(btn_style)
            configure_control_button(self.btn_detach, "Paneli Ayır", "Paneli ayrı pencerede açar.", "↗")
            self.btn_detach.clicked.connect(self.detach_requested.emit)
            controls_layout.addWidget(self.btn_detach)
        else:
            # Maximize Button (Only show in detached mode, before Dock)
            self.btn_maximize = QPushButton()
            self.btn_maximize.setObjectName("MaximizeBtn")
            self.btn_maximize.setToolTip("Pencereyi Tam Ekran Yap / Küçült")
            self.btn_maximize.setStyleSheet(btn_style)
            configure_control_button(self.btn_maximize, "Tam Ekran", "Pencereyi tam ekran ve normal mod arasında değiştirir.", "◻")
            self.btn_maximize.clicked.connect(self.maximize_requested.emit)
            controls_layout.addWidget(self.btn_maximize)

            # Dock Button (Only show Dock in detached mode)
            self.btn_dock = QPushButton()
            self.btn_dock.setObjectName("DockBtn")
            self.btn_dock.setToolTip("Paneli Ana Pencereye Geri Gönder")
            self.btn_dock.setStyleSheet(btn_style)
            configure_control_button(self.btn_dock, "Panele Geri Yerleştir", "Paneli ana pencereye geri yerleştirir.", "↙")
            self.btn_dock.clicked.connect(self.dock_requested.emit)
            controls_layout.addWidget(self.btn_dock)

            # Close Button for detached window (Only if closable)
            if self.has_close:
                btn_close = QPushButton()
                btn_close.setObjectName("CloseBtn")
                btn_close.setToolTip("Pencereyi Kapat")
                if self.is_analysis:
                    btn_close.setStyleSheet(btn_style.replace("color: white;", "color: #FEE2E2;")) 
                else:
                    btn_close.setStyleSheet(btn_style + "QPushButton { color: #EF4444; } QPushButton:hover { background-color: #FEE2E2; }")
                configure_control_button(btn_close, "Pencereyi Kapat", "Ayrılmış panel penceresini kapatır.", "✕")
                btn_close.clicked.connect(self.close_requested.emit)
                controls_layout.addWidget(btn_close)
            
        layout.addLayout(controls_layout)
        self.controls_layout = controls_layout

    def set_detach_visible(self, visible: bool):
        """Show or hide the detach button."""
        if hasattr(self, 'btn_detach') and self.btn_detach:
            self.btn_detach.setVisible(visible)

    def set_help(self, tooltip: str, page_name: str = "analysis_tools.html", anchor: str = None):
        """Configure and show the help button."""
        self.help_tooltip = tooltip
        self.help_page = page_name
        self.help_anchor = anchor

        if hasattr(self, 'btn_help'):
            self.btn_help.setToolTip(tooltip)
            try: self.btn_help.clicked.disconnect()
            except: pass
            self.btn_help.clicked.connect(self._open_help)
            self.btn_help.show()
        
        if self.is_analysis and hasattr(self, 'icon_label'):
            self.icon_label.setToolTip(tooltip)
            self.icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
            try: self.icon_label.clicked.disconnect()
            except: pass
            self.icon_label.clicked.connect(self._open_help)

    def _open_help(self):
        """Open local help URL."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if self.help_page.startswith("http") or self.help_page.startswith("file:"):
            url = QUrl(self.help_page)
        else:
            page = os.path.join(base, "docs", "encyclopedia", self.help_page)
            url = QUrl.fromLocalFile(page)
            if self.help_anchor:
                url.setFragment(self.help_anchor.lstrip('#'))
        QDesktopServices.openUrl(url)

    def set_title(self, text: str):
        self.title_text = text
        if hasattr(self, 'label') and self.label:
            self.label.setText(text)

    def set_title_visible(self, visible: bool):
        """Show or hide the title label."""
        if hasattr(self, 'label') and self.label:
            self.label.setVisible(visible)

    def setText(self, text: str):
        """Alias for set_title to maintain compatibility with QLabel interface."""
        self.set_title(text)

    def text(self) -> str:
        """Returns the current title text."""
        return self.title_text
