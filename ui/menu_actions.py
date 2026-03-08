"""
Menu Actions for LexiScholar Main Window
Modularized menu action handlers and dialog methods.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from . import common_ui
import os
from __version__ import APP_DISPLAY_VERSION

class MenuActions:
    """Mixin class providing menu action methods for MainWindow."""
    
    def _export_code_report(self, format_type: str = 'txt'):
        """Export a code report for the selected code."""
        code_id = self.retrieved_segments._current_code_id
        if not code_id:
            common_ui.show_info(self, "Bilgi", "Lütfen önce bir kod seçin.")
            return
        
        # Get code info
        code = None
        for c in self.code_dao.get_all():
            if c['id'] == code_id:
                code = c
                break
        
        if not code:
            return
        
        # Get segments
        segments = self.segment_dao.get_by_code(code_id)
        
        if not segments:
            common_ui.show_info(self, "Bilgi", "Bu kodda segment bulunmuyor.")
            return
        
        # Generate report
        from export import ReportExporter
        exporter = ReportExporter()
        content = exporter.generate_code_report(code, segments, format_type)
        
        # Get save path
        ext_map = {'word': 'docx', 'xlsx': 'xlsx', 'txt': 'txt', 'html': 'html', 'csv': 'csv', 'md': 'md', 'json': 'json'}
        filter_map = {
            'word': 'Word Belgesi (*.docx)',
            'xlsx': 'Excel Belgesi (*.xlsx)',
            'txt': 'Metin Dosyası (*.txt)',
            'html': 'HTML Belgesi (*.html)',
            'csv': 'CSV Veri Dosyası (Excel için) (*.csv)',
            'md': 'Markdown Notu (Notion/Obsidian için) (*.md)',
            'json': 'JSON Veri Dosyası (*.json)'
        }
        
        ext = ext_map.get(format_type, 'txt')
        save_filter = filter_map.get(format_type, 'Tüm Dosyalar (*.*)')
        
        file_path = common_ui.get_save_file(
            self, "Raporu Kaydet", f"{code['name']}_rapor.{ext}",
            save_filter
        )
        
        if file_path:
            success = exporter.save_report(file_path, content, format_type)
            if success:
                if common_ui.ask_confirmation(
                    self, "Rapor Kaydedildi",
                    f"Rapor kaydedildi:\n{file_path}\n\nDosyayı açmak ister misiniz?"
                ):
                    os.startfile(file_path)
            else:
                common_ui.show_warning(self, "Dışa Aktarma Hatası", "Dosya kaydedilemedi.")

    def _export_memo_report(self, format_type: str = 'word'):
        """Export all project memos to a report."""
        memos = self.memo_dao.get_all()
        if not memos:
            common_ui.show_info(self, "Bilgi", "Projede henüz herhangi bir not (memo) bulunmuyor.")
            return

        # Prepare formatting for save name
        ext = 'docx' if format_type == 'word' else 'txt'
        filter_str = 'Word Belgesi (*.docx)' if format_type == 'word' else 'Metin Dosyası (*.txt)'
        
        file_path = common_ui.get_save_file(
            self, "Memo Raporunu Kaydet", f"Proje_Memolari.{ext}",
            filter_str
        )
        
        if file_path:
            from export import ReportExporter
            exporter = ReportExporter()
            if exporter.save_memo_report(file_path, memos, format_type):
                if common_ui.ask_confirmation(
                    self, "Rapor Kaydedildi",
                    f"Memo raporu kaydedildi:\n{file_path}\n\nDosyayı açmak ister misiniz?"
                ):
                    os.startfile(file_path)
            else:
                common_ui.show_warning(self, "Hata", "Memo raporu kaydedilemedi.")

    def _export_codebook(self):
        """Export Codebook (Kod Kitabı) as HTML."""
        codes = self.code_dao.get_all()
        if not codes:
            common_ui.show_info(self, "Bilgi", "Projede henüz kod bulunmuyor.")
            return

        file_path = common_ui.get_save_file(
            self, "Kod Kitabını Kaydet", "Kod_Kitabi_Codebook.html",
            "HTML Dosyası (*.html)"
        )
        
        if file_path:
            from export import ReportExporter
            exporter = ReportExporter()
            content = exporter.generate_codebook(codes)
            
            if exporter.save_report(file_path, content, 'html'):
                if common_ui.ask_confirmation(
                    self, "Kod Kitabı Oluşturuldu",
                    f"Kod kitabı kaydedildi:\n{file_path}\n\nDosyayı açmak ister misiniz?"
                ):
                    os.startfile(file_path)

    def _show_project_summary_report(self):
        """Generate and show/save Project Summary Dashboard."""
        # Collect stats
        stats = {
            'doc_count': len(self.doc_dao.get_all()),
            'code_count': len(self.code_dao.get_all()),
            'segment_count': len(self.segment_dao.get_all()), # Fixed method name
            'memo_count': len(self.memo_dao.get_all())
        }
        
        from export import ReportExporter
        exporter = ReportExporter()
        content = exporter.generate_project_summary(
            self._active_project_name or "Adsız Proje", 
            stats
        )
        
        # Save temp or ask user? Let's save.
        file_path = common_ui.get_save_file(
            self, "Proje Özetini Kaydet", "Proje_Ozeti_Dashboard.html",
            "HTML Dosyası (*.html)"
        )
         
        if file_path:
            if exporter.save_report(file_path, content, 'html'):
                os.startfile(file_path)

    
    def _show_guide(self):
        """Open the comprehensive Turkish usage guide in the default web browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        import os
        
        guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "kullanim_kilavuzu.html")
        if os.path.exists(guide_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(guide_path))
        else:
            common_ui.show_warning(self, "Kılavuz Bulunamadı", "Kullanım kılavuzu dosyası (docs/kullanim_kilavuzu.html) bulunamadı.")
    
    def _show_about(self):
        """Show about dialog."""
        from .help_window import AboutDialog
        dialog = AboutDialog(self)
        dialog.exec()
    
    def _new_project(self):
        """Create a new project."""
        from .project_dialog import ProjectDialog
        
        dialog = ProjectDialog(self, mode='create')
        
        if dialog.exec():
            project_name = dialog.get_project_name()
            if project_name:
                from project_manager import ProjectManager
                pm = ProjectManager(self.db_path)
                
                success, result = pm.create_project(project_name)
                
                if success:
                    # Result is the new db path
                    self.db_path = result
                    self._reinitialize_daos(self.db_path)
                    
                    project_display_name = project_name
                    self._update_project_label(project_display_name)
                    self._reload_all_data()
                    
                    
                    self.statusbar.showMessage(f"✅ Yeni proje oluşturuldu: {project_name}")
                    common_ui.show_info(self, "Proje Oluşturuldu", f"'{project_name}' oluşturuldu ve aktif edildi.")
                else:
                    common_ui.show_warning(self, "Hata", result)
    
    def _save_project(self):
        """Save the current project directly (overwrite)."""
        if not self._active_project_name:
            # No active project, fall back to Save As
            return self._save_project_as()
        
        from project_manager import ProjectManager
        pm = ProjectManager(self.db_path)
        success, result = pm.save_project(self._active_project_name)
        if success:
            self.statusbar.showMessage(f"✅ Proje kaydedildi: {self._active_project_name}")
            return True
        else:
            common_ui.show_warning(self, "Kaydetme Hatası", result)
            return False
    
    def _save_project_as(self):
        """Save the project with a new name."""
        from .project_dialog import ProjectDialog
        
        dialog = ProjectDialog(self, mode='save')
        if dialog.exec():
            project_name = dialog.get_project_name()
            if project_name:
                from project_manager import ProjectManager
                pm = ProjectManager(self.db_path)
                success, result = pm.save_project(project_name)
                if success:
                    self.statusbar.showMessage(f"✅ Proje kaydedildi: {project_name}")
                    self._update_project_label(project_name)
                    common_ui.show_info(self, "Proje Kaydedildi", f"'{project_name}' kaydedildi.\n\nKonum: {result}")
                    return True
                else:
                    common_ui.show_warning(self, "Kaydetme Hatası", result)
                    return False
        return False # Cancelled or failed
    
    def _load_project(self):
        """Load a project via dialog."""
        from .project_dialog import ProjectDialog
        from project_manager import ProjectManager
        from pathlib import Path
        
        pm = ProjectManager(self.db_path)
        recent_projects = pm.get_recent_projects()
        
        dialog = ProjectDialog(self, mode='load', recent_projects=recent_projects)
        if dialog.exec():
            selected = dialog.get_selected_project()
            if selected:
                self._load_project_path(selected)
    
    def _load_project_path(self, project_path: str):
        """Load a project from a specific path — GenericWorker ile async (UI donmaz)."""
        from project_manager import ProjectManager
        from pathlib import Path
        from .worker_threads import GenericWorker

        # Eski DB yolunu sakla (hata varsa geri dön)
        old_db_path = self.db_path
        pm = ProjectManager(old_db_path)

        # Status bar'da yükleniyor geri bildirimi
        self.statusbar.showMessage("⏳ Proje yükleniyor...")
        self.setEnabled(False)   # UI'yi kilitler — istem dışı etkileşimi önler

        self._load_worker = GenericWorker(pm.load_project, project_path)

        def _on_load_ok(result):
            success, new_db_path = result
            self.setEnabled(True)
            if success:
                try:
                    from database.connection import close_connection
                    close_connection(old_db_path)
                except Exception:
                    pass
                self.config.db_path = new_db_path
                self._reinitialize_daos(new_db_path)
                p = Path(project_path)
                project_display_name = p.stem if p.is_file() else p.name
                self._update_project_label(project_display_name)
                self._reload_all_data()
                self.statusbar.showMessage(f"✅ Proje yüklendi: {project_display_name}")
                # NLP modellerini boşalt — eski proje modelleri temizlensin
                try:
                    from nlp_engine import _cache
                    _cache.unload_all()
                    if hasattr(self, 'nlp_status'):
                        self.nlp_status.refresh()
                except Exception:
                    pass
            else:
                self.statusbar.showMessage("❌ Proje yüklenemedi")
                common_ui.show_warning(self, "Yükleme Hatası", new_db_path)

        def _on_load_err(err_msg):
            self.setEnabled(True)
            self.statusbar.showMessage("❌ Proje yüklenemedi")
            common_ui.show_error(self, "Kritik Hata",
                                 f"Proje yüklenirken beklenmeyen hata:\n{err_msg}")

        self._load_worker.finished_ok.connect(_on_load_ok)
        self._load_worker.finished_err.connect(_on_load_err)
        self._load_worker.start()

    def _reinitialize_daos(self, db_path: str):
        """Reinitialize all DAOs with a new database path."""
        from database import (
            DocumentDAO, CodeDAO, CodedSegmentDAO, MemoDAO, 
            VariableDAO, VariableValueDAO, FolderDAO, 
            ProjectJournalDAO, CodeSummaryDAO
        )
        self.doc_dao = DocumentDAO(db_path)
        self.code_dao = CodeDAO(db_path)
        self.segment_dao = CodedSegmentDAO(db_path)
        self.memo_dao = MemoDAO(db_path)
        self.var_dao = VariableDAO(db_path)
        self.var_value_dao = VariableValueDAO(db_path)
        self.folder_dao = FolderDAO(db_path)
        self.journal_dao = ProjectJournalDAO(db_path)
        self.summary_dao = CodeSummaryDAO(db_path)
        from database import CoderDAO
        self.coder_dao = CoderDAO(db_path)
