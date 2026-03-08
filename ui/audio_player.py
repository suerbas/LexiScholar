"""
Audio Player Bar for LexiScholar
Provides playback controls for transcribed audio files.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QSlider, QFrame
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from .styles import COLORS

class AudioPlayerBar(QFrame):
    """Floating or docked bar to control audio playback."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-top: 1px solid {COLORS['border']};
                border-left: 1px solid {COLORS['border']};
                border-right: 1px solid {COLORS['border']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)
        
        # Play/Pause
        self.btn_play = QPushButton("▶️")
        self.btn_play.setFixedSize(40, 40)
        self.btn_play.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']}; color: white; border: none; border-radius: 20px; font-size: 16px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
        """)
        layout.addWidget(self.btn_play)
        
        # Time Labels
        self.lbl_current = QLabel("00:00")
        self.lbl_current.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600; font-family: 'Consolas';")
        layout.addWidget(self.lbl_current)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border']};
                height: 6px;
                background: {COLORS['bg_hover']};
                margin: 2px 0;
                border_radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['primary']};
                border: none;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
        """)
        layout.addWidget(self.slider)
        
        self.lbl_total = QLabel("00:00")
        self.lbl_total.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: 'Consolas';")
        layout.addWidget(self.lbl_total)
        
        # Close
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['text_muted']}; border: none; font-weight: bold;
            }}
            QPushButton:hover {{ color: {COLORS['error']}; }}
        """)
        layout.addWidget(self.btn_close)
        
    def _connect_signals(self):
        self.btn_play.clicked.connect(self.toggle_playback)
        self.btn_close.clicked.connect(self.hide)
        
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        
        self.slider.sliderMoved.connect(self.set_position)
        
    def load_audio(self, file_path):
        """Load a file for playback."""
        if os.path.exists(file_path):
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.show()
            # We don't auto-play here, wait for user or sync click
            
    def play_at(self, seconds):
        """Jump to specific position and play."""
        self.player.setPosition(int(seconds * 1000))
        self.player.play()
        
    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()
            
    def set_position(self, ms):
        self.player.setPosition(ms)
        
    def _on_position_changed(self, ms):
        if not self.slider.isSliderDown():
            self.slider.setValue(ms)
        self.lbl_current.setText(self._format_time(ms))
        
    def _on_duration_changed(self, ms):
        self.slider.setRange(0, ms)
        self.lbl_total.setText(self._format_time(ms))
        
    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText("⏸️")
        else:
            self.btn_play.setText("▶️")
            
    def _format_time(self, ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"

import os
