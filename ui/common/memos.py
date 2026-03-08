"""
Memo Dialog for LexiScholar.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class MemoDialog(QDialog):
    """Dialog for creating and editing memos."""
    def __init__(self, parent=None, existing_content: str = "", segment_text: str = ""):
        super().__init__(parent)
        self.memo_content = ""
        self.segment_text = segment_text
        self.existing_content = existing_content
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Not Ekle" if not self.existing_content else "Notu Düzenle")
        self.setMinimumSize(500, 400); self.setModal(True)
        layout = QVBoxLayout(self); layout.setSpacing(16); layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("📝 Akademik Not"); title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1E293B;"); layout.addWidget(title)
        
        if self.segment_text:
            frame = QFrame(); frame.setStyleSheet("background-color: #F1F5F9; border: 1px solid #E2E8F0; border-left: 4px solid #4F46E5; border-radius: 8px; padding: 12px;")
            slo = QVBoxLayout(frame); slo.setContentsMargins(12, 8, 12, 8)
            lbl = QLabel("İlgili Metin:"); lbl.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 600;"); slo.addWidget(lbl)
            txt = QLabel(f'"{self.segment_text[:200]}..."' if len(self.segment_text) > 200 else f'"{self.segment_text}"'); txt.setWordWrap(True)
            txt.setStyleSheet("color: #1E293B; font-size: 12px; font-style: italic;"); slo.addWidget(txt); layout.addWidget(frame)
        
        layout.addWidget(QLabel("Notunuz:")); self.memo_edit = QTextEdit(); self.memo_edit.setPlainText(self.existing_content)
        self.memo_edit.setStyleSheet("QTextEdit { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 13px; } QTextEdit:focus { border-color: #4F46E5; }")
        self.memo_edit.setFont(QFont("Georgia", 11)); layout.addWidget(self.memo_edit, 1)
        
        blo = QHBoxLayout(); cancel = QPushButton("İptal", clicked=self.reject); cancel.setStyleSheet("background: #F1F5F9; color: #64748B; border-radius: 8px; padding: 12px 24px;")
        save = QPushButton("💾 Kaydet", clicked=self._save_memo); save.setStyleSheet("background: #4F46E5; color: white; border-radius: 8px; padding: 12px 32px; font-weight: 600;")
        blo.addWidget(cancel); blo.addStretch(); blo.addWidget(save); layout.addLayout(blo); self.setStyleSheet("QDialog { background: #FFFFFF; }")

    def _save_memo(self):
        self.memo_content = self.memo_edit.toPlainText().strip()
        if self.memo_content: self.accept()
        else: self.reject()

    def get_memo_content(self) -> str: return self.memo_content
