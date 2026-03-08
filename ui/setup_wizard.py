"""
Setup Wizard for LexiScholar
Handles initial environment setup, dependency check, and AI model downloading.
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QFrame, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont

from .common.modern_dialog import ModernBaseDialog

class SetupWorker(QThread):
    """Worker thread for background installation and downloads."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool)
    log = pyqtSignal(str)

    def get_runtime_path(self):
        """Get or create the persistent runtime path in AppData."""
        appdata = os.environ.get('APPDATA')
        if appdata:
            path = Path(appdata) / "LexiScholar" / "runtime_env"
        else:
            path = Path.home() / ".lexischolar" / "runtime_env"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _has_nvidia_gpu(self):
        """Check if the system has an NVIDIA GPU using OS commands."""
        try:
            if os.name == 'nt':
                # Windows: wmic path win32_VideoController get name
                output = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"], capture_output=True, text=True, check=True).stdout
                return "NVIDIA" in output.upper()
            else:
                # Linux/Mac: lspci (if available) or assume no GPU for safety in VMs
                # Most standard users won't have proprietary drivers set up perfectly for pip anyway
                return False 
        except:
            return False

    def run(self):
        try:
            # 1. Check Dependencies
            self.status.emit("📚 Kütüphaneler kontrol ediliyor...")
            self.progress.emit(10)
            
            requirements_path = Path(__file__).parent.parent / "requirements.txt"
            if requirements_path.exists():
                self.log.emit("pip install başlatılıyor...")
                runtime_path = self.get_runtime_path()
                
                if getattr(sys, 'frozen', False):
                    # FROZEN MODE FIX: Do NOT use sys.executable because it points to LexiScholar.exe
                    # Running 'LexiScholar.exe -m pip' re-launches the app, causing a fork bomb.
                    # We must rely on system python.
                    python_exe = "python"
                else:
                    python_exe = sys.executable

                # If frozen, we install into the persistent AppData folder
                cmd = [python_exe, "-m", "pip", "install", "--target", str(runtime_path)]
                
                # SMART HARDWARE DETECTION
                # Check for NVIDIA GPU to decide between heavy CUDA version (2.5GB) or light CPU version (200MB)
                has_gpu = self._has_nvidia_gpu()
                
                if has_gpu:
                    self.log.emit("🚀 NVIDIA GPU Tespit Edildi: Yüksek performanslı sürüm yükleniyor (Büyük dosya)...")
                    # Standard pip install torch installs CUDA version by default on Windows
                else:
                    self.log.emit("🍃 NVIDIA GPU Bulunamadı: Hafif sürüm yükleniyor (CPU-Only)...")
                    # Force CPU version to save massive space and bandwidth
                    cmd.extend(["--index-url", "https://download.pytorch.org/whl/cpu"])

                cmd.extend(["-r", str(requirements_path)])
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                for line in process.stdout:
                    self.log.emit(line.strip())
                    if "Installing" in line:
                        self.progress.emit(20)
                
                process.wait()
            
            self.progress.emit(40)
            
            # 2. Check and Download AI Models (Lazy-trigger)
            self.status.emit("🧠 Yapay zeka modelleri hazırlanıyor...")
            self.log.emit("Model indirme testi başlatılıyor (HuggingFace)...")
            
            # We'll import transformers here to make sure it's available after pip install
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification, pipeline
                models_to_check = [
                    ("savasy/bert-base-turkish-sentiment-cased", "Duygu Analizi (TR)"),
                    ("savasy/bert-base-turkish-ner-cased", "Varlık İsmi Tanıma (TR)")
                ]
                step_val = 50 / len(models_to_check)
                current_p = 40
                for model_id, label in models_to_check:
                    self.status.emit(f"🧠 {label} indiriliyor...")
                    self.log.emit(f"Model indiriliyor: {model_id}")
                    AutoTokenizer.from_pretrained(model_id)
                    if "Varlık" in label or "NER" in label:
                        AutoModelForTokenClassification.from_pretrained(model_id)
                    else:
                        AutoModelForSequenceClassification.from_pretrained(model_id)
                    current_p += step_val
                    self.progress.emit(int(current_p))
                
            except Exception as e:
                self.log.emit(f"Model indirme uyarısı: {e}")
                self.log.emit("Not: Modeller ilk kullanımda otomatik olarak indirilecek.")

            self.status.emit("✅ Kurulum tamamlandı!")
            self.progress.emit(100)
            
            # Create flag file in the PERSISTENT directory
            flag_path = self.get_runtime_path().parent / ".setup_done"
            flag_path.touch()
            
            self.finished.emit(True)
            
        except Exception as e:
            self.log.emit(f"KRİTİK HATA: {e}")
            self.finished.emit(False)


