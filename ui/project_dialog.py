"""
Project Dialog for LexiScholar
Dialog for project save/load/create operations.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from .common.modern_dialog import ModernBaseDialog
from .common_ui import show_info, show_warning, show_error, ask_confirmation


class ProjectDialog(ModernBaseDialog):
    """Dialog for project save/load operations, modernized with ModernBaseDialog."""
    
    def __init__(self, parent=None, mode: str = 'save', recent_projects: list = None):
        super().__init__(parent, min_width=480, min_height=mode == 'load' and 400 or 320)
        self.mode = mode  # 'save' or 'load'
        self.project_name = ""
        self.project_path = ""
        self.recent_projects = recent_projects or []
        self.selected_project_path = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI using ModernBaseDialog."""
        self._setup_base_ui()
        is_save = self.mode == 'save'
        is_create = self.mode == 'create'
        
        if is_create:
            title_text = "Yeni Proje Oluştur"
            header_icon = "✨"
            btn_text = "✨ Proje Oluştur"
        elif is_save:
            title_text = "Projeyi Kaydet"
            header_icon = "💾"
            btn_text = "💾 Değişiklikleri Kaydet"
        else:
            title_text = "Projeyi Aç"
            header_icon = "📂"
            btn_text = "📂 Projeyi Aç"
            
        # Header Area
        header_layout = QHBoxLayout()
        icon = QLabel(header_icon)
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Red X Close Button
        close_btn_top = QPushButton("✕")
        close_btn_top.setFixedSize(32, 32)
        close_btn_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_top.clicked.connect(self.reject)
        close_btn_top.setStyleSheet("""
            QPushButton { background: transparent; color: #64748B; font-size: 18px; font-weight: bold; border: none; border-radius: 16px; }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; }
        """)
        header_layout.addWidget(close_btn_top)
        self.layout.addLayout(header_layout)
        
        if is_save or is_create:
            # Project name
            name_layout = QHBoxLayout()
            name_label = QLabel("Proje Adı:")
            name_label.setFixedWidth(80)
            self.name_input = QLineEdit()
            self.name_input.setPlaceholderText("Proje adını girin...")
            self.name_input.setStyleSheet("""
                QLineEdit {
                    background-color: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 10px 14px;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #4F46E5;
                }
            """)
            name_layout.addWidget(name_label)
            name_layout.addWidget(self.name_input)
            self.layout.addLayout(name_layout)
            
            # Info
            info_text = "Yeni boş bir proje oluşturulacak." if is_create else "Proje, tüm belgeler, kodlar ve segmentlerle birlikte kaydedilir."
            info = QLabel(info_text)
            info.setStyleSheet("color: #64748B; font-size: 12px;")
            info.setWordWrap(True)
            self.layout.addWidget(info)
        else:
            # Load mode - show recent projects
            if self.recent_projects:
                projects_label = QLabel("Son Projeler:")
                projects_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500;")
                self.layout.addWidget(projects_label)
                
                self.projects_list = QListWidget()
                self.projects_list.setStyleSheet("""
                    QListWidget {
                        background-color: #F8FAFC;
                        border: 1px solid #E2E8F0;
                        border-radius: 8px;
                        padding: 8px;
                    }
                    QListWidget::item {
                        padding: 10px;
                        border-bottom: 1px solid #E2E8F0;
                    }
                    QListWidget::item:selected {
                        background-color: #E0E7FF;
                    }
                """)
                
                for proj in self.recent_projects:
                    item = QListWidgetItem(f"📁 {proj.get('name', 'Bilinmeyen')}")
                    item.setData(Qt.ItemDataRole.UserRole, proj.get('path'))
                    self.projects_list.addItem(item)
                
                self.projects_list.itemDoubleClicked.connect(self._handle_action)
                self.layout.addWidget(self.projects_list)
                
                # Browse Button for Load Mode
                browse_layout = QHBoxLayout()
                browse_layout.addStretch()
                self.browse_btn = QPushButton("📂 Bilgisayardan Gözat...")
                self.browse_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F1F5F9;
                        color: #4F46E5;
                        border: 1px solid #E2E8F0;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-size: 12px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #EEF2FF;
                        border-color: #C7D2FE;
                    }
                """)
                self.browse_btn.clicked.connect(self._handle_browse)
                browse_layout.addWidget(self.browse_btn)
                self.layout.addLayout(browse_layout)
            else:
                no_projects = QLabel("Henüz kaydedilmiş proje bulunmuyor.")
                no_projects.setStyleSheet("color: #94A3B8; font-size: 12px; font-style: italic;")
                self.layout.addWidget(no_projects)
                
                # Still show browse even if no recents
                self.browse_btn = QPushButton("📂 Bilgisayardan Gözat...")
                self.browse_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F1F5F9;
                        color: #4F46E5;
                        border: 1px solid #E2E8F0;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-size: 12px;
                    }
                """)
                self.browse_btn.clicked.connect(self._handle_browse)
                self.layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.layout.addStretch()
        
        # Footer Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Vazgeç")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 10px 24px;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        button_layout.addWidget(cancel_btn)
        
        action_btn = QPushButton(btn_text)
        action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        action_btn.clicked.connect(self._handle_action)
        action_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 32px;
                font-weight: 800;
                font-size: 14px;
            }
            QPushButton:hover { background: #4338CA; }
        """)
        button_layout.addWidget(action_btn)
        
        button_layout.addStretch()
        self.layout.addLayout(button_layout)
    
    def _handle_action(self):
        """Handle save/load action."""
        if self.mode in ('save', 'create'):
            name = self.name_input.text().strip()
            if not name:
                show_warning(self, "Uyarı", "Lütfen proje adını girin.")
                return
            self.project_name = name
        else:
            # Load mode - get selected project
            if hasattr(self, 'projects_list') and self.projects_list.currentItem():
                self.selected_project_path = self.projects_list.currentItem().data(Qt.ItemDataRole.UserRole)
            else:
                show_warning(self, "Uyarı", "Lütfen bir proje seçin.")
                return
        
        self.accept()
    
    def _handle_browse(self):
        """Open file dialog to browse for project."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Proje Seç", "", "LexiScholar Projesi (project.json);;LexiScholar Marker (*.lxs)"
        )
        if file_path:
            self.selected_project_path = file_path
            self.accept()

    def get_project_name(self) -> str:
        """Get the entered project name."""
        return self.project_name
    
    def get_selected_project(self) -> str:
        """Get the selected project path (for load mode)."""
        return self.selected_project_path
