"""Coder management dialogs for LexiScholar."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLineEdit, QLabel, QColorDialog,
    QListWidgetItem, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon
from .common.modern_dialog import ModernBaseDialog
from .common_ui import show_warning, show_info, ask_confirmation

class CoderEditDialog(ModernBaseDialog):
    """Dialog to create or edit a coder."""
    def __init__(self, parent=None, coder=None):
        super().__init__(parent, min_width=400, min_height=350)
        self.coder = coder # If None, create new
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        title_str = "Kodlayıcı Düzenle" if self.coder else "Yeni Kodlayıcı"
        header = self.build_ribbon_header("👤", title_str)
        self.layout.addWidget(header)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(10, 10, 10, 10)
        
        # Name
        form_layout.addWidget(QLabel("İsim:"))
        self.name_edit = QLineEdit(self)
        self.name_edit.setStyleSheet("padding: 8px; border: 1px solid #CBD5E1; border-radius: 6px; background: white;")
        if self.coder: self.name_edit.setText(self.coder['name'])
        form_layout.addWidget(self.name_edit)
        
        # Initials
        form_layout.addWidget(QLabel("Baş Harfler (Kısa Ad):"))
        self.initials_edit = QLineEdit(self)
        self.initials_edit.setMaxLength(3)
        self.initials_edit.setStyleSheet("padding: 8px; border: 1px solid #CBD5E1; border-radius: 6px; background: white;")
        if self.coder: self.initials_edit.setText(self.coder['initials'])
        form_layout.addWidget(self.initials_edit)
        
        # Color
        form_layout.addWidget(QLabel("Renk:"))
        color_layout = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.current_color = self.coder['color'] if self.coder else "#3498db"
        self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border-radius: 12px; border: 1px solid #CBD5E1;")
        
        btn_color = QPushButton("Renk Seç...")
        btn_color.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_color.setStyleSheet("QPushButton { background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 16px; font-weight: bold; color: #475569; } QPushButton:hover { background: #F8FAFC; border-color: #94A3B8; }")
        btn_color.clicked.connect(self._select_color)
        
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(btn_color)
        color_layout.addStretch()
        form_layout.addLayout(color_layout)
        
        self.layout.addLayout(form_layout)
        self.layout.addStretch()
        
        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        
        btn_cancel = QPushButton("İptal")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("QPushButton { background: transparent; color: #64748B; border: 1px solid #CBD5E1; border-radius: 8px; padding: 10px 20px; font-weight: bold; font-size: 13px; } QPushButton:hover { background: #F1F5F9; }")
        
        btn_save = QPushButton("Kaydet")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.accept)
        btn_save.setDefault(True)
        btn_save.setStyleSheet("QPushButton { background: #4F46E5; color: white; border: none; border-radius: 8px; padding: 10px 30px; font-weight: bold; font-size: 14px; } QPushButton:hover { background: #4338CA; }")
        
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        
        self.add_size_grip(btns)
        self.layout.addLayout(btns)
        
    def accept(self):
        """Validate input before closing."""
        name = self.name_edit.text().strip()
        initials = self.initials_edit.text().strip()
        
        if not name:
            show_warning(self, "Geçersiz İsim", "Kodlayıcı ismi boş olamaz.")
            return
        if not initials:
            show_warning(self, "Geçersiz Kısaltma", "Baş harfler (kısa ad) boş olamaz.")
            return
            
        super().accept()
        
    def _select_color(self):
        color = QColorDialog.getColor(QColor(self.current_color), self, "Renk Seç")
        if color.isValid():
            self.current_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border-radius: 12px; border: 1px solid #CBD5E1;")
            
    def get_data(self):
        return {
            'name': self.name_edit.text(),
            'initials': self.initials_edit.text(),
            'color': self.current_color
        }

class CoderManagerDialog(ModernBaseDialog):
    """Dialog to manage all coders and switch active coder."""
    def __init__(self, coder_dao, current_coder_id, parent=None):
        super().__init__(parent, min_width=500, min_height=400)
        self.coder_dao = coder_dao
        self.current_coder_id = current_coder_id
        self.selected_coder_id = current_coder_id
        
        self._setup_ui()
        self._load_coders()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header Area
        header = self.build_ribbon_header("👥", "Kodlayıcı Yönetimi")
        self.layout.addWidget(header)
        
        desc_layout = QHBoxLayout()
        desc = QLabel("Projeye erişebilecek kodlayıcıları listeleyin, ekleyin ve düzenleyin.")
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        desc_layout.addWidget(desc)
        
        self.btn_help = QPushButton("💡 Yardım")
        self.btn_help.setToolTip("Grup çalışması hakkında yardım")
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setStyleSheet("QPushButton { background: transparent; color: #4F46E5; font-weight: bold; font-size: 13px; border: none; } QPushButton:hover { text-decoration: underline; color: #4338CA; }")
        self.btn_help.clicked.connect(self._show_help)
        desc_layout.addStretch()
        desc_layout.addWidget(self.btn_help)
        self.layout.addLayout(desc_layout)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #CBD5E1; border-radius: 8px; background: white; padding: 4px; font-size: 14px;
            }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #F1F5F9; border-radius: 4px; color: #1E293B; }
            QListWidget::item:hover { background: #F8FAFC; }
            QListWidget::item:selected { background: #EEF2FF; color: #4F46E5; font-weight: bold; }
        """)
        self.layout.addWidget(self.list_widget, 1)
        
        self.layout.addSpacing(10)
        
        controls = QHBoxLayout()
        btn_add = QPushButton("Ekle")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("QPushButton { background: white; color: #10B981; border: 1px solid #10B981; border-radius: 8px; padding: 8px 20px; font-weight: bold; font-size: 13px; } QPushButton:hover { background: #ECFDF5; }")
        btn_add.clicked.connect(self._add_coder)
        
        btn_edit = QPushButton("Düzenle")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet("QPushButton { background: white; color: #4F46E5; border: 1px solid #4F46E5; border-radius: 8px; padding: 8px 20px; font-weight: bold; font-size: 13px; } QPushButton:hover { background: #EEF2FF; }")
        btn_edit.clicked.connect(self._edit_coder)
        
        btn_delete = QPushButton("Sil")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setStyleSheet("QPushButton { background: white; color: #EF4444; border: 1px solid #EF4444; border-radius: 8px; padding: 8px 20px; font-weight: bold; font-size: 13px; } QPushButton:hover { background: #FEF2F2; }")
        btn_delete.clicked.connect(self._delete_coder)
        
        controls.addWidget(btn_add)
        controls.addWidget(btn_edit)
        controls.addWidget(btn_delete)
        
        controls.addStretch()
        
        btn_select = QPushButton("Aktif Olarak Seç")
        btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select.setStyleSheet("QPushButton { background: #4F46E5; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-weight: bold; font-size: 14px; } QPushButton:hover { background: #4338CA; }")
        btn_select.clicked.connect(self._select_active)
        controls.addWidget(btn_select)
        
        self.add_size_grip(controls)
        self.layout.addLayout(controls)
        
    def _show_help(self):
        """Show contextual help for coder management."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        help_path = os.path.join(base_dir, "docs", "encyclopedia", "teamwork_reliability.html")
        if os.path.exists(help_path):
            url = QUrl.fromLocalFile(help_path)
            url.setFragment("coder-management")
            QDesktopServices.openUrl(url)
        
    def _load_coders(self):
        self.list_widget.clear()
        coders = self.coder_dao.get_all()
        for c in coders:
            item = QListWidgetItem(c['name'])
            item.setData(Qt.ItemDataRole.UserRole, c['id'])
            
            # Show "Active" marker
            if c['id'] == self.current_coder_id:
                item.setText(f"{c['name']} (AKTİF)")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled) # Prevent re-selecting active?
                # Actually let's just highlight it
                item.setForeground(QColor("#2ecc71"))
                
            self.list_widget.addItem(item)
            
    def _add_coder(self):
        dialog = CoderEditDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data['name']:
                self.coder_dao.create(data['name'], data['color'], data['initials'])
                self._load_coders()
                
    def _edit_coder(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        coder_id = item.data(Qt.ItemDataRole.UserRole)
        coder = self.coder_dao.get_by_id(coder_id)
        
        dialog = CoderEditDialog(self, coder)
        if dialog.exec():
            data = dialog.get_data()
            name = data['name'].strip()
            initials = data['initials'].strip()
            
            if not name or not initials:
                # Should be caught by CoderEditDialog.accept, but extra safety
                return
                
            self.coder_dao.update(coder_id, name, data['color'], initials)
            self._load_coders()
            
    def _delete_coder(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        coder_id = item.data(Qt.ItemDataRole.UserRole)
        if coder_id == 1:
            show_warning(self, "Hata", "Varsayılan kodlayıcı silinemez.")
            return
            
        confirm = ask_confirmation(self, "Onay", "Bu kodlayıcıyı silmek istediğinize emin misiniz?\nBu kodlayıcının yaptığı tüm kodlamalar 'Varsayılan Kodlayıcı'ya geri atanacaktır.")
        if confirm:
            self.coder_dao.delete(coder_id)
            self._load_coders()
            
    def _select_active(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        self.selected_coder_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
