"""
Model population logic for CodeTree.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QColor

class CodeTreeModelPopulatorMixin:
    """Methods for populating the QStandardItemModel from data."""

    def add_code(self, code_id: int, name: str, color: str, parent_id: int = None, is_active: bool = False, description: str = ""):
        """Add a single code to the tree model."""
        prefix = "🔴" if is_active else "●"
        item = QStandardItem(f"{prefix} {name}")
        item.setCheckable(True)
        item.setCheckState(Qt.CheckState.Checked if is_active else Qt.CheckState.Unchecked)
        
        item.setForeground(QColor(color))
        item.setData("code", Qt.ItemDataRole.UserRole)
        item.setData(code_id, Qt.ItemDataRole.UserRole + 1)
        item.setData(color, Qt.ItemDataRole.UserRole + 2)
        item.setData(name, Qt.ItemDataRole.UserRole + 3)
        item.setData(description, Qt.ItemDataRole.UserRole + 4)
        
        if parent_id and parent_id in self._code_items:
            self._code_items[parent_id].appendRow(item)
        else:
            self.model.appendRow(item)
        
        self._code_items[code_id] = item
        self.tree.expandAll()

    def populate_codes(self, codes: list):
        """Full rebuild of the tree model."""
        self.loading = True
        self.model.clear()
        self.model.setHorizontalHeaderLabels([""])
        self._code_items = {}
        
        # Build hierarchy (Assuming parent_id refers to a code already in list or processed)
        # Sort codes to process parents before children if possible, 
        # but the add_code logic expects parent to exist.
        processed = set()
        to_process = codes[:]
        
        # Simple iterative approach for hierarchy
        attempts = 0
        while to_process and attempts < 10:
            remaining = []
            for c in to_process:
                p_id = c.get('parent_id')
                if not p_id or p_id in self._code_items:
                    self.add_code(c['id'], c['name'], c['color'], p_id, c.get('is_active', False), c.get('description', ""))
                    processed.add(c['id'])
                else:
                    remaining.append(c)
            to_process = remaining
            attempts += 1
            
        # Add any orphans at root
        for c in to_process:
            self.add_code(c['id'], c['name'], c['color'], None, c.get('is_active', False), c.get('description', ""))
            
        self.loading = False

    def clear_codes(self):
        """Clear the model."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels([""])
        self._code_items.clear()

    def _update_item_display(self, item):
        """Update item text/color based on state."""
        name = item.data(Qt.ItemDataRole.UserRole + 3) or "Kod"
        color = item.data(Qt.ItemDataRole.UserRole + 2) or "#4F46E5"
        is_active = item.checkState() == Qt.CheckState.Checked
        prefix = "🔴" if is_active else "●"
        item.setText(f"{prefix} {name}")
        item.setForeground(QColor(color))

    def get_selected_code(self) -> dict:
        """Return dict of selected code info."""
        indexes = self.tree.selectedIndexes()
        if indexes:
            item = self.model.itemFromIndex(indexes[0])
            return {
                'id': item.data(Qt.ItemDataRole.UserRole + 1),
                'name': item.data(Qt.ItemDataRole.UserRole + 3),
                'color': item.data(Qt.ItemDataRole.UserRole + 2),
                'description': item.data(Qt.ItemDataRole.UserRole + 4)
            }
        return None
