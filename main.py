"""
LexiScholar - Lightweight Qualitative Data Analysis Tool
A streamlined MAXQDA clone for PhD academics.

Usage:
    python main.py
"""

import sys
import os
from pathlib import Path
from __version__ import APP_VERSION, APP_NAME

# PyInstaller DLL Loading
# Torch DLL loading is now handled by hooks/hook-torch.py
# This provides proper DLL initialization for PyInstaller builds

try:
    import torch
except ImportError:
    pass

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def get_data_dir():
    """Get the persistent data directory for LexiScholar."""
    if getattr(sys, 'frozen', False):
        # We are running as an EXE
        appdata = os.environ.get('APPDATA')
        if appdata:
            data_dir = Path(appdata) / "LexiScholar"
        else:
            # Fallback to local if APPDATA is somehow missing
            data_dir = Path(sys.executable).parent / "data"
    else:
        # Development mode
        data_dir = Path(__file__).parent
        
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

# CRITICAL: Add SetupWizard Install Location to Path
# This enables the app to find libraries installed in AppData
data_dir = get_data_dir()
runtime_lib = data_dir / "runtime_env" / "Lib" / "site-packages"
runtime_root = data_dir / "runtime_env"

if runtime_lib.exists():
    sys.path.insert(0, str(runtime_lib))
    sys.path.insert(0, str(runtime_root))
    # Also for Windows specifically, add bin/Scripts if needed
    runtime_scripts = data_dir / "runtime_env" / "Scripts"
    if runtime_scripts.exists():
        os.environ["PATH"] += os.pathsep + str(runtime_scripts)


import logging
import traceback

def setup_logging(data_dir):
    """Initialize logging to a file in the data directory."""
    log_file = data_dir / "lexischolar.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("--- LexiScholar Starting ---")
    return log_file

def global_exception_handler(exctype, value, tb):
    """Global handler for uncaught exceptions."""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    logging.critical(f"Uncaught Exception:\n{error_msg}")
    
    # Try to show a message box if QApplication exists
    from PyQt6.QtWidgets import QMessageBox, QApplication
    if QApplication.instance():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Kritik Hata")
        msg.setText("Uygulama beklenmedik bir hata ile karşılaştı.")
        msg.setInformativeText("Detaylar log dosyasına kaydedildi. Lütfen teknik destek ile iletişime geçin.")
        msg.setDetailedText(error_msg)
        msg.exec()
    
    # Still call the original excepthook
    sys.__excepthook__(exctype, value, tb)

