"""
Actions Mixin for Document Tree
Handles file imports, deletions, and moves.
"""

from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtCore import Qt
from .. import common_ui
from pathlib import Path

class DocumentTreeActionsMixin:
    """Provides action methods for DocumentTree."""
    
    def _get_checked_items(self):
        """Get all items that have a checkbox checked."""
        checked_docs = [] # (id, title, item)
        checked_folders = [] # (id, title, item)
        
        for doc_id, item in self._doc_items.items():
            try:
                if item.checkState() == Qt.CheckState.Checked:
                    title = item.data(Qt.ItemDataRole.UserRole + 2) or item.text()
                    checked_docs.append((doc_id, title, item))
            except RuntimeError: continue
            
        for folder_id, item in self._folder_items.items():
            try:
                if item.checkState() == Qt.CheckState.Checked:
                    title = item.data(Qt.ItemDataRole.UserRole + 2) or item.text()
                    checked_folders.append((folder_id, title, item))
            except RuntimeError: continue
            
        return checked_docs, checked_folders

    def _get_target_items(self):
        """Identify items targeted for an action."""
        selected_docs = []
        selected_folders = []
        
        indexes = self.tree.selectedIndexes()
        indexes = [ix for ix in indexes if ix.column() == 0]
        
        for ix in indexes:
            item = self.model.itemFromIndex(ix)
            item_type = item.data(Qt.ItemDataRole.UserRole)
            item_id = item.data(Qt.ItemDataRole.UserRole + 1)
            title = item.data(Qt.ItemDataRole.UserRole + 2) or item.text()
            
            if item_type == "document":
                selected_docs.append((item_id, title, item))
            elif item_type == "folder":
                selected_folders.append((item_id, title, item))
                
        if selected_docs or selected_folders:
            return selected_docs, selected_folders

        return self._get_checked_items()

    def _import_document(self):
        """Open file dialog to import documents."""
        file_paths = common_ui.get_open_files(
            self,
            "Belge İçe Aktar",
            "Belgeler (*.pdf *.docx *.doc *.txt *.rtf *.odt *.sav *.xls *.xlsx);;Tüm Dosyalar (*.*)"
        )
        
        target_folder_id = None
        indexes = self.tree.selectedIndexes()
        if indexes:
            item = self.model.itemFromIndex(indexes[0])
            if item.data(Qt.ItemDataRole.UserRole) == "folder":
                target_folder_id = item.data(Qt.ItemDataRole.UserRole + 1)
        
        if file_paths:
            for file_path in file_paths:
                 file_path = str(Path(file_path))
                 file_type = Path(file_path).suffix[1:].lower()
                 if target_folder_id:
                      self.document_imported_with_folder.emit(file_path, file_type, target_folder_id)
                 else:
                      self.document_imported.emit(file_path, file_type)
    
    def _import_folder(self):
        """Import all documents from a folder into a new project folder."""
        if not self.folder_dao:
            common_ui.show_warning(self, "Hata", "Proje veritabanı bağlantısı yok.")
            return

        folder_path = common_ui.get_existing_directory(self, "Klasör Seç")
        if folder_path:
            folder_path = Path(folder_path)
            folder_name = folder_path.name
            
            try:
                folder_id = self.folder_dao.create(folder_name)
                count = 0
                for ext in ['*.pdf', '*.docx', '*.doc', '*.txt', '*.rtf', '*.xls', '*.xlsx']:
                    for file_path in folder_path.glob(ext):
                        file_type = file_path.suffix[1:].lower()
                        self.document_imported_with_folder.emit(str(file_path), file_type, folder_id)
                        count += 1
                
                if count == 0:
                     common_ui.show_info(self, "Bilgi", "Seçilen klasörde desteklenen belge bulunamadı.")
            except Exception as e:
                common_ui.show_error(self, "Hata", f"Klasör oluşturma hatası: {str(e)}")
    
    def _create_folder(self):
        """Create a new folder in the tree."""
        from ..modern_dialogs import ModernInputDialog
        name, ok = ModernInputDialog.get_input(self, "Yeni Klasör", "Klasör adı:")
        if ok:
            name = name.strip()
            if not name:
                common_ui.show_warning(self, "Geçersiz İsim", "Klasör adı boş olamaz.")
                return
                
            if self.folder_dao:
                folder_id = self.folder_dao.create(name)
                self.add_folder(folder_id, name)
            else:
                from PyQt6.QtGui import QStandardItem
                folder_item = QStandardItem(f"📁 {name}")
                folder_item.setData("folder", Qt.ItemDataRole.UserRole)
                self.model.appendRow(folder_item)

    def _move_selected_to_custom(self, target_docs, target_folders, target_folder_id):
        """Move targeted items to a specific folder."""
        if self.doc_dao:
            for doc_id, title, item in target_docs:
                self.doc_dao.move_to_folder(doc_id, target_folder_id)
        
        if self.folder_dao:
            for f_id, title, item in target_folders:
                if f_id != target_folder_id:
                     self.folder_dao.move_to_folder(f_id, target_folder_id)
        self._refresh_data()
        self.project_modified.emit()

    def _delete_selected_custom(self, target_docs, target_folders):
        """Delete specific targeted items with confirmation."""
        total_count = len(target_docs) + len(target_folders)
        if total_count == 0:
            return

        if total_count == 1:
            if target_docs:
                msg = f"'{target_docs[0][1]}' belgesini ve tüm kodlamalarını silmek istediğinizden emin misiniz?"
            else:
                msg = f"'{target_folders[0][1]}' klasörünü silmek istediğinizden emin misiniz?\n\nİçindeki belgeler silinmeyecek, ana dizine taşınacaktır."
        else:
            msg = f"Seçilen {total_count} öğeyi silmek istediğinizden emin misiniz?\n\n"
            if target_folders:
                msg += f"• {len(target_folders)} Klasör (İçindeki belgeler korunur)\n"
            if target_docs:
                msg += f"• {len(target_docs)} Belge\n"
            msg += "\nBu işlem geri alınamaz."
            
        if common_ui.ask_confirmation(self, "Silmeyi Onayla", msg):
            if target_docs and self.doc_dao:
                for doc_id, title, item in target_docs:
                    self.doc_dao.delete(doc_id)
                    self.document_deleted.emit(doc_id)
                    if doc_id in self._doc_items: del self._doc_items[doc_id]
            if target_folders and self.folder_dao:
                for folder_id, title, item in target_folders:
                    self.folder_dao.delete(folder_id)
                    if folder_id in self._folder_items: del self._folder_items[folder_id]
            self._refresh_data()

    def _delete_selected(self):
        """Legacy delete selected items."""
        target_docs, target_folders = self._get_target_items()
        self._delete_selected_custom(target_docs, target_folders)
