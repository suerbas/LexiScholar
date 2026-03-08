"""
Context menu and event routing for CodeTree.
"""

from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import Qt
from ..styles import CONTEXT_MENU_STYLE
from .base import CodeDialog
from .. import common_ui

class CodeTreeMenuMixin:
    """Handles context menus and UI-triggered events."""

    def _show_context_menu(self, position):
        """Build and show context menu."""
        menu = QMenu(self)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        
        indexes = self.tree.selectedIndexes()
        selected_item = self.model.itemFromIndex(indexes[0]) if indexes else None
        
        new_code_action = menu.addAction("🏷️ Yeni Kod")
        new_subcode_action = menu.addAction("📎 Yeni Alt Kod")
        
        segments_action = None
        quick_code_action = None
        
        if selected_item:
            menu.addSeparator()
            segments_action = menu.addAction("🔎 Kodlanmış Bölümleri Gör...")
            quick_code_action = menu.addAction("📊 Anket Verisini Kategorilere Ayır...")

        if selected_item and selected_item.hasChildren():
            menu.addSeparator()
            activate_subcodes_action = menu.addAction("✅ Alt Kodları Etkinleştir")
            deactivate_subcodes_action = menu.addAction("⬜ Alt Kodların Etkinliğini Kaldır")
            
        menu.addSeparator()
        edit_action = menu.addAction("✏️ Düzenle (Ad, Renk, Tanım)")
        memo_action = menu.addAction("📝 Not Ekle/Düzenle...")
        menu.addSeparator()
        
        ai_menu = menu.addMenu("🤖 Yapay Zeka Kısayolları")
        ai_sum = ai_menu.addAction("📝 Kodlu Bölümleri Özetle")
        ai_sug = ai_menu.addAction("💡 Alt Kod Önerileri Sun")
        ai_crt = ai_menu.addAction("🎯 Aykırı/Uyumsuz Metinleri Bul")
        
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Sil")
        
        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        if not action: return

        if action == new_code_action: self._create_code(None)
        elif action == new_subcode_action: self._create_subcode()
        elif action == segments_action: self._open_coded_segments(selected_item)
        elif action == quick_code_action:
            c_id = selected_item.data(Qt.ItemDataRole.UserRole + 1)
            name = selected_item.data(Qt.ItemDataRole.UserRole + 3)
            color = selected_item.data(Qt.ItemDataRole.UserRole + 2)
            self.quick_code_requested.emit(c_id, name, color)
        elif action == edit_action: self._edit_code()
        elif action == delete_action: self._delete_selected()
        elif action == memo_action:
            self.code_memo_requested.emit(selected_item.data(Qt.ItemDataRole.UserRole + 1), selected_item.data(Qt.ItemDataRole.UserRole + 3))
        # AI Actions simplified...
        elif action in [ai_sum, ai_sug, ai_crt]:
            c_id = selected_item.data(Qt.ItemDataRole.UserRole + 1)
            name = selected_item.data(Qt.ItemDataRole.UserRole + 3)
            atype = "summarize" if action == ai_sum else "suggest_subcodes" if action == ai_sug else "find_outliers"
            self.ai_action_requested.emit(c_id, name, atype)

    def _create_code(self, parent_id):
        dialog = CodeDialog(self, title="Yeni Kod Oluştur")
        if dialog.exec():
            data = dialog.get_data()
            if data['name']: self.code_created.emit(data['name'], data['color'], parent_id, data['description'])
            else: common_ui.show_warning(self, "Geçersiz İsim", "Kod adı boş olamaz.")

    def _create_subcode(self):
        indexes = self.tree.selectedIndexes()
        if indexes:
            item = self.model.itemFromIndex(indexes[0])
            self._create_code(item.data(Qt.ItemDataRole.UserRole + 1))
        else: common_ui.show_info(self, "Kod Seç", "Lütfen önce bir üst kod seçin.")

    def _edit_code(self):
        indexes = self.tree.selectedIndexes()
        if not indexes: return
        item = self.model.itemFromIndex(indexes[0])
        code_id = item.data(Qt.ItemDataRole.UserRole + 1)
        dialog = CodeDialog(self, title="Kodu Düzenle", 
                            name=item.data(Qt.ItemDataRole.UserRole + 3), 
                            color=item.data(Qt.ItemDataRole.UserRole + 2),
                            description=item.data(Qt.ItemDataRole.UserRole + 4))
        if dialog.exec():
            data = dialog.get_data()
            if self.code_dao and self.code_dao.update(code_id, **data):
                item.setData(data['name'], Qt.ItemDataRole.UserRole + 3)
                item.setData(data['color'], Qt.ItemDataRole.UserRole + 2)
                item.setData(data['description'], Qt.ItemDataRole.UserRole + 4)
                self._update_item_display(item)
                self.project_modified.emit()
