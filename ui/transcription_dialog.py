import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QComboBox, QProgressBar, QMessageBox, QFrame,
    QGraphicsDropShadowEffect, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QIcon
from transcription_engine import TranscriptionEngine
from .styles import COLORS, get_color
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class TranscriptionWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, engine, file_path):
        super().__init__()
        self.engine = engine
        self.file_path = file_path
        
        # Connect engine signals to worker signals
        self.engine.progress_update.connect(lambda msg: self.progress.emit(msg))

    def run(self):
        try:
            self.engine.transcribe(self.file_path)
            # engine.transcription_finished is connected in the dialog
        except Exception as e:
            self.error.emit(str(e))

class ModernTranscriptionDialog(QDialog):
    def __init__(self, doc_dao, coder_id, parent=None):
        super().__init__(parent)
        self.doc_dao = doc_dao
        self.coder_id = coder_id
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        self.selected_file = None
        
    def _setup_ui(self):
        self.setFixedSize(550, 480)
        
        # Main Container
        container = QFrame(self)
        container.setObjectName("MainContainer")
        container.setFixedSize(530, 460)
        container.move(10, 10)
        container.setStyleSheet(f"""
            #MainContainer {{
                background-color: white;
                border: 2px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 1. Header Row
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("🎙️")
        icon_lbl.setStyleSheet("font-size: 28px;")
        header_layout.addWidget(icon_lbl)
        
        title_lbl = QLabel("Ses / Video Transkripsiyon")
        title_lbl.setStyleSheet(f"color: #1E293B; font-size: 20px; font-weight: 800; border: none;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet("""
            QPushButton {
                border: none; border-radius: 16px; background: #F1F5F9;
                color: #64748B; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; }
        """)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        desc_lbl = QLabel("Whisper AI motoru ile medya dosyalarınızı yerel makinenizde metne dönüştürün.")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #64748B; font-size: 13px; border: none;")
        layout.addWidget(desc_lbl)
        
        # 2. File Selection Zone (Fixed clarity issues)
        self.file_zone = QFrame()
        self.file_zone.setFixedHeight(120)
        self.file_zone.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('bg_main')};
                border: 2px solid {get_color('border')};
                border-radius: 12px;
            }}
        """)
        file_inner_layout = QVBoxLayout(self.file_zone)
        file_inner_layout.setContentsMargins(15, 15, 15, 15)
        file_inner_layout.setSpacing(10)
        
        self.lbl_file = QLabel("Henüz bir dosya seçilmedi")
        self.lbl_file.setWordWrap(True)
        self.lbl_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_file.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 13px; border: none;")
        file_inner_layout.addWidget(self.lbl_file)
        
        self.btn_select = QPushButton("📁  Medya Dosyası Seç")
        self.btn_select.setFixedSize(200, 40)
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.clicked.connect(self.select_file)
        self.btn_select.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']}; 
                color: white; 
                border-radius: 8px; 
                font-weight: 700; 
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {COLORS['primary_dark']}; }}
        """)
        file_inner_layout.addWidget(self.btn_select, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.file_zone)
        
        # 3. Model Option
        opt_layout = QHBoxLayout()
        opt_layout.setSpacing(15)
        
        model_lbl = QLabel("Yapay Zeka Modeli:")
        model_lbl.setStyleSheet("color: #334155; font-weight: 700; font-size: 14px; border: none;")
        opt_layout.addWidget(model_lbl)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems(["tiny (Hızlı/Basit)", "base (Dengeli)", "small (Yüksek Kalite)", "medium (Profesyonel)", "large (Stüdyo Kalitesi - Yavaş)"])
        self.combo_model.setCurrentIndex(1)
        self.combo_model.setFixedHeight(40)
        self.combo_model.setStyleSheet(f"""
            QComboBox {{
                border: 2px solid #E2E8F0; border-radius: 8px; padding: 0 15px;
                background: white; color: #1E293B; font-size: 13px;
            }}
            QComboBox:hover {{ border-color: {COLORS['primary']}; }}
        """)
        opt_layout.addWidget(self.combo_model)
        layout.addLayout(opt_layout)
        
        layout.addStretch()
        
        # 4. Status and Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0) # Indeterminate mode for infinite animation
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background: #F1F5F9; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background: {COLORS['success']}; border-radius: 4px; }}
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet(f"color: {COLORS['primary']}; font-size: 12px; font-weight: 700; border: none;")
        layout.addWidget(self.lbl_status)
        
        # 5. Massive Start Button
        self.btn_start = QPushButton("İŞLEMİ BAŞLAT")
        self.btn_start.setEnabled(False)
        self.btn_start.setFixedHeight(55)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_transcription)
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('success')}; 
                color: white; 
                border-radius: 12px; 
                font-size: 16px; 
                font-weight: 800; 
                border: none;
            }}
            QPushButton:hover {{ background-color: {get_color('success')}; }}
            QPushButton:disabled {{ background-color: {get_color('border')}; color: {get_color('text_muted')}; }}
        """)
        layout.addWidget(self.btn_start)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Medya Dosyası Seç", "", 
            "Medya Dosyaları (*.mp3 *.wav *.m4a *.mp4 *.flac *.ogg *.avi *.mkv);;Tüm Dosyalar (*)"
        )
        if file_path:
            self.selected_file = file_path
            self.lbl_file.setText(os.path.basename(file_path))
            self.btn_start.setEnabled(True)
            self.lbl_file.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 700;")

    def start_transcription(self):
        self.btn_start.setEnabled(False)
        self.btn_select.setEnabled(False)
        self.combo_model.setEnabled(False)
        self.progress_bar.show()
        
        model_display = self.combo_model.currentText()
        model_id = model_display.split()[0] # e.g. "base (Dengeli)" -> "base"
        self.engine = TranscriptionEngine(model_id)
        self.worker = TranscriptionWorker(self.engine, self.selected_file)
        
        # Connect signals
        self.worker.progress.connect(self.lbl_status.setText)
        self.engine.transcription_finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        
        self.worker.start()

    def on_finished(self, file_path, result_json):
        self.progress_bar.hide()
        self.lbl_status.setText("Tamamlandı!")
        
        try:
            data = json.loads(result_json)
            raw_text = data.get("text", "")
            segments = data.get("segments", [])
            
            # Format text with clickable timestamps
            formatted_html = "<html><body>"
            for seg in segments:
                start = seg.get("start", 0)
                text = seg.get("text", "").strip()
                
                # Format time: MM:SS
                m, s = divmod(int(start), 60)
                time_str = f"[{m:02d}:{s:02d}]"
                
                # Wrap timestamp in a link that our browser can catch
                # play://seconds
                formatted_html += f'<p><a href="play://{start}" style="color: #4F46E5; text-decoration: none; font-weight: bold;">{time_str}</a> {text}</p>'
            
            formatted_html += "</body></html>"
            
            # Save to DB
            doc_title = os.path.basename(file_path) + " (Transkript)"
            self.doc_dao.create(
                title=doc_title,
                file_path=file_path,
                file_type="transcription",
                extracted_text=formatted_html
            )
            
            show_info(self, "Başarılı", f"Transkripsiyon tamamlandı. '{doc_title}' belgelere eklendi.")
            self.accept()
        except Exception as e:
            self.on_error(f"Sonuç işlenemedi: {e}")

    def on_error(self, message):
        self.progress_bar.hide()
        self.lbl_status.setText("Hata!")
        self.btn_start.setEnabled(True)
        self.btn_select.setEnabled(True)
        show_error(self, "Hata", f"İşlem başarısız:\n{message}")
