"""
Welcome Dialog for LexiScholar
Startup window for project selection.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, 
    QFrame, QSizePolicy, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

from .icons import IconProvider
from .styles import COLORS, get_color
from __version__ import APP_DISPLAY_VERSION

class WelcomeDialog(QDialog):
    """Modern welcome screen for LexiScholar."""
    
    # Result codes
    EXIT = 0
    NEW_PROJECT = 1
    LOAD_PROJECT = 2
    BROWSE_PROJECT = 3
    
    def __init__(self, recent_projects: list = None):
        super().__init__()
        self.recent_projects = recent_projects or []
        self.selected_project_path = None
        self.result_code = self.EXIT
        
        self._setup_ui()
        self._old_pos = None
        self._margin = 5
        self._resize_mode = None # 'left', 'right', 'top', 'bottom', or corner combos
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _get_resize_mode(self, pos):
        """Determine which edge or corner the mouse is over."""
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = self._margin
        
        mode = ""
        if y < m: mode += "top"
        elif y > h - m: mode += "bottom"
        
        if x < m: mode += "left"
        elif x > w - m: mode += "right"
        
        return mode if mode else None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self._resize_mode = self._get_resize_mode(pos)
            if not self._resize_mode:
                self._old_pos = event.globalPosition().toPoint()
            else:
                self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()
        
        # 1. Update Cursor based on position
        if not event.buttons():
            mode = self._get_resize_mode(pos)
            if mode == "top" or mode == "bottom": self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif mode == "left" or mode == "right": self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif mode == "topleft" or mode == "bottomright": self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif mode == "topright" or mode == "bottomleft": self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else: self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        # 2. Handle Resizing
        if self._resize_mode:
            delta = global_pos - self._old_pos
            geo = self.geometry()
            
            if "left" in self._resize_mode:
                geo.setLeft(geo.left() + delta.x())
            elif "right" in self._resize_mode:
                geo.setRight(geo.right() + delta.x())
                
            if "top" in self._resize_mode:
                geo.setTop(geo.top() + delta.y())
            elif "bottom" in self._resize_mode:
                geo.setBottom(geo.bottom() + delta.y())
            
            # Constraints
            if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
                self.setGeometry(geo)
                self._old_pos = global_pos
            return

        # 3. Handle Moving
        if self._old_pos is not None:
            delta = global_pos - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = global_pos

    def mouseReleaseEvent(self, event):
        self._old_pos = None
        self._resize_mode = None
        
    def _setup_ui(self):
        """Configure the welcome screen UI."""
        self.setWindowTitle("LexiScholar - Hoş Geldiniz")
        self.setMinimumSize(700, 500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Container with shadow-like margin
        container = QFrame(self)
        container.setObjectName("MainContainer")
        container.setStyleSheet(f"""
            #MainContainer {{
                background-color: {get_color('bg_panel')};
                border-radius: 12px;
                border: 1px solid {get_color('border')};
            }}
        """)
        
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Left Side: Branding/Visual ---
        left_panel = QFrame()
        left_panel.setObjectName("LeftPanel")
        left_panel.setFixedWidth(280)
        left_panel.setStyleSheet(f"""
            #LeftPanel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['primary']});
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
            }}
        """)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(32, 40, 32, 40)
        
        logo_lbl = QLabel("🎓")
        logo_lbl.setStyleSheet("font-size: 64px; background: transparent;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_lbl = QLabel("LexiScholar")
        title_lbl.setStyleSheet("font-size: 28px; font-weight: 800; color: #FFFFFF; background: transparent;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_lbl = QLabel("Nitel Veri Analizi\nve Araştırma Asistanı")
        subtitle_lbl.setStyleSheet("font-size: 14px; color: rgba(255, 255, 255, 0.8); background: transparent;")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl.setWordWrap(True)
        
        version_lbl = QLabel(APP_DISPLAY_VERSION)
        version_lbl.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.6); background: transparent;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addWidget(logo_lbl)
        left_layout.addWidget(title_lbl)
        left_layout.addSpacing(8)
        left_layout.addWidget(subtitle_lbl)
        left_layout.addStretch()
        left_layout.addWidget(version_lbl)
        
        # --- Right Side: Actions ---
        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        right_panel.setStyleSheet(f"#RightPanel {{ background-color: {get_color('bg_panel')}; border-top-right-radius: 12px; border-bottom-right-radius: 12px; }}")
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 32, 40, 32)
        right_layout.setSpacing(12)
        
        # Header and Close
        header_layout = QHBoxLayout()
        welcome_lbl = QLabel("Tekrar Hoş Geldiniz")
        welcome_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #1E293B;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{ 
                border: none; color: {get_color('text_muted')}; font-size: 16px; border-radius: 12px; 
            }}
            QPushButton:hover {{ 
                background-color: {get_color('error_bg')}; color: {get_color('error')}; 
            }}
        """)
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(welcome_lbl)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        right_layout.addLayout(header_layout)
        
        # Recent Projects Section
        recent_label = QLabel("Son Çalışılan Projeler (Açmak için çift tıklayınız)")
        recent_label.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 12px; font-weight: 600; margin-top: 8px;")
        right_layout.addWidget(recent_label)
        
        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {get_color('border')};
                border-radius: 8px;
                background-color: {get_color('bg_main')};
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px;
                border-radius: 6px;
                color: {get_color('text_primary')};
                border: 1px solid transparent;
            }}
            QListWidget::item:hover {{
                background-color: {get_color('bg_hover')};
                border: 1px solid {get_color('border')};
            }}
            QListWidget::item:selected {{
                background-color: {get_color('primary_50')};
                color: {get_color('primary')};
                border: 1px solid {get_color('primary')};
                font-weight: 600;
            }}
        """)
        
        if self.recent_projects:
            for proj in self.recent_projects[:5]:
                name = proj.get('name', 'Bilinmeyen Proje')
                path = proj.get('path', '')
                item = QListWidgetItem(f"📁 {name}")
                item.setToolTip(path)
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.recent_list.addItem(item)
            
            self.recent_list.itemDoubleClicked.connect(self._on_recent_clicked)
            right_layout.addWidget(self.recent_list)
        else:
            no_proj = QLabel("Henüz bir projeniz yok.")
            no_proj.setStyleSheet("color: #94A3B8; font-size: 13px; font-style: italic; padding: 20px;")
            no_proj.setAlignment(Qt.AlignmentFlag.AlignCenter)
            right_layout.addWidget(no_proj)
            self.recent_list.hide()
            
        # Action Buttons
        right_layout.addSpacing(8)
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_new = self._create_action_button("✨ Yeni Proje Oluştur", "Yeni bir araştırma dosyası başlatın", "#4F46E5")
        self.btn_new.clicked.connect(self._on_new_project)
        
        self.btn_browse = self._create_action_button("📂 Mevcut Projeyi Aç (Gözat)", "Bilgisayarınızdaki bir projeyi seçin", COLORS['primary'])
        self.btn_browse.clicked.connect(self._on_browse_project)
        
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_browse)
        right_layout.addLayout(btn_layout)
        
        # Main Layout Assembly
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Center the dialog manually since it is frameless
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.addWidget(container)
        
    def _create_action_button(self, text, subtitle, color):
        btn = QPushButton()
        btn.setFixedHeight(54)
        
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(2)
        
        title_lbl = QLabel(text)
        title_lbl.setStyleSheet(f"font-weight: 600; font-size: 14px; color: #FFFFFF; background: transparent;")
        
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.7); background: transparent;")
        
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 1px solid {color};
                border-radius: 8px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {color};
                border: 1px solid #FFFFFF;
                /* Subtle glow effect using border */
            }}
            QPushButton:pressed {{
                background-color: {color};
                padding-top: 2px;
                padding-left: 2px;
            }}
        """)
        
        # Add a subtle highlight overlay for hover
        title_lbl.setObjectName("ActionTitle")
        sub_lbl.setObjectName("ActionSub")
        
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _on_recent_clicked(self, item):
        self.selected_project_path = item.data(Qt.ItemDataRole.UserRole)
        self.result_code = self.LOAD_PROJECT
        self.accept()
        
    def _on_new_project(self):
        self.result_code = self.NEW_PROJECT
        self.accept()
        
    def _on_browse_project(self):
        self.result_code = self.BROWSE_PROJECT
        self.accept()

    def get_result(self):
        return self.result_code, self.selected_project_path
