"""
Common UI components and standardized dialogs for LexiScholar.
Aims to reduce redundancy across the UI layer.
"""

from PyQt6.QtWidgets import QMessageBox, QFileDialog
from .common.message_boxes import ModernMessageBox

def show_info(parent, title, message):
    """Standardized information dialog."""
    return ModernMessageBox.show_info(parent, title, message, "ℹ️")

def show_warning(parent, title, message):
    """Standardized warning dialog."""
    return ModernMessageBox.show_info(parent, title, message, "⚠️")

def show_error(parent, title, message):
    """Standardized error/critical dialog."""
    return ModernMessageBox.show_info(parent, title, message, "❌")

def show_scrollable_info(parent, title, message):
    """Standardized scrollable info dialog for long messages."""
    from .common.message_boxes import ScrollableMessageBox
    dlg = ScrollableMessageBox(parent, title, message)
    return dlg.exec()

def ask_confirmation(parent, title, message, yes_text="Evet", no_text="Hayır", default_yes=False):
    """Standardized yes/no confirmation dialog with Turkish labels."""
    from ui.common.modern_confirmation_dialog import ModernConfirmationDialog
    dialog = ModernConfirmationDialog(parent, title, message, yes_text, no_text, default_yes)
    return dialog.get_result()

def ask_save_before_exit(parent, title="Değişiklikleri Kaydet", message="Kaydedilmemiş değişiklikleriniz var. Çıkmadan önce kaydetmek ister misiniz?"):
    """Standardized three-option dialog for save before exit (Save, Discard, Cancel)."""
    from ui.common.modern_save_exit_dialog import ModernSaveExitDialog
    dialog = ModernSaveExitDialog(parent, title, message)
    return dialog.get_result()

def get_open_file(parent, title="Dosya Seç", filter="Tüm Dosyalar (*.*)"):
    """Standardized file open dialog."""
    path, _ = QFileDialog.getOpenFileName(parent, title, "", filter)
    return path

def get_open_files(parent, title="Dosyaları Seç", filter="Tüm Dosyalar (*.*)"):
    """Standardized multiple files open dialog."""
    paths, _ = QFileDialog.getOpenFileNames(parent, title, "", filter)
    return paths

def get_save_file(parent, title="Farklı Kaydet", filter="Tüm Dosyalar (*.*)", default_name=""):
    """Standardized file save dialog."""
    path, _ = QFileDialog.getSaveFileName(parent, title, default_name, filter)
    return path

def get_existing_directory(parent, title="Klasör Seç"):
    """Standardized directory selection dialog."""
    return QFileDialog.getExistingDirectory(parent, title)
