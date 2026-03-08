"""
Menu Builder Mixin for Document Tree
Handles context menus and UI events (selection, activation, rename).
"""

from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from .. import common_ui
from ..styles import CONTEXT_MENU_STYLE
from ..icons import IconProvider

class DocumentTreeMenuMixin:
    """Provides context menu and event handling for DocumentTree."""

    def _show_context_menu(self, position):
        """Show context menu for document operations."""
        index = self.tree.indexAt(position)
        clicked_item = self.model.itemFromIndex(index) if index.isValid() else None
        
        if index.isValid() and not self.tree.selectionModel().isSelected(index):
            self.tree.setCurrentIndex(index)
            self.tree.selectionModel().select(index, self.tree.selectionModel().SelectionFlag.ClearAndSelect)

        menu = QMenu(self)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        
        item_type = clicked_item.data(Qt.ItemDataRole.UserRole) if clicked_item else None
        
        if item_type == "folder":
             target_docs = []
             target_folders = [(clicked_item.data(Qt.ItemDataRole.UserRole + 1), clicked_item.data(Qt.ItemDataRole.UserRole + 2), clicked_item)]
        elif item_type == "document":
             target_docs, target_folders = self._get_target_items()
        else:
             target_docs = []
             target_folders = []

        total_targets = len(target_docs) + len(target_folders)
        
        import_action = menu.addAction("📄 Belge İçe Aktar...")
        import_folder_action = menu.addAction("📁 Klasör İçe Aktar...")
        survey_import_action = menu.addAction("📊 Anket İçe Aktar (Excel)...")
        menu.addSeparator()
        new_folder_action = menu.addAction("➕ Yeni Klasör")
        
        if total_targets > 0:
            menu.addSeparator()
            move_menu = menu.addMenu("🚚 Şuraya Taşı...")
            move_to_root = move_menu.addAction("(Ana Dizin)")
            move_to_root.setData(None)
            
            all_folders = self.folder_dao.get_all() if self.folder_dao else []
            for folder in all_folders:
                is_invalid_target = False
                for f_id, f_title, f_item in target_folders:
                    if folder['id'] == f_id:
                        is_invalid_target = True
                        break
                if not is_invalid_target:
                    f_action = move_menu.addAction(f"📁 {folder['name']}")
                    f_action.setData(folder['id'])
            
            menu.addSeparator()
            if item_type == "folder" and total_targets == 1:
                rename_action = menu.addAction("✏️ Klasörü Yeniden Adlandır")
                menu.addSeparator()
                is_fully_selected = self._is_folder_fully_selected(clicked_item)
                if is_fully_selected:
                    toggle_folder_action = menu.addAction("⬜ Klasördeki Belgelerin Seçimini Kaldır")
                    toggle_folder_action.setData(False)
                else:
                    toggle_folder_action = menu.addAction("✅ Klasördeki Tüm Belgeleri Seç")
                    toggle_folder_action.setData(True)
            
            if item_type == "document":
                if total_targets == 1:
                     rename_doc_action = menu.addAction("✏️ Belgeyi Yeniden Adlandır\tF2")
                     self.variables_action = menu.addAction("📊 Değişkenleri Düzenle...")
                     self.memo_action = menu.addAction("📝 Not Ekle/Düzenle...\tAlt+M")
                     self.chat_action = menu.addAction("💬 AI Sohbet Et...\tAlt+C")
                     self.code_cloud_action = menu.addAction("☁️ Belgedeki Kodları Göster (Kod Bulutu)")
                     self.export_action = menu.addAction("📄 Belgeyi Dışa Aktar (TXT/DOCX)")
            
            menu.addSeparator()
            if item_type == "folder" and total_targets == 1:
                 delete_text = "🗑️ Klasörü Sil\tDel"
            elif total_targets > 1:
                 delete_text = f"🗑️ Sil ({total_targets} Öğe)\tDel"
            else:
                 delete_text = "🗑️ Sil\tDel"
            delete_action = menu.addAction(delete_text)

        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        
        if action == import_action:
            self._import_document()
        elif action == import_folder_action:
            self._import_folder()
        elif action == survey_import_action:
            self.survey_import_requested.emit()
        elif action == new_folder_action:
            self._create_folder()
        elif total_targets > 0:
            if action == delete_action:
                self._delete_selected_custom(target_docs, target_folders)
            elif 'move_menu' in locals() and action in move_menu.actions():
                target_folder_id = action.data()
                self._move_selected_to_custom(target_docs, target_folders, target_folder_id)
            elif item_type == "folder" and total_targets == 1:
                if action == rename_action:
                    self.tree.edit(index)
                elif action == toggle_folder_action:
                    self._toggle_folder_selection(clicked_item, action.data())
            elif item_type == "document" and total_targets == 1:
                if action == rename_doc_action:
                    self.tree.edit(index)
                elif action == getattr(self, 'variables_action', None):
                    self._edit_variables_item(clicked_item)
                elif action == getattr(self, 'memo_action', None):
                    doc_id = clicked_item.data(Qt.ItemDataRole.UserRole + 1)
                    title = clicked_item.data(Qt.ItemDataRole.UserRole + 2) or clicked_item.text()
                    if doc_id:
                        self.document_memo_requested.emit(doc_id, title)
                elif action == getattr(self, 'chat_action', None):
                    doc_id = clicked_item.data(Qt.ItemDataRole.UserRole + 1)
                    title = clicked_item.data(Qt.ItemDataRole.UserRole + 2) or clicked_item.text()
                    if doc_id:
                        self.chat_requested.emit(doc_id, title)
                elif action == getattr(self, 'code_cloud_action', None):
                    doc_id = clicked_item.data(Qt.ItemDataRole.UserRole + 1)
                    title = clicked_item.data(Qt.ItemDataRole.UserRole + 2) or clicked_item.text()
                    if doc_id:
                        self.code_cloud_requested.emit(doc_id, title)
                elif action == getattr(self, 'export_action', None):
                    doc_id = clicked_item.data(Qt.ItemDataRole.UserRole + 1)
                    title = clicked_item.data(Qt.ItemDataRole.UserRole + 2) or clicked_item.text()
                    if doc_id:
                        self.export_requested.emit(doc_id, title)

    def _on_selection_changed(self, selected, deselected):
        """Handle document selection."""
        indexes = selected.indexes()
        if indexes:
            item = self.model.itemFromIndex(indexes[0])
            item_type = item.data(Qt.ItemDataRole.UserRole)
            if item_type == "document":
                doc_id = item.data(Qt.ItemDataRole.UserRole + 1)
                if doc_id is not None:
                    self.document_selected.emit(doc_id)

    def _on_item_changed(self, item):
        """Handle item change (checkbox toggle OR rename)."""
        if self._is_updating or not item.model(): return
        item_type = item.data(Qt.ItemDataRole.UserRole)
        item_id = item.data(Qt.ItemDataRole.UserRole + 1)
        prev_name = item.data(Qt.ItemDataRole.UserRole + 2)
        current_text = item.text()

        if prev_name and current_text != prev_name and not current_text.startswith(("📁", "📄", "📕", "📘", "📝", "📊")):
            new_name = current_text.strip()
            if not new_name:
                common_ui.show_warning(self, "Geçersiz İsim", "İsim boş olamaz.")
                self._update_item_display(item, item_type, prev_name)
                return
            if item_type == "document" and self.doc_dao:
                self.doc_dao.rename(item_id, new_name)
            elif item_type == "folder" and self.folder_dao:
                self.folder_dao.update(item_id, new_name)
            self._update_item_display(item, item_type, new_name)
            self.project_modified.emit()
            return

        if item_type == "document":
            doc_id = item.data(Qt.ItemDataRole.UserRole + 1)
            if doc_id:
                is_active = item.checkState() == Qt.CheckState.Checked
                if self.doc_dao:
                    self.doc_dao.set_active(doc_id, is_active)
                item.setForeground(QColor("#DC2626") if is_active else QColor("black"))
                self.document_activation_changed.emit(doc_id, is_active)
        elif item_type == "folder":
            is_active = item.checkState() == Qt.CheckState.Checked
            self._toggle_folder_selection(item, is_active)
            self.document_activation_changed.emit(-1, is_active)

    def _update_item_display(self, item, item_type, name):
        """Update display text and real icon while preserving EditRole."""
        self._is_updating = True
        try:
            item.setText(name)
            item.setData(name, Qt.ItemDataRole.EditRole)
            item.setData(name, Qt.ItemDataRole.UserRole + 2)
            if item_type == "folder":
                icon = IconProvider.get_icon("📁", color="#F59E0B", size=32)
            else:
                file_type = item.data(Qt.ItemDataRole.UserRole + 3) or "txt"
                icon_char = self._get_doc_icon(file_type)
                icon_color = "#4F46E5"
                if file_type == 'pdf': icon_color = "#EF4444"
                elif file_type in ['docx', 'doc']: icon_color = "#3B82F6"
                elif file_type in ['xls', 'xlsx']: icon_color = "#10B981"
                elif file_type == 'sav': icon_color = "#8B5CF6"
                icon = IconProvider.get_icon(icon_char, color=icon_color, size=32)
            item.setIcon(icon)
        finally:
            self._is_updating = False

    def _set_all_active(self, is_active: bool):
        """Set activation status for all documents."""
        if not self.doc_dao or not self.doc_dao.set_all_active(is_active):
            return
        self._is_updating = True
        try:
            check_state = Qt.CheckState.Checked if is_active else Qt.CheckState.Unchecked
            color = QColor("#DC2626") if is_active else QColor("black")
            for doc_id, item in self._doc_items.items():
                try:
                    item.setCheckState(check_state)
                    item.setForeground(color)
                except RuntimeError: pass
            self.document_activation_changed.emit(-1, is_active)
        finally:
            self._is_updating = False

    def _toggle_folder_selection(self, folder_item, is_active):
        """Recursively toggle selection for all documents in a folder."""
        try:
            check_state = Qt.CheckState.Checked if is_active else Qt.CheckState.Unchecked
            color = QColor("#DC2626") if is_active else QColor("black")
            for row in range(folder_item.rowCount()):
                child = folder_item.child(row)
                if not child: continue
                item_type = child.data(Qt.ItemDataRole.UserRole)
                if item_type == "document":
                    if child.checkState() != check_state:
                        child.setCheckState(check_state)
                        child.setForeground(color)
                elif item_type == "folder":
                    self._toggle_folder_selection(child, is_active)
        except RuntimeError: pass

    def _is_folder_fully_selected(self, folder_item):
        """Check if all documents in the folder are selected (checked)."""
        try:
            if folder_item.rowCount() == 0: return False
            for row in range(folder_item.rowCount()):
                child = folder_item.child(row)
                if not child: continue
                item_type = child.data(Qt.ItemDataRole.UserRole)
                if item_type == "document":
                    if child.checkState() != Qt.CheckState.Checked: return False
                elif item_type == "folder":
                    if not self._is_folder_fully_selected(child): return False
            return True
        except RuntimeError: return False

    def _edit_variables_item(self, item):
        """Handle variable editing for a specific item."""
        doc_id = item.data(Qt.ItemDataRole.UserRole + 1)
        title = item.data(Qt.ItemDataRole.UserRole + 2) or item.text()
        if doc_id:
            self.document_variables_requested.emit(doc_id, title)
