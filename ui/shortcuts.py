"""
LexiScholar Shortcut Manager
Centralized management for application-wide keyboard shortcuts.
"""

from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import QWidget, QApplication

class ShortcutManager(QObject):
    """
    Central manager for keyboard shortcuts.
    Allows easy remapping and centralized documentation.
    """
    
    # Define actions and default keys
    ACTIONS = {
        # Project
        'project_save': {'key': 'Ctrl+S', 'desc': 'Projeyi Kaydet'},
        'project_journal': {'key': 'Ctrl+J', 'desc': 'Proje Günlüğü'},
        'app_quit': {'key': 'Ctrl+Q', 'desc': 'Çıkış'},
        
        # Coding
        'code_new': {'key': 'Ctrl+Shift+C', 'desc': 'Yeni Kod Oluştur'},
        'code_quick': {'key': 'Ctrl+K', 'desc': 'Hızlı Kodla (Seçili Kod ile)'},
        'code_invivo': {'key': 'Ctrl+Shift+I', 'desc': 'In-Vivo Kodla'},
        'code_search': {'key': 'Ctrl+Shift+F', 'desc': 'Kod Ara'},
        
        # Memos
        'memo_new': {'key': 'Ctrl+M', 'desc': 'Yeni Not Ekle'},
        
        # Editing
        'edit_undo': {'key': 'Ctrl+Z', 'desc': 'Geri Al'},
        'edit_redo': {'key': 'Ctrl+Y', 'desc': 'Yinele'},
        'edit_delete': {'key': 'Delete', 'desc': 'Seçili Öğeyi Sil'},
        'edit_rename': {'key': 'F2', 'desc': 'Yeniden Adlandır'},
        
        # Navigation / Panels
        'nav_focus_browser': {'key': 'Alt+1', 'desc': 'Belge Okuyucuya Odaklan'},
        'nav_focus_codes': {'key': 'Alt+2', 'desc': 'Kod Ağacına Odaklan'},
        'nav_focus_docs': {'key': 'Alt+3', 'desc': 'Belge Ağacına Odaklan'},
        'nav_focus_segments': {'key': 'Alt+4', 'desc': 'Segment Listesine Odaklan'},
        'view_layout_toggle': {'key': 'Ctrl+L', 'desc': 'Arayüz Düzenini Değiştir'},
        
        # Help
        'help_manual': {'key': 'F1', 'desc': 'Kullanım Kılavuzu'},
        'help_shortcuts': {'key': 'Ctrl+Shift+H', 'desc': 'Kısayol Listesi'}
    }

    def __init__(self, window):
        super().__init__(parent=window)
        self.window = window
        self._shortcuts = {}
        
    def register_all(self):
        """Register all defined shortcuts to the main window."""
        # Project
        self._add('project_save', self.window._save_project)
        self._add('project_journal', self.window._show_journal_dialog)
        # self._add('app_quit', self.window.close) # Let standard close handle it
        
        # Coding (Check existence of methods before connecting)
        if hasattr(self.window, '_quick_code'):
             self._add('code_quick', self.window._quick_code)
             
        if hasattr(self.window, '_create_code_interactive'):
             self._add('code_new', self.window._create_code_interactive)
        elif hasattr(self.window, 'code_tree'):
             self._add('code_new', lambda: self.window.code_tree._create_code(None))

        # Memos
        if hasattr(self.window, '_add_memo_interactive'):
            self._add('memo_new', self.window._add_memo_interactive)
        
        # Editing
        if hasattr(self.window, '_undo'):
            self._add('edit_undo', self.window._undo)
        if hasattr(self.window, '_redo'):
            self._add('edit_redo', self.window._redo)
        if hasattr(self.window, '_delete_active_item'):
            self._add('edit_delete', self.window._delete_active_item)
        if hasattr(self.window, '_rename_active_item'):
             self._add('edit_rename', self.window._rename_active_item)
        elif hasattr(self.window, 'code_tree'): # Fallback logic
             # We might need a smarter dispatcher for Rename like Delete has
             pass 

        # Navigation
        self._add('nav_focus_browser', lambda: self._focus_panel(self.window.document_browser))
        self._add('nav_focus_codes', lambda: self._focus_panel(self.window.code_tree))
        self._add('nav_focus_docs', lambda: self._focus_panel(self.window.document_tree))
        self._add('nav_focus_segments', lambda: self._focus_panel(self.window.retrieved_segments))
        
        if hasattr(self.window, '_toggle_layout'):
            self._add('view_layout_toggle', self.window._toggle_layout)
            
        # Help
        if hasattr(self.window, '_show_manual'):
            self._add('help_manual', self.window._show_manual)
            
        self._add('help_shortcuts', self.show_cheat_sheet)

    def _add(self, action_id, callback):
        """Helper to create QShortcut."""
        if action_id in self.ACTIONS:
            data = self.ACTIONS[action_id]
            seq = QKeySequence(data['key'])
            shortcut = QShortcut(seq, self.window)
            shortcut.activated.connect(callback)
            self._shortcuts[action_id] = shortcut
            
    def _focus_panel(self, widget):
        """Focus specific panel widget."""
        if widget:
            # Try to focus the specific inner widget if known, else the container
            if hasattr(widget, 'tree'):
                widget.tree.setFocus()
            elif hasattr(widget, 'text_edit'):
                widget.text_edit.setFocus()
            elif hasattr(widget, 'list_widget'):
                widget.list_widget.setFocus()
            else:
                widget.setFocus()

    def show_cheat_sheet(self):
        """Show a dialog with all available shortcuts."""
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHBoxLayout, QVBoxLayout, QHeaderView, QLabel, QPushButton, QFrame
        from .common.modern_dialog import ModernBaseDialog
        
        dialog = ModernBaseDialog(self.window, min_width=550, min_height=650)
        dialog._setup_base_ui()
        dialog.layout.setContentsMargins(0, 0, 0, 20)
        dialog.layout.setSpacing(15)
        
        # Header Area
        header = dialog.build_ribbon_header("⌨️", "Klavye Kısayolları")
        dialog.layout.addWidget(header)
        
        content_wrapper = QFrame()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(20, 10, 20, 10)
        
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Eylem", "Kısayol Tuşu"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        from .styles.main_qss import TABLE_STYLE
        table.setStyleSheet(TABLE_STYLE + """
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 8px; alternate-background-color: #F8FAFC; }
            QTableWidget::item { padding: 8px 12px; font-size: 13px; color: #334155; }
            QHeaderView::section {
                background-color: #F1F5F9;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #CBD5E1;
                font-weight: 700;
                color: #475569;
                font-size: 11px;
                text-transform: uppercase;
            }
        """)
        table.setAlternatingRowColors(True)
        
        table.setRowCount(len(self.ACTIONS))
        row = 0
        for action_id, data in self.ACTIONS.items():
            item_desc = QTableWidgetItem(data['desc'])
            
            item_key = QTableWidgetItem(data['key'].replace('Ctrl', 'Ctrl ').replace('Shift', 'Shift ').replace('Alt', 'Alt '))
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_key.setForeground(Qt.GlobalColor.darkBlue)
            # Give keys a slightly bold "badge" feel via font
            f = item_key.font()
            f.setBold(True)
            f.setPointSize(10)
            item_key.setFont(f)
            
            table.setItem(row, 0, item_desc)
            table.setItem(row, 1, item_key)
            row += 1
            
        content_layout.addWidget(table)
        dialog.layout.addWidget(content_wrapper)
        
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 0, 20, 0)
        btn_layout.addStretch()
        btn_ok = QPushButton("Kapat")
        btn_ok.setFixedWidth(100)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton { background: #E2E8F0; color: #475569; border: none; border-radius: 8px; padding: 10px; font-weight: 700; font-size: 13px; }
            QPushButton:hover { background: #CBD5E1; color: #1E293B; }
        """)
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)
        dialog.layout.addLayout(btn_layout)
        
        dialog.exec()
