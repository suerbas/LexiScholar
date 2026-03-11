"""
Action Handlers for LexiScholar MainWindow.
Contains project management, general UI actions, and dialog launchers.
"""

import os
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class MainWindowActions:
    """Mixin class for general MainWindow actions and project data management."""
    
    def _reload_all_data(self):
        """Clear all UI components and reload data from DAOs."""
        self.document_browser.clear()
        self.retrieved_segments.clear()
        self._load_initial_data()
        
    def _load_initial_data(self):
        """Load existing documents and codes from database."""
        if not self.db_path or not os.path.exists(self.db_path):
            self.statusbar.showMessage("Veritabanı bulunamadı")
            return
        
        documents = self.doc_dao.get_all()
        folders = self.folder_dao.get_all()
        self.document_tree.populate_tree(documents, folders)
        
        codes = self.code_dao.get_all()
        self.code_tree.populate_codes(codes)
        
        self.statusbar.showMessage(f"Yüklendi: {len(documents)} belge, {len(codes)} kod")

    def _refresh_current_document(self):
        """Helper to refresh the currently viewed document."""
        doc_id = self.document_browser._current_doc_id
        if doc_id:
            segments = self.segment_dao.get_by_document(doc_id)
            doc = self.doc_dao.get_by_id(doc_id)
            memos = self.memo_dao.get_by_document(doc_id)
            if doc:
                self.document_browser.set_document(doc_id, doc['extracted_text'] or "", segments, memos)

    def _manage_coders(self):
        """Show coder management dialog and switch active coder."""
        from .coder_dialogs import CoderManagerDialog
        
        dialog = CoderManagerDialog(self.coder_dao, self.current_coder_id, self)
        if dialog.exec():
            new_id = dialog.selected_coder_id
            if new_id != self.current_coder_id:
                self.current_coder_id = new_id
                
                coder = self.coder_dao.get_by_id(new_id)
                self.statusbar.showMessage(f"Aktif Kodlayıcı Değiştirildi: {coder['name']}")
                
                if self.document_browser._current_doc_id:
                    self._on_document_selected(self.document_browser._current_doc_id)
                
                # Refresh retrieved segments if the code is selected
                if hasattr(self, 'retrieved_segments'):
                    selected_code_id = getattr(self.retrieved_segments, '_current_code_id', None)
                    if selected_code_id:
                        if hasattr(self, '_on_code_selected'):
                            self._on_code_selected(selected_code_id)

    def _confirm_exit(self):
        """Show exit confirmation dialog with save/discard/cancel options."""
        if not self._is_dirty:
            return True # Exit immediately if no changes
            
        from .common_ui import ask_save_before_exit
        result = ask_save_before_exit(self, "Çıkış Onayı", 
                                    "Kaydedilmemiş değişiklikleriniz olabilir.\n\nÇıkmadan önce projeyi kaydetmek ister misiniz?")
        
        if result == "save":
            return self._save_project()
        elif result == "discard":
            return True # Exit without saving
        else:
            return False # Cancel exit

    def _update_project_label(self, name: str = None):
        """Update the project name label in the statusbar."""
        if name:
            self._active_project_name = name
            
        display_name = self._active_project_name if self._active_project_name else "Adsız Proje"
        self.project_name_label.setText(f"📂 {display_name}")
        
        # Set window title
        dirty_star = " *" if self._is_dirty else ""
        self.setWindowTitle(f"LexiScholar - {display_name}{dirty_star}")

    def _show_journal_dialog(self):
        """Show Project Journal in a central tab."""
        from .journal_window import JournalWidget
        
        tab_name = "📔 Proje Günlüğü"
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return

        widget = JournalWidget(self.journal_dao)
        self.add_analysis_tab(widget, tab_name)
        self.statusbar.showMessage("Proje Günlüğü açıldı.")

    def _show_summary_grid(self):
        """Show Summary Grid in a central tab."""
        from .summary_grid import SummaryGridWidget
        
        tab_name = "📋 Özet Izgarası"
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return

        widget = SummaryGridWidget(self.db_path)
        self.add_analysis_tab(widget, tab_name)
        self.statusbar.showMessage("Özet Izgarası hazır.")

    def _show_transcription_dialog(self):
        """Show Audio/Video transcription dialog."""
        from .transcription_dialog import ModernTranscriptionDialog
        # Pass document DAO and current coder ID to facilitate direct import after transcription
        dialog = ModernTranscriptionDialog(self.doc_dao, getattr(self, 'current_coder_id', 1), self)
        if dialog.exec():
            # If transcription was successful and imported, refresh the document tree
            self._reload_all_data()

    def _show_comparison_tool(self):
        """Show Document Comparison Tool in a tab."""
        tab_name = "🔄 Belge Karşılaştırma"
        
        # Check if already open
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == tab_name:
                self.central_tabs.setCurrentIndex(i)
                return
                
        from .comparison_tool import ComparisonToolWidget
        widget = ComparisonToolWidget(self.db_path, self)
        self.add_analysis_tab(widget, tab_name)
        self.statusbar.showMessage("Belge Karşılaştırma açıldı.")

    def _show_manual(self):
        """Open the modern Encyclopedia in the default web browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        import os
        
        # Determine the path to the encyclopedia index
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        encyclopedia_path = os.path.join(base_dir, "docs", "encyclopedia", "index.html")
        
        if os.path.exists(encyclopedia_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(encyclopedia_path))
        else:
            # Fallback to the old manual if new one isn't found
            guide_path = os.path.join(base_dir, "docs", "kullanim_kilavuzu.html")
            if os.path.exists(guide_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(guide_path))
            else:
                show_warning(self, "Kılavuz Bulunamadı", 
                                 "Ansiklopedi veya Kullanım Kılavuzu dosyası bulunamadı.")
        
    def _show_about(self):
        """Open About Dialog."""
        from .help_window import AboutDialog
        dialog = AboutDialog(self)
        dialog.exec()

    def _show_log_file(self):
        """Open the application log file for debugging."""
        from main import get_data_dir
        try:
            log_path = get_data_dir() / "lexischolar.log"
            if log_path.exists():
                os.startfile(log_path)
            else:
                show_info(self, "Bilgi", "Henüz bir log dosyası oluşturulmamış.")
        except Exception as e:
            show_warning(self, "Hata", f"Log dosyası açılamadı: {e}")

    def _show_search_dialog_auto(self):
         self._show_search_dialog()

    def _create_code_interactive(self):
        """Interactive code creation (shortcut compatible)."""
        if hasattr(self, 'code_tree'):
            self.code_tree._create_code(None)

    def _add_memo_interactive(self):
        """Interactive memo creation based on context."""
        # 1. If text selected in browser -> Create Memo for selection
        if self.document_browser.text_edit.hasFocus():
            cursor = self.document_browser.text_edit.textCursor()
            if cursor.hasSelection():
                self._on_memo_requested(
                    cursor.selectionStart(), 
                    cursor.selectionEnd(), 
                    cursor.selectedText()
                )
                return
        
        # 2. If browser has focus but no selection -> Create Document Memo
        if self.document_browser.isVisible() and self.document_browser._current_doc_id:
             # Trigger document memo
             self._on_document_memo_requested(
                 self.document_browser._current_doc_id, 
                 "Belge Notu" # Title usually generic, or we fetch doc title
             )
             return

        # 3. If code tree has focus -> Create Code Memo
        if self.code_tree.tree.hasFocus():
             code = self.code_tree.get_selected_code()
             if code:
                 self._on_code_memo_requested(code['id'], code['name'])
                 return
                 
        self.statusbar.showMessage("💡 Not eklemek için önce bir metin, belge veya kod seçin.")

    def _rename_active_item(self):
        """Rename the currently selected item in the active tree."""
        if self.code_tree.tree.hasFocus():
            # Trigger rename in code tree
            # CodeTree needs a rename method exposed, or we simulate F2
            # Assuming CodeTree has edit triggers enabled, we can edit current item
            self.code_tree.tree.edit(self.code_tree.tree.currentIndex())
            
        elif self.document_tree.tree.hasFocus():
            self.document_tree.tree.edit(self.document_tree.tree.currentIndex())