class SetupWizard(ModernBaseDialog):
    """Modern setup wizard with progress bar and logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LexiScholar | Akıllı Kurulum")
        self.setFixedSize(500, 450)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setModal(True)
        
        self._setup_ui()
        self._apply_styles()
        
        # Start Worker
        self.worker = SetupWorker()
        
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.log.connect(self._add_log)
        self.worker.finished.connect(self._on_finished)
        
        QTimer.singleShot(1000, self.worker.start)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("🚀 LexiScholar Hazırlanıyor")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        layout.addWidget(header)
        
        desc = QLabel("Uygulamanın optimize çalışması için gerekli kütüphaneler ve yapay zeka modelleri yapılandırılıyor. Lütfen bekleyiniz...")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.5;")
        layout.addWidget(desc)
        
        # Status & Progress
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("⏳ Kontroller başlatılıyor...")
        self.status_label.setStyleSheet("font-weight: 600; color: #4F46E5;")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_frame)
        
        # Log area
        from PyQt6.QtWidgets import QTextEdit
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 9))
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                color: #475569;
            }
        """)
        layout.addWidget(self.log_area)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_cancel = QPushButton("İptal")
        self.btn_cancel.setFixedSize(80, 40)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9; color: #64748B; border: none; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_next = QPushButton("Lütfen Bekleyiniz...")
        self.btn_next.setEnabled(False)
        self.btn_next.setFixedHeight(40)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #CBD5E1;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background-color: #4F46E5;
            }
        """)
        self.btn_next.clicked.connect(self.accept)
        
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_next)
        layout.addLayout(footer_layout)

    def _apply_styles(self):
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")

    def _add_log(self, message):
        self.log_area.append(f"> {message}")
    
    def _on_finished(self, success):
        if success:
            self.btn_next.setText("Uygulamayı Başlat")
            self.btn_next.setEnabled(True)
        else:
            self.status_label.setText("❌ Hata Oluştu!")
            self.status_label.setStyleSheet("color: #EF4444; font-weight: bold;")
            self.btn_next.setText("Yine de Devam Et")
            self.btn_next.setEnabled(True)


def check_setup():
    """Check if setup is needed and run it."""
    # Build persistent runtime path
    appdata = os.environ.get('APPDATA')
    if appdata:
        runtime_path = Path(appdata) / "LexiScholar" / "runtime_env"
    else:
        runtime_path = Path.home() / ".lexischolar" / "runtime_env"
    
    # Add libraries to path immediately to test imports
    site_packages = runtime_path / "Lib" / "site-packages"
    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))
    
    flag_path = runtime_path.parent / ".setup_done"
    
    # 1. Force verification of critical libraries
    missing_libs = False
    try:
        import torch
        import pandas
    except ImportError:
        missing_libs = True
        print("Eksik kütüphaneler tespit edildi, kurulum sihirbazı başlatılıyor...")

    # 2. If flag missing OR libs missing -> Run Wizard
    if missing_libs or not flag_path.exists():
        # Ensure QApplication exists before showing dialog
        from PyQt6.QtWidgets import QApplication
        if not QApplication.instance():
            # This should technically be handled by main.py, but safe guard
            return False 
            
        wizard = SetupWizard()
        result = wizard.exec()
        
        # Verify again after wizard
        if result:
            return True
        return False
        
    return True


