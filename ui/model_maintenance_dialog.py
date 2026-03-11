"""
Model Maintenance Dialog for LexiScholar.
Allows users to select specific AI models to download/update and view their sizes.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from ui.common.modern_dialog import ModernBaseDialog
from ui.styles import get_color, COLORS

class ModelMaintenanceDialog(ModernBaseDialog):
    """
    Dialog for selective AI model updates with size information.
    """
    def __init__(self, parent, models_report):
        super().__init__(parent, min_width=500, min_height=400)
        self.models_report = models_report
        self.selected_models = []
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header
        header = self.build_ribbon_header("🧠", "Dil Modelleri Güncellemesi")
        self.layout.addWidget(header)
        
        # Description
        desc_label = QLabel("Bazı lokal dil modelleri eksik veya güncel değil.\nİndirmek istediğiniz modelleri seçiniz:")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 13px; margin: 10px 0;")
        self.layout.addWidget(desc_label)
        
        # Scroll Area for models
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: 1px solid {get_color('border')}; border-radius: 8px; background: white; }}
            QScrollBar:vertical {{ width: 8px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: {get_color('border')}; border-radius: 4px; }}
        """)
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(12)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        
        self.checkboxes = {}
        
        # Filter only missing or outdated models
        models_to_list = [
            item for item in self.models_report.get("checked", [])
            if item.get("status") in {"missing", "outdated"}
        ]
        
        for model in models_to_list:
            item_frame = QFrame()
            item_frame.setStyleSheet(f"QFrame {{ background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; }}")
            item_layout = QHBoxLayout(item_frame)
            
            cb = QCheckBox(model['label'])
            cb.setChecked(True) # Default all on
            cb.setStyleSheet(f"font-weight: 600; color: {get_color('text_primary')};")
            self.checkboxes[model['model_id']] = cb
            
            size_mb = model.get('size_bytes', 0) / (1024 * 1024)
            size_label = QLabel(f"{size_mb:.1f} MB")
            size_label.setStyleSheet(f"color: {get_color('text_muted')}; font-size: 11px;")
            
            item_layout.addWidget(cb)
            item_layout.addStretch()
            item_layout.addWidget(size_label)
            
            self.content_layout.addWidget(item_frame)
            
        self.content_layout.addStretch()
        scroll.setWidget(content_widget)
        self.layout.addWidget(scroll)
        
        # Selection Controls
        select_layout = QHBoxLayout()
        btn_all = QPushButton("Tümünü Seç")
        btn_none = QPushButton("Seçimleri Kaldır")
        
        btn_style = f"""
            QPushButton {{ 
                background: transparent; color: {get_color('primary')}; 
                border: none; font-size: 12px; font-weight: 600; 
            }}
            QPushButton:hover {{ text-decoration: underline; }}
        """
        btn_all.setStyleSheet(btn_style)
        btn_none.setStyleSheet(btn_style)
        
        btn_all.clicked.connect(self._select_all)
        btn_none.clicked.connect(self._deselect_all)
        
        select_layout.addWidget(btn_all)
        select_layout.addWidget(btn_none)
        select_layout.addStretch()
        self.layout.addLayout(select_layout)
        
        # Footer
        footer = QHBoxLayout()
        btn_cancel = QPushButton("İptal")
        btn_update = QPushButton("Güncelle")
        
        btn_cancel.setFixedSize(100, 36)
        btn_update.setFixedSize(120, 36)
        
        btn_cancel.setStyleSheet(f"""
            QPushButton {{ background: white; border: 1px solid {get_color('border')}; border-radius: 6px; color: {get_color('text_secondary')}; font-weight: 600; }}
            QPushButton:hover {{ background: {get_color('bg_hover')}; }}
        """)
        
        btn_update.setStyleSheet(f"""
            QPushButton {{ background: {get_color('primary')}; border: none; border-radius: 6px; color: white; font-weight: bold; }}
            QPushButton:hover {{ background: {get_color('primary_dark')}; }}
        """)
        
        btn_cancel.clicked.connect(self.reject)
        btn_update.clicked.connect(self._on_update)
        
        footer.addStretch()
        footer.addWidget(btn_cancel)
        footer.addWidget(btn_update)
        self.layout.addLayout(footer)
        
    def _select_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(True)
            
    def _deselect_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)
            
    def _on_update(self):
        self.selected_models = [m_id for m_id, cb in self.checkboxes.items() if cb.isChecked()]
        if not self.selected_models:
            from ui.common_ui import show_warning
            show_warning(self, "Seçim Gerekli", "Lütfen güncellenecek en az bir model seçiniz.")
            return
        self.accept()
        
    def get_selected_models(self):
        return self.selected_models