def main():
    """Application entry point with Smart Setup check and Error Handling."""
    data_dir = get_data_dir()
    log_path = setup_logging(data_dir)
    sys.excepthook = global_exception_handler
    
    # 0. Initial Dependency Check (Before anything else)
    # We check for a few core libraries. If missing, we assume a fresh install is needed.
    # This block ensures that a user with only Python installed can run the app directly.
    auto_install_enabled = os.environ.get("LEXISCHOLAR_AUTO_INSTALL", "0") == "1"
    try:
        import PyQt6
        import pandas
        import torch
        import openai
        import whisper
        
        # Suppress QFont warnings after PyQt6 is imported
        from PyQt6 import QtCore
        def qt_message_handler(mode, context, message):
            # Filter out QFont warnings
            if "QFont::setPointSize" in message or "Point size" in message:
                return
            # Print other messages to stderr
            import sys
            print(message, file=sys.stderr)
        
        QtCore.qInstallMessageHandler(qt_message_handler)
        
    except ImportError as e:
        print(f"Eksik kütüphane tespit edildi: {e.name}")
        if not auto_install_enabled:
            logging.error(f"Missing dependency: {e.name}. Auto-install is disabled.")
            print("Eksik bağımlılıklar bulundu. Otomatik kurulum güvenlik nedeniyle varsayılan olarak kapalı.")
            print("Kurmak için önce 'python -m pip install -r requirements.txt' çalıştırın")
            print("veya geçici olarak LEXISCHOLAR_AUTO_INSTALL=1 ile yeniden başlatın.")
            sys.exit(1)

        logging.warning(f"Missing dependency: {e.name}. Initiating auto-install from requirements.txt...")
        print("Gerekli kütüphaneler yükleniyor... Bu işlem internet hızınıza bağlı olarak zaman alabilir.")
        print("(Lütfen pencereyi kapatmayın, işlem bitince uygulama otomatik açılacaktır)")
        
        import subprocess
        
        req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        if os.path.exists(req_file):
            try:
                # Install pip first just in case
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
                
                # Install all requirements
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
                
                print("Tüm kütüphaneler başarıyla yüklendi! Uygulama yeniden başlatılıyor...")
                logging.info("Auto-install completed successfully. Restarting process...")
                
                # Restart the application to ensure fresh imports
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except subprocess.CalledProcessError as e:
                logging.error(f"Auto-install failed: {e}")
                print(f"\nKURULUM HATASI: {e}")
                print("Lütfen internet bağlantınızı kontrol edin ve tekrar deneyin.")
                input("Çıkış için Enter'a basın...")
                sys.exit(1)
        else:
            print("HATA: 'requirements.txt' dosyası bulunamadı!")
            logging.critical("requirements.txt missing during auto-install.")
            sys.exit(1)

    # 1. Initialize QApplication (REQUIRED before any UI)
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        
        # Try to initialize QtWebEngineWidgets if available
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except Exception as e:
            logging.warning(f"QtWebEngine import failed: {e}")

        # Fix for 'GPU state invalid' and 'Compositor returned null texture' errors
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-gpu-compositing --disable-software-rasterizer --log-level=3 --disable-logging"
        os.environ["QT_LOGGING_RULES"] = "*webengine*=false;*chromium*=false"
        
        extra_args = ["--disable-gpu", "--disable-gpu-compositing", "--no-sandbox", "--disable-software-rasterizer", "--log-level=3", "--disable-logging"]
        
        # Create application instance
        app = QApplication(sys.argv + extra_args)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setOrganizationName("Academic Research Tools")
        
        # Set font
        font = QFont("Segoe UI", 10)
        app.setFont(font)
        
        # Enforce global ToolTip and Context Menu design entirely from here 
        # to prevent OS Dark Mode overrides on specific elements like Ribbon.
        app.setStyleSheet("""
            QToolTip {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                padding: 4px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', sans-serif;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
                color: #1E293B;
                font-size: 9.5pt;
            }
            QMenu::item:selected {
                background-color: #F1F5F9;
                color: #0F172A;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E2E8F0;
                margin: 4px 8px;
            }
        """)
        
    except Exception as e:
        logging.critical(f"Failed to initialize QApplication: {e}")
        sys.exit(1)

    # 2. Run Smart Setup (UI Wizard)
    # Now that we have 'app', we can safely show dialogs
    try:
        from ui.setup_wizard import check_setup
        if not check_setup():
             sys.exit(0)
    except Exception as e:
        # If setup fails but we have app, show message box
        logging.error(f"Setup Wizard Error: {e}")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Kurulum Hatası", f"Kurulum sihirbazı başlatılamadı:\n{e}")
        # We might continue or exit depending on severity. 

    # 3. Continue to Main Application
    try:
        from database import init_db
        from ui import MainWindow, WelcomeDialog, ProjectDialog
        from project_manager import ProjectManager
    
        # Initialize database
        default_db_path = data_dir / "lexischolar.db"
        try:
            init_db(str(default_db_path))
        except Exception as e:
            logging.error(f"Database Init Error: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Veritabanı Hatası", f"Veritabanı ilklendirilemedi. Uygulama kapatılıyor.\n\nDetay: {e}")
            sys.exit(1)
        
        # Ask for project via Welcome Dialog
        pm = ProjectManager(str(default_db_path))
        recent_projects = pm.get_recent_projects()
        
        final_db_path = None
        initial_project_name = ""
        
        while True:
            welcome = WelcomeDialog(recent_projects)
            if welcome.exec():
                result_code, project_path = welcome.get_result()
                
                if result_code == WelcomeDialog.LOAD_PROJECT:
                    # Load specific project
                    success, result = pm.load_project(project_path)
                    if success:
                        final_db_path = result
                        initial_project_name = Path(project_path).name
                        break
                    else:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.warning(None, "Proje Yüklenemedi", result)
                
                elif result_code == WelcomeDialog.NEW_PROJECT:
                    # Show New Project Dialog
                    nd = ProjectDialog(mode='create')
                    if nd.exec():
                        p_name = nd.get_project_name()
                        success, result = pm.create_project(p_name)
                        if success:
                            final_db_path = result
                            initial_project_name = p_name
                            break
                        else:
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.warning(None, "Proje Oluşturulamadı", result)
                    else:
                        # User cancelled new projectNaming, go back to welcome
                        continue
                            
                elif result_code == WelcomeDialog.BROWSE_PROJECT:
                    # External Browse
                    from PyQt6.QtWidgets import QFileDialog
                    f_path, _ = QFileDialog.getOpenFileName(
                        None, "Proje Seç", "", "LexiScholar Projesi (project.json);;LexiScholar Marker (*.lxs)"
                    )
                    if f_path:
                        success, result = pm.load_project(f_path)
                        if success:
                            final_db_path = result
                            initial_project_name = Path(f_path).stem if f_path.endswith('.lxs') else Path(f_path).parent.name
                            break
                    else:
                        # User cancelled browse, go back to welcome
                        continue
            else:
                # User closed welcome dialog without selecting
                sys.exit(0)

        # Create and show main window with selected project
        app.processEvents()
        window = MainWindow(final_db_path, initial_project_name)
        window.show()
        
        # CRITICAL FIX for Windows: Force OS to bring window to foreground
        # standard Qt activateWindow() is often blocked by Windows "Focus Stealing Prevention"
        if os.name == 'nt':
            try:
                import ctypes
                hwnd = int(window.winId())
                ctypes.windll.user32.AllowSetForegroundWindow(-1) # ASFW_ANY
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception as e:
                print(f"Windows Focus Error: {e}")

        # Standard Qt activation sequence
        app.processEvents()
        window.activateWindow()
        window.raise_()
        window.setFocus()
        
        # Run event loop
        sys.exit(app.exec())

    except Exception as e:
        logging.critical(f"Critical Application Error: {e}")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Kritik Hata", f"Uygulama başlatılırken hata oluştu:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
