"""
Model Populator Mixin for Document Tree
Handles the recursive building and refreshing of the tree model.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QColor, QTextDocument
from ..icons import IconProvider
import re

class DocumentTreeModelPopulatorMixin:
    """Provides methods for populating and updating the DocumentTree model."""
    
    def _refresh_data(self):
        """Re-fetch data from DB and update tree UI."""
        if self.doc_dao and self.folder_dao:
            docs = self.doc_dao.get_all()
            folders = self.folder_dao.get_all()
            self.populate_tree(docs, folders)

    def _get_doc_icon(self, file_type):
        icon_map = {
            'pdf': '📕', 
            'docx': '📘', 
            'doc': '📘',
            'txt': '📄', 
            'rtf': '📝', 
            'odt': '📝',
            'sav': '📊',
            'xls': '📊', 
            'xlsx': '📊',
            'transcription': '🎙️'
        }
        return icon_map.get(file_type, '📄')

    def add_folder(self, folder_id: int, name: str, parent_item=None):
        """Add a folder to the tree with real icons."""
        is_updating_prev = self._is_updating
        self._is_updating = True
        try:
            item = QStandardItem(name)
            item.setEditable(True)
            item.setDragEnabled(True)
            item.setDropEnabled(True)
            item.setData("folder", Qt.ItemDataRole.UserRole)
            item.setData(folder_id, Qt.ItemDataRole.UserRole + 1)
            item.setData(name, Qt.ItemDataRole.UserRole + 2)
            item.setData(name, Qt.ItemDataRole.EditRole)
            
            icon = IconProvider.get_icon("📁", color="#F59E0B", size=32)
            item.setIcon(icon)
            
            if parent_item:
                parent_item.appendRow(item)
            else:
                self.model.appendRow(item)
            self._folder_items[folder_id] = item
        finally:
            self._is_updating = is_updating_prev

    def add_document(self, doc_id: int, title: str, file_type: str, is_active: bool = False, folder_id: int = None, text: str = ""):
        """Add a document to the tree with real icons."""
        is_updating_prev = self._is_updating
        self._is_updating = True
        try:
            item = QStandardItem(title)
            item.setCheckable(True)
            item.setCheckState(Qt.CheckState.Checked if is_active else Qt.CheckState.Unchecked)
            item.setEditable(True)
            item.setData("document", Qt.ItemDataRole.UserRole)
            item.setData(doc_id, Qt.ItemDataRole.UserRole + 1)
            item.setData(title, Qt.ItemDataRole.UserRole + 2)
            item.setData(file_type, Qt.ItemDataRole.UserRole + 3)
            item.setData(title, Qt.ItemDataRole.EditRole)
            item.setDragEnabled(True)
            item.setDropEnabled(False)
            
            icon_char = self._get_doc_icon(file_type)
            icon_color = "#4F46E5"
            if file_type == 'pdf': icon_color = "#EF4444"
            elif file_type in ['docx', 'doc']: icon_color = "#3B82F6"
            elif file_type in ['xls', 'xlsx']: icon_color = "#10B981"
            elif file_type == 'transcription': icon_color = "#10B981"
            
            icon = IconProvider.get_icon(icon_char, color=icon_color, size=32)
            item.setIcon(icon)
            
            if text:
                doc = QTextDocument()
                doc.setHtml(text)
                clean_text = doc.toPlainText()
                char_count = len(clean_text)
                preview = " ".join(clean_text[:200].split())
                if len(clean_text) > 200:
                    preview += "..."
                
                tooltip = f"<b>{title}</b><br/>Tip: {file_type.upper()}<br/>Karakter: {char_count}<br/><br/><i>{preview}</i>"
                item.setToolTip(tooltip)
            else:
                item.setToolTip(f"<b>{title}</b><br/>Tip: {file_type.upper()}")
            
            if is_active:
                 item.setForeground(QColor("#DC2626"))
            
            f_id = int(folder_id) if folder_id is not None else None
            if f_id is not None and f_id in self._folder_items:
                self._folder_items[f_id].appendRow(item)
            else:
                self.model.appendRow(item)
            self._doc_items[doc_id] = item
        finally:
            self._is_updating = is_updating_prev

    def clear_documents(self):
        """Clear all documents from the tree."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels([""])
        self._doc_items.clear()
        self._folder_items.clear()

    def populate_tree(self, documents: list, folders: list = None):
        """Populate tree with persistent mixed order."""
        if folders is None: folders = []
        self._is_updating = True
        try:
            self.clear_documents()
            hierarchy = {}
            for f in folders:
                p_id = int(f.get('parent_id')) if f.get('parent_id') is not None else None
                if p_id not in hierarchy: hierarchy[p_id] = []
                hierarchy[p_id].append(('folder', f))
            for d in documents:
                f_id = int(d.get('folder_id')) if d.get('folder_id') is not None else None
                if f_id not in hierarchy: hierarchy[f_id] = []
                hierarchy[f_id].append(('document', d))
            
            def get_sort_key(item_tuple):
                item_type, data = item_tuple
                order_idx = data.get('order_index', 0)
                name_str = str(data.get('title') if item_type == 'document' else data.get('name', ''))
                nat_key = [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', name_str)]
                type_val = 0 if item_type == 'folder' else 1
                return (order_idx, type_val, nat_key)

            for p_id in hierarchy:
                hierarchy[p_id].sort(key=get_sort_key)
            
            def build_level(p_id, parent_item=None):
                children = hierarchy.get(p_id, [])
                for child_type, data in children:
                    if child_type == 'folder':
                        f_id = int(data['id'])
                        item = QStandardItem(data['name'])
                        item.setEditable(True)
                        item.setDragEnabled(True)
                        item.setDropEnabled(True)
                        item.setData("folder", Qt.ItemDataRole.UserRole)
                        item.setData(f_id, Qt.ItemDataRole.UserRole + 1)
                        item.setData(data['name'], Qt.ItemDataRole.UserRole + 2)
                        item.setData(data['name'], Qt.ItemDataRole.EditRole)
                        item.setIcon(IconProvider.get_icon("📁", color="#F59E0B", size=32))
                        
                        if parent_item: parent_item.appendRow(item)
                        else: self.model.appendRow(item)
                        
                        self._folder_items[f_id] = item
                        build_level(f_id, item)
                    else:
                        self.add_document(
                            data['id'], data['title'], data['file_type'],
                            data.get('is_active', False), p_id,
                            text=data.get('extracted_text', "")
                        )
            build_level(None, None)
        finally:
            self._is_updating = False
        self.tree.expandAll()
