import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame,
    QFormLayout, QScrollArea, QWidget, QCheckBox,
    QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from .common.modern_dialog import ModernBaseDialog
from .styles import COLORS, get_color
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class VariableManagerDialog(ModernBaseDialog):
    """Dialog for defining and deleting document variables, modernized."""
    
    def __init__(self, var_dao, parent=None):
        super().__init__(parent, min_width=550, min_height=600)
        self.var_dao = var_dao
        self._setup_ui()

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("🏷️", "Değişken Yönetimi")
        self.layout.addWidget(header)

        # Form for new variable
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('bg_main')};
                border: 1px solid {get_color('border')};
                border-radius: 12px;
                padding: 10px;
            }}
            QLabel {{ color: {get_color('text_secondary')}; font-weight: 700; font-size: 12px; border: none; background: transparent; }}
            QLineEdit, QComboBox {{
                border: 1px solid {get_color('border_hover')};
                border-radius: 8px;
                padding: 8px 10px;
                background: white;
                font-size: 13px;
                color: {get_color('text_primary')};
            }}
        """)
        form_layout = QVBoxLayout(form_frame)
        
        form_layout.addWidget(QLabel("YENİ DEĞİŞKEN EKLE"))
        
        # Row 1: Name and Type
        input_row1 = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Değişken Adı (Örn: Yaş, Şehir)")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Metin", "Sayı", "Mantıksal (Evet/Hayır)"])
        
        input_row1.addWidget(QLabel("Ad:"))
        input_row1.addWidget(self.name_input)
        input_row1.addWidget(QLabel("Tip:"))
        input_row1.addWidget(self.type_combo)
        form_layout.addLayout(input_row1)
        
        # Row 2: Parent Selection and Add Button
        input_row2 = QHBoxLayout()
        self.parent_combo = QComboBox()
        self._update_parent_combo()
        
        self.add_btn = QPushButton("Ekle")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_variable)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 700;
            }
            QPushButton:hover { background: #4338CA; }
        """)
        
        input_row2.addWidget(QLabel("Kategori:"))
        input_row2.addWidget(self.parent_combo)
        input_row2.addStretch()
        input_row2.addWidget(self.add_btn)
        form_layout.addLayout(input_row2)
        
        self.layout.addWidget(form_frame)
        
        # Tree of existing variables
        self.layout.addWidget(QLabel("<b>Tanımlı Değişkenler</b>"))
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Ad", "Tip"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                border: 1px solid {get_color('border')};
                border-radius: 12px;
                background: white;
                outline: none;
            }}
            QHeaderView::section {{
                background-color: {get_color('bg_main')};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {get_color('border')};
                font-weight: 700;
                color: {get_color('text_secondary')};
            }}
        """)
        self.layout.addWidget(self.tree)
        
        # Footer
        footer = QHBoxLayout()
        
        self.delete_btn = QPushButton("🗑️ Seçileni Sil")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self._delete_variable)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                color: #DC2626;
                padding: 8px 16px;
                border: 1px solid #FECACA;
                border-radius: 8px;
                font-weight: 600;
                background: transparent;
            }
            QPushButton:hover { background: #FEF2F2; border-color: #EF4444; }
        """)
        footer.addWidget(self.delete_btn)
        
        footer.addStretch()
        
        self.close_btn = QPushButton("Kapat")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: none;
                border-radius: 8px;
                padding: 8px 32px;
                font-weight: 700;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)
        footer.addWidget(self.close_btn)
        
        self.layout.addLayout(footer)
        
        self._refresh_tree()
        
    def _update_parent_combo(self):
        """Update the list of potential parent variables."""
        self.parent_combo.clear()
        self.parent_combo.addItem("(Yok - Üst Seviye)", None)
        variables = self.var_dao.get_all()
        for v in variables:
            # For simplicity, we only allow 1 level of nesting for now,
            # or we could allow deep nesting by showing hierarchy in combo
            self.parent_combo.addItem(v['name'], v['id'])

    def _refresh_tree(self):
        """Load variables from database and display in tree."""
        self.tree.clear()
        hierarchy = self.var_dao.get_hierarchy()
        
        type_map = {'text': 'Metin', 'integer': 'Sayı', 'boolean': 'Mantıksal'}
        
        def add_item(var, parent_item=None):
            item = QTreeWidgetItem([
                var['name'], 
                type_map.get(var['data_type'], 'Metin')
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, var['id'])
            
            if parent_item:
                parent_item.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
                
            for child in var.get('children', []):
                add_item(child, item)
            
            item.setExpanded(True)
            
        for var in hierarchy:
            add_item(var)
        
        # Synchronize combo after data change
        self._update_parent_combo()

    def _add_variable(self):
        """Add a new variable to database."""
        name = self.name_input.text().strip()
        if not name:
            show_warning(self, "Hata", "Lütfen bir isim girin.")
            return
            
        type_idx = self.type_combo.currentIndex()
        data_type = ['text', 'integer', 'boolean'][type_idx]
        
        parent_id = self.parent_combo.currentData()
        
        try:
            self.var_dao.create(name, data_type, parent_id)
            self.name_input.clear()
            self._refresh_tree()
        except Exception as e:
            show_error(self, "Hata", f"Değişken oluşturulamadı: {e}")
            
    def _delete_variable(self):
        """Delete selected variable."""
        item = self.tree.currentItem()
        if not item:
            return
            
        var_id = item.data(0, Qt.ItemDataRole.UserRole)
        var_name = item.text(0)
        
        confirm = ask_confirmation(
            self, "Onay", 
            f"'{var_name}' değişkenini silmek istediğinize emin misiniz? "
            "Bu değişkene ait TÜM alt değişkenler ve belge değerleri silinecektir!"
        )
        
        if confirm :
            if self.var_dao.delete(var_id):
                self._refresh_tree()

class DocumentVariablesDialog(ModernBaseDialog):
    """Dialog for setting variable values for a specific document, modernized."""
    
    def __init__(self, doc_id, doc_title, var_dao, value_dao, parent=None):
        super().__init__(parent, min_width=500, min_height=450)
        self.doc_id = doc_id
        self.doc_title = doc_title
        self.var_dao = var_dao
        self.value_dao = value_dao
        self._setup_ui()

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header Area
        header_layout = QHBoxLayout()
        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel(f"Belge Değişkenleri: {self.doc_title}")
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0F172A;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Close Button
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

        desc = QLabel("Bu belgeye ait değişken değerlerini aşağıdan güncelleyebilirsiniz.")
        desc.setStyleSheet("color: #64748B; font-size: 12px; margin-bottom: 5px;")
        self.layout.addWidget(desc)
        
        # Scroll area for many variables
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget { background: transparent; }
            QLabel { color: #334155; font-size: 13px; font-weight: 600; }
            QLineEdit, QCheckBox {
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 10px;
                background: white;
                color: #0F172A;
            }
            QLineEdit:focus { border: 2px solid #4F46E5; }
        """)
        self.form_layout = QFormLayout(content_widget)
        self.form_layout.setContentsMargins(10, 10, 10, 10)
        self.form_layout.setSpacing(12)
        
        # Load variables and existing values
        self.hierarchy = self.var_dao.get_hierarchy()
        self.existing_values = self.value_dao.get_values_by_document(self.doc_id)
        
        self.inputs = {} # variable_id -> input widget
        
        def add_vars_to_layout(vars_list, level=0):
            for var in vars_list:
                v_id = var['id']
                v_type = var['data_type']
                v_name = var['name']
                current_val = self.existing_values.get(v_id, "")
                
                # Visual hierarchy: Indentation
                label_text = f"{'  ' * level}• {v_name}" if level > 0 else f"{v_name}"
                
                # If it's a parent (has children), it's just a category
                if var.get('children'):
                    cat_label = QLabel(label_text.upper())
                    cat_label.setStyleSheet("color: #4F46E5; font-weight: 800; font-size: 11px; margin-top: 10px;")
                    self.form_layout.addRow(cat_label, QLabel(""))
                    add_vars_to_layout(var['children'], level + 1)
                    continue

                if v_type == 'boolean':
                    cb = QCheckBox()
                    cb.setChecked(current_val.lower() == 'true' or current_val == '1')
                    self.inputs[v_id] = cb
                    self.form_layout.addRow(label_text, cb)
                elif v_type == 'integer':
                    le = QLineEdit()
                    le.setText(str(current_val) if current_val is not None else "")
                    le.setPlaceholderText("Sayı")
                    self.inputs[v_id] = le
                    self.form_layout.addRow(label_text, le)
                else: # text
                    le = QLineEdit()
                    le.setText(str(current_val) if current_val is not None else "")
                    le.setPlaceholderText("Metin")
                    self.inputs[v_id] = le
                    self.form_layout.addRow(label_text, le)

        add_vars_to_layout(self.hierarchy)
                
        scroll.setWidget(content_widget)
        self.layout.addWidget(scroll)
        
        if not self.hierarchy:
            warn = QLabel("Henüz tanımlı değişken yok.\nLütfen önce 'Değişken Yönetimi'nden değişken ekleyin.")
            warn.setStyleSheet("color: #64748B; font-style: italic;")
            self.layout.addWidget(warn)
        
        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        
        self.cancel_btn = QPushButton("Vazgeç")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 700;
            }
            QPushButton:hover { background: #F8FAFC; }
        """)
        
        self.save_btn = QPushButton("✅ Kaydet")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save_values)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 32px;
                font-weight: 800;
            }
            QPushButton:hover { background: #4338CA; }
        """)
        
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)
        btns.addStretch()
        self.layout.addLayout(btns)
        
    def _save_values(self):
        """Save entered values to database."""
        success = True
        for v_id, widget in self.inputs.items():
            # Explicitly check widget type or attributes to avoid lint errors
            if hasattr(widget, 'isChecked'):
                val = "true" if widget.isChecked() else "false"
            elif hasattr(widget, 'text'):
                val = widget.text().strip()
            else:
                val = ""
                
            if not self.value_dao.set_value(self.doc_id, v_id, val):
                success = False
                
        if success:
            self.accept()
        else:
            show_error(self, "Hata", "Bazı değerler kaydedilemedi.")

class NaturalTableWidgetItem(QTableWidgetItem):
    """Table widget item that sorts naturally (e.g., K2 relates to K10 correctly)."""
    def __lt__(self, other):
        if hasattr(self, 'data') and hasattr(other, 'data'):
            t1 = self.text()
            t2 = other.text()
            
            def convert(text):
                return int(text) if text.isdigit() else text.lower()
            
            def alphanumeric_key(key):
                return [convert(c) for c in re.split('([0-9]+)', key)]
            
            return alphanumeric_key(t1) < alphanumeric_key(t2)
        return super().__lt__(other)

class DataEditorWidget(QWidget):
    """Spreadsheet-like editor for document variables."""
    
    def __init__(self, doc_dao, var_dao, value_dao, parent=None):
        super().__init__(parent)
        self.doc_dao = doc_dao
        self.var_dao = var_dao
        self.value_dao = value_dao
        
        self.setWindowTitle("Veri Editörü (Değişkenler)")
        self.setMinimumSize(800, 600)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)
        
        # Modern Support Header
        info_frame = QFrame()
        from .styles.palette import get_color
        info_frame.setStyleSheet(f"background-color: {get_color('primary_50')}; border: 1px solid {get_color('border')}; border-radius: 8px;")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 8, 15, 8)
        info_layout.setSpacing(20)
        
        info_msg = QLabel("<b>Değişken Veri Editörü:</b> Veritabanını Excel gibi kullanın. Hücrelere çift tıklayarak metin/sayı değerlerini güncelleyebilirsiniz. "
                          "Değişiklikler anında kaydedilir (mavi renkli 'Belge Adı' sütunu salt okunurdur).")
        info_msg.setWordWrap(True)
        info_msg.setStyleSheet("color: #4338CA; font-size: 11.5px; line-height: 1.4;")
        info_layout.addWidget(info_msg, 4) # Take most space
        
        # Refresh Button integrated into info box
        self.refresh_btn = QPushButton(" Yenile 🔄 ")
        self.refresh_btn.setMinimumHeight(30)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: 700;
                font-size: 11px;
                color: {COLORS['primary_700']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_400']};
                color: {COLORS['text_primary']};
            }}
        """)
        self.refresh_btn.clicked.connect(self._load_data)
        info_layout.addWidget(self.refresh_btn, 0) # Fixed size on the right
        
        self.layout.addWidget(info_frame)
        
        # Table setup
        self.table = QTableWidget()
        self.table.setSortingEnabled(False) # Disable during initial load
        self.table.itemChanged.connect(self._on_item_changed)
        self.layout.addWidget(self.table)
        
        self._load_data()
        
    def _load_data(self):
        """Load all documents and variables into table."""
        self.table.blockSignals(True) # Prevent save during build
        
        self.documents = self.doc_dao.get_all()
        self.variables = self.var_dao.get_all()
        self.values = self.value_dao.get_all_document_values()
        
        # Matrix: [document_id][variable_id] = value
        self.val_matrix = {}
        for row in self.values:
            d_id = row['document_id']
            v_id = row['variable_id']
            if d_id not in self.val_matrix:
                self.val_matrix[d_id] = {}
            self.val_matrix[d_id][v_id] = row['value']
            
        # Headers
        # Flat list for col indexing, but names show hierarchy
        self.flat_vars = []
        def flatten(vars_list, prefix=""):
            for var in vars_list:
                name = f"{prefix}{var['name']}"
                # Only add to editor if it's a leaf node (no children)
                if not var.get('children'):
                    self.flat_vars.append({**var, 'display_name': name})
                else:
                    flatten(var['children'], f"{name} > ")
        
        flatten(self.var_dao.get_hierarchy())
        
        self.table.setColumnCount(len(self.flat_vars) + 1)
        self.table.setRowCount(len(self.documents))
        
        headers = ["Belge Adı"] + [v['display_name'] for v in self.flat_vars]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Populate rows
        for r, doc in enumerate(self.documents):
            d_id = doc['id']
            
            # Col 0: Doc Title (read only) - Use NaturalTableWidgetItem
            item_title = NaturalTableWidgetItem(doc['title'])
            item_title.setFlags(item_title.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_title.setBackground(QColor("#E0F2FE")) # Light Blue (matches "mavi" in help text)
            item_title.setData(Qt.ItemDataRole.UserRole, d_id) # Store doc id
            self.table.setItem(r, 0, item_title)
            
            # Columns 1+: Variables
            for c, var in enumerate(self.flat_vars):
                v_id = var['id']
                v_val = self.val_matrix.get(d_id, {}).get(v_id, "")
                
                # Use NaturalTableWidgetItem for consistency in all columns
                item = NaturalTableWidgetItem(str(v_val) if v_val is not None else "")
                item.setData(Qt.ItemDataRole.UserRole, (d_id, v_id)) # Store ids
                
                # Visual hint for types
                if var['data_type'] == 'boolean':
                    item.setToolTip("Metin olarak 'true' veya 'false' giriniz")
                elif var['data_type'] == 'integer':
                    item.setToolTip("Sayı giriniz")
                
                self.table.setItem(r, c + 1, item)
        
        # Sort by default on doc names (Column 0, Ascending)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table.setSortingEnabled(True)
        
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        if self.table.columnWidth(0) < 200:
            self.table.setColumnWidth(0, 200) # Minimum width for Document Name
        
        self.table.blockSignals(False)
        
    def _on_item_changed(self, item):
        """Auto-save changes to database."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, tuple):
            return
            
        d_id, v_id = data
        new_val = item.text().strip()
        
        # Basic validation (optional, can be improved)
        if self.value_dao.set_value(d_id, v_id, new_val):
            # Optional: feedback via statusbar if we had access to it
            pass
        else:
            show_warning(self, "Hata", "Değer kaydedilemedi.")
