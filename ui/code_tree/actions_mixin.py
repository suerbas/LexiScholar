"""
Actions and filtering logic for CodeTree.
"""

from PyQt6.QtCore import Qt
from .. import common_ui

class CodeTreeActionsMixin:
    """Handles interaction logic: search filtering, CRUD triggers, and toggles."""

    def _filter_codes(self, text):
        """Filter codes based on search text."""
        search_text = text.lower()
        self._apply_filter_to_view(self.model.invisibleRootItem(), search_text)
    
    def _apply_filter_to_view(self, parent_item, text):
        """Recursively hide/show rows in view based on search."""
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row)
            name = child.data(Qt.ItemDataRole.UserRole + 3) or ""
            
            child_has_match = self._check_children_match(child, text)
            self_match = text in name.lower()
            
            should_show = self_match or child_has_match
            self.tree.setRowHidden(row, parent_item.index(), not should_show)
            
            if should_show and text:
                self.tree.expand(parent_item.index())
                
            if child.hasChildren():
                self._apply_filter_to_view(child, text)

    def _check_children_match(self, item, text):
        """Helper for recursive filtering."""
        for row in range(item.rowCount()):
            child = item.child(row)
            name = child.data(Qt.ItemDataRole.UserRole + 3) or ""
            if text in name.lower(): return True
            if self._check_children_match(child, text): return True
        return False

    def _delete_selected(self):
        """Delete all selected codes."""
        indexes = self.tree.selectedIndexes()
        if not indexes: return
            
        selected_items = []
        seen_ids = set()
        for index in indexes:
            item = self.model.itemFromIndex(index)
            code_id = item.data(Qt.ItemDataRole.UserRole + 1)
            if code_id and code_id not in seen_ids:
                selected_items.append(item)
                seen_ids.add(code_id)
        
        if not selected_items: return

        count = len(selected_items)
        name = selected_items[0].data(Qt.ItemDataRole.UserRole + 3) or "Kod"
        msg = f"'{name}' kodunu silmek istediğinizden emin misiniz?" if count == 1 else f"{count} adet kodu silmek istediğinizden emin misiniz?"
        msg += "\nBu işlem kodlanmış tüm segmentleri de silecektir."

        if common_ui.ask_confirmation(self, "Silmeyi Onayla", msg):
            ids_to_delete = [item.data(Qt.ItemDataRole.UserRole + 1) for item in selected_items]
            
            if self.code_dao:
                if hasattr(self.code_dao, 'delete_batch'):
                    self.code_dao.delete_batch(ids_to_delete)
                else:
                    for c_id in ids_to_delete: self.code_dao.delete(c_id)
                        
            for c_id in ids_to_delete:
                self.code_deleted.emit(c_id)
                if c_id in self._code_items: del self._code_items[c_id]
            
            self.populate_codes(self.code_dao.get_all() if self.code_dao else [])

    def _set_all_active(self, is_active: bool):
        """Set activation status for all codes."""
        if not self.code_dao: return
            
        if self.code_dao.set_all_active(is_active):
            try: self.model.itemChanged.disconnect(self._on_item_changed)
            except RuntimeError: pass
            
            check_state = Qt.CheckState.Checked if is_active else Qt.CheckState.Unchecked
            for item in self._code_items.values():
                item.setCheckState(check_state)
                self._update_item_display(item)
            
            self.model.itemChanged.connect(self._on_item_changed)
            self.code_activation_changed.emit(-1, is_active)

    def _toggle_subcodes(self, parent_item, is_active):
        """Recursively toggle activation for all subcodes."""
        try: self.model.itemChanged.disconnect(self._on_item_changed)
        except RuntimeError: pass
            
        check_state = Qt.CheckState.Checked if is_active else Qt.CheckState.Unchecked
        
        def recurse(item):
            for row in range(item.rowCount()):
                child = item.child(row)
                child.setCheckState(check_state)
                code_id = child.data(Qt.ItemDataRole.UserRole + 1)
                if code_id and self.code_dao: self.code_dao.set_active(code_id, is_active)
                self._update_item_display(child)
                self.code_activation_changed.emit(code_id, is_active)
                if child.hasChildren(): recurse(child)
        
        recurse(parent_item)
        self.model.itemChanged.connect(self._on_item_changed)
