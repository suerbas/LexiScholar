"""
Quote Matrix analysis dialogs.
"""

from typing import List, Dict, Tuple
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QListWidget, QListWidgetItem,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame,
    QToolButton, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QFont, QDesktopServices
from ..styles import TABLE_STYLE
from .quotes_by_variables import QuotesByVariablesResultWidget
from ..common.modern_dialog import ModernBaseDialog
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class QuoteMatrixDialog(ModernBaseDialog):
    """Selection dialog for Quote Matrix analysis."""
    def __init__(self, codes: List[Dict], variables: List[Dict], parent=None):
        super().__init__(parent, min_width=520, min_height=520)
        self.codes = codes
        self.variables = variables
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("📊", "Alıntı Matrisi Oluştur")
        self.layout.addWidget(header)

        desc = QLabel("Kodları satırlarda, değişken değerlerini sütunlarda olacak şekilde alıntıları listeleyin.")
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        self.layout.addWidget(desc)

        form_group = QGroupBox("Analiz Parametreleri")
        form_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                margin-top: 14px;
                background: rgba(255,255,255,0.7);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #334155;
                font-weight: 700;
                font-size: 13px;
            }
            QLabel { color: #334155; font-size: 12px; font-weight: 600; margin-bottom: 2px; }
            QListWidget {
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                padding: 4px;
            }
            QListWidget::item { 
                padding: 8px; 
                border-radius: 4px; 
                color: #1E293B;
            }
            QListWidget::item:hover { background: #F1F5F9; }
            QListWidget::indicator {
                width: 18px;
                height: 18px;
                border: 1.5px solid #CBD5E1;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::indicator:checked {
                background-color: #4F46E5;
                border-color: #4F46E5;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjIwIDYgOSAxNyA0IDEyIj48L3BvbHlsaW5lPjwvc3ZnPg==);
            }
            QListWidget::indicator:unchecked:hover {
                border-color: #94A3B8;
            }
            QComboBox {
                min-height: 42px;
                padding: 0px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                font-size: 13px;
                color: #0F172A;
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #4F46E5;
                selection-color: white;
                color: #0F172A;
                font-size: 13px;
                border: 1px solid #E2E8F0;
                outline: none;
            }
        """)
        form_layout = QVBoxLayout(form_group)
        form_layout.setContentsMargins(18, 28, 18, 18)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("1. Analiz Edilecek Kodları Seçin:"))
        self.code_list = QListWidget()
        self.code_list.setMinimumHeight(180)
        for code in sorted(self.codes, key=lambda x: x['name'].lower()):
            item = QListWidgetItem(code['name'])
            item.setData(Qt.ItemDataRole.UserRole, code['id'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.code_list.addItem(item)
        form_layout.addWidget(self.code_list)

        sel_btns = QHBoxLayout()
        btn_all = QPushButton("Tümünü Seç")
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(self._select_all_codes)
        btn_all.setStyleSheet("""
            QPushButton {
                background: #F8FAFC;
                color: #334155;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 8px 14px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)

        btn_none = QPushButton("Seçimi Kaldır")
        btn_none.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_none.clicked.connect(self._select_no_codes)
        btn_none.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 14px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        sel_btns.addWidget(btn_all)
        sel_btns.addWidget(btn_none)
        sel_btns.addStretch()
        form_layout.addLayout(sel_btns)
        
        form_layout.addSpacing(10)

        form_layout.addWidget(QLabel("2. Sütun Değişkenini Seçin:"))
        self.var_combo = QComboBox()
        for var in self.variables:
            self.var_combo.addItem(var['name'], var['id'])
        form_layout.addWidget(self.var_combo)

        self.layout.addWidget(form_group)
        self.layout.addSpacing(10)

        btns = QHBoxLayout()
        btns.addStretch()

        ok_btn = QPushButton("Matrisi Oluştur")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
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
        btns.addWidget(ok_btn)
        
        btns.addStretch()
        self.layout.addLayout(btns)
        
    def get_selection(self) -> Tuple[List[int], int, str]:
        sel_codes = [self.code_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.code_list.count()) if self.code_list.item(i).checkState() == Qt.CheckState.Checked]
        return sel_codes, self.var_combo.currentData(), self.var_combo.currentText()

    def _select_all_codes(self):
        for i in range(self.code_list.count()):
            self.code_list.item(i).setCheckState(Qt.CheckState.Checked)

    def _select_no_codes(self):
        for i in range(self.code_list.count()):
            self.code_list.item(i).setCheckState(Qt.CheckState.Unchecked)

class QuoteMatrixResultWidget(QFrame):
    """Displays coded segments counts in a matrix as a tab widget."""
    def __init__(self, var_name: str, matrix_data: Dict, parent=None):
        super().__init__(parent)
        self.var_name = var_name; self.data = matrix_data
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ── Grid ─────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        
        # Apply modern, clean styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8fafc;
                border: none;
                gridline-color: #e2e8f0;
                font-size: 13px;
                color: #1e293b;
            }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; outline: none; }
            QTableWidget::item:selected { background-color: #eff6ff; color: #1e40af; outline: none; }
            QTableWidget::item:focus { outline: none; border: none; }
            QHeaderView::section {
                background-color: #f8fafc; padding: 10px; border: none;
                border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;
                font-weight: 700; color: #64748b; font-size: 11px;
                text-transform: uppercase;
            }
            QTableCornerButton::section { background: #f8fafc; border: none; }
        """)
        
        cols, rows, mtx = self.data['groups'], self.data['codes'], self.data['matrix']
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([str(g) for g in cols])
        
        # Calculate hierarchy for vertical headers
        all_codes = rows
        if self.parent() and hasattr(self.parent(), 'code_dao'):
            all_codes = self.parent().code_dao.get_all()
            
        def get_level(c_id):
            level = 0
            curr = next((c for c in all_codes if c['id'] == c_id), None)
            while curr and curr.get('parent_id'):
                level += 1
                curr = next((c for c in all_codes if c['id'] == curr['parent_id']), None)
            return level

        for r_idx, row in enumerate(rows):
            full_name = row['name']
            display_name = (full_name[:40] + "...") if len(full_name) > 40 else full_name
            
            level = get_level(row['id'])
            is_parent = any(c.get('parent_id') == row['id'] for c in all_codes)
            
            indent = "    " * level
            prefix = "▪ " if level > 0 else ""
            
            header_item = QTableWidgetItem(f"{indent}{prefix}{display_name}")
            header_item.setToolTip(full_name) # Always set tooltip to full name
            header_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            
            if is_parent:
                font = header_item.font()
                font.setBold(True)
                header_item.setFont(font)
            self.table.setVerticalHeaderItem(r_idx, header_item)

        # Do not stretch columns generically, let them fit content but with a minimum
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        for r_idx, row_codes in enumerate(mtx):
            for c_idx, count in enumerate(row_codes):
                item = QTableWidgetItem(str(count) if count > 0 else "-"); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, (rows[r_idx]['id'], cols[c_idx]))
                if count > 0:
                    # Heatmap style badge
                    item.setBackground(QColor("#e0f2fe"))
                    item.setForeground(QColor("#0369a1"))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                else:
                    item.setForeground(QColor("#94a3b8"))
                self.table.setItem(r_idx, c_idx, item)
                
        self.table.resizeColumnsToContents()
        for c in range(self.table.columnCount()):
            if self.table.columnWidth(c) < 120:
                self.table.setColumnWidth(c, 120)
                
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Remove focus rectangle on click
        layout.addWidget(self.table)
        
    def _export_to_excel(self):
        """Export matrix content to CSV (Excel compatible)."""
        from PyQt6.QtWidgets import QFileDialog
        import csv
        
        path, _ = QFileDialog.getSaveFileName(self, "Excel'e Aktar", f"alinti_matrisi_{self.var_name}.csv", "CSV Files (*.csv)")
        if not path: return
        
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, delimiter=';')
                
                cols = self.data['groups']
                rows = self.data['codes']
                mtx = self.data['matrix']
                
                header = [f"Kod / {self.var_name}"] + [str(g) for g in cols]
                writer.writerow(header)
                
                for r_idx, row_codes in enumerate(mtx):
                    writer.writerow([rows[r_idx]['name']] + [str(c) for c in row_codes])
                    
            show_info(self, "Başarılı", f"Veriler başarıyla aktarıldı:\n{path}")
        except Exception as e:
            show_error(self, "Hata", f"Dışa aktarma başarısız oldu:\n{str(e)}")

    def setup_header_controls(self, layout):
        """Add custom header controls to the main window's blue ribbon."""
        from PyQt6.QtWidgets import QPushButton
        layout.addSpacing(10)
        export_btn = QPushButton("📄 Excel'e Aktar")
        export_btn.setToolTip("Matrisi CSV olarak dışa aktar")
        export_btn.setFixedHeight(32)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        export_btn.clicked.connect(self._export_to_excel)
        layout.addWidget(export_btn)
        layout.addSpacing(2)
        # Note: main_window.add_analysis_tab auto-registers this widget as
        # persistent in header._persistent_widgets so it survives detach/dock.



    def _on_cell_clicked(self, row, col):
        data = self.table.item(row, col).data(Qt.ItemDataRole.UserRole)
        if data:
            c_id, g_val = data
            quotes = self.data.get('quotes', {}).get(f"{c_id}:{g_val}", [])
            if quotes:
                # Use clean name (remove prefix/indent)
                clean_name = self.table.verticalHeaderItem(row).text().strip(" ▪")
                
                # Show in a dialog for now, as clicking cell is a sub-detail action
                # Or ideally, open another tab? Let's keep it simple for now as a dialog 
                # or better, use the Widget in a Dialog wrapper
                
                from PyQt6.QtWidgets import QDialog
                d = QDialog(self)
                d.setWindowTitle(f"Alıntılar: {clean_name}")
                d.resize(800, 600)
                l = QVBoxLayout(d); l.setContentsMargins(0,0,0,0)
                w = QuotesByVariablesResultWidget(clean_name, self.var_name, {'groups': {g_val: quotes}, 'total_segments': len(quotes)}, d)
                l.addWidget(w)
                d.exec()
            else: show_info(self, "Bilgi", "Bu hücre için alıntı bulunamadı.")
