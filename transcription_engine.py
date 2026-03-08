"""
Transcription Engine for LexiScholar
Handles audio/video transcription using OpenAI Whisper with structured error handling.
"""

import os
import logging
import json
from enum import Enum
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
import imageio_ffmpeg

logger = logging.getLogger(__name__)

class TranscriptionError(Enum):
    LIBRARY_MISSING = ("'openai-whisper' kütüphanesi bulunamadı.", "TR_ERR_001")
    MODEL_LOAD_FAILED = ("Model yüklenemedi: {error}", "TR_ERR_002")
    FILE_NOT_FOUND = ("Dosya bulunamadı: {path}", "TR_ERR_003")
    PROCESS_FAILED = ("Transkripsiyon hatası: {error}", "TR_ERR_004")
# Ensure ffmpeg is in PATH FIRST (so it overrides any broken system ffmpegs)
try:
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    
    # The most bulletproof way on Windows: Patch whisper's load_audio directly
    try:
        import whisper.audio
        _original_load_audio = whisper.audio.load_audio
        
        def _patched_load_audio(file: str, sr: int = whisper.audio.SAMPLE_RATE):
            import subprocess
            import numpy as np
            cmd = [
                ffmpeg_path, # USE THE ABSOLUTE PATH HERE
                "-nostdin",
                "-threads", "0",
                "-i", file,
                "-f", "s16le",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                "-ar", str(sr),
                "-"
            ]
            try:
                # Add creationflags=subprocess.CREATE_NO_WINDOW to hide console popup on Windows
                creationflags = 0
                if os.name == 'nt':
                    creationflags = 0x08000000
                out = subprocess.run(cmd, capture_output=True, check=True, creationflags=creationflags).stdout
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

            return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

        # Apply the monkey patch
        whisper.audio.load_audio = _patched_load_audio
        whisper.load_audio = _patched_load_audio
    except (ImportError, AttributeError):
        logger.debug("Whisper not installed or audio module missing, skipping monkey-patch.")

except Exception as e:
    logger.warning(f"FFmpeg path binding failed: {e}")

class TranscriptionEngine(QObject):
    """
    Backend for transcribing audio files with detailed error reporting.
    """
    progress_update = pyqtSignal(str)
    transcription_finished = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, model_size: str = "base"):
        super().__init__()
        self.model_size = model_size
        self.model = None

    def load_model(self) -> bool:
        """Load the whisper model lazily."""
        if self.model is not None:
            return True
            
        self.progress_update.emit(f"Model yükleniyor ({self.model_size})...")
        try:
            import whisper
        except ImportError:
            err = TranscriptionError.LIBRARY_MISSING
            msg = f"[{err.value[1]}] {err.value[0]}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            return False

        try:
            self.model = whisper.load_model(self.model_size)
            self.progress_update.emit("Model yüklendi.")
            return True
        except Exception as e:
            err = TranscriptionError.MODEL_LOAD_FAILED
            msg = f"[{err.value[1]}] {err.value[0].format(error=e)}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            return False

    def transcribe(self, file_path: str):
        """Transcribe audio file."""
        if not os.path.exists(file_path):
            err = TranscriptionError.FILE_NOT_FOUND
            msg = f"[{err.value[1]}] {err.value[0].format(path=file_path)}"
            self.error_occurred.emit(msg)
            return

        if not self.load_model():
            return

        try:
            # Build dynamic wait time estimation message
            est_map = {
                "tiny": "oldukça kısa",
                "base": "kısa bir süre",
                "small": "birkaç dakika",
                "medium": "ortalama 10-20 dakika",
                "large": "donanımınıza göre görece uzun (dosya süresini aşan bir zaman)"
            }
            duration_text = est_map.get(self.model_size, "bir süre")
            
            msg = f"Transkripsiyon başlatılıyor: {os.path.basename(file_path)}...\n\n(Bu işlem dosyanın büyüklüğüne ve bilgisayarınızın hızına bağlı olarak {duration_text} sürebilir.)"
            self.progress_update.emit(msg)
            result = self.model.transcribe(file_path, fp16=False)
            
            output = {
                "text": result["text"],
                "segments": result.get("segments", [])
            }
            
            self.progress_update.emit("Tamamlandı.")
            self.transcription_finished.emit(file_path, json.dumps(output))
        except Exception as e:
            err = TranscriptionError.PROCESS_FAILED
            msg = f"[{err.value[1]}] {err.value[0].format(error=e)}"
            logger.error(msg)
            self.error_occurred.emit(msg)
