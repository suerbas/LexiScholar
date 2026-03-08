"""
Scrollable message boxes for AI responses.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QApplication, QProgressDialog, QMessageBox, QSizePolicy
from PyQt6.QtCore import Qt
from .modern_dialog import ModernBaseDialog

class ScrollableMessageBox(ModernBaseDialog):
    """A message box with a scrollable text area for long messages."""
    def __init__(self, parent=None, title: str = "Bilgi", message: str = ""):
        super().__init__(parent, min_width=600, min_height=400)
        self.title_text = title; self.message_text = message; self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header("ℹ️", self.title_text)
        self.layout.addWidget(header)
        
        self.text_edit = QTextEdit(); self.text_edit.setReadOnly(True); self.text_edit.setMarkdown(self.message_text)
        self.text_edit.setStyleSheet("QTextEdit { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; font-size: 14px; color: #1E293B; }")
        self.layout.addWidget(self.text_edit, 1)
        
        blo = QHBoxLayout(); tbtn = QPushButton("🌍 Çevir (TR/EN)", clicked=self._translate_content)
        tbtn.setCursor(Qt.CursorShape.PointingHandCursor)
        tbtn.setStyleSheet("QPushButton { background: transparent; color: #475569; border: 1px solid #CBD5E1; border-radius: 10px; padding: 10px 20px; font-weight: 700; font-size: 13px; } QPushButton:hover { background: #F1F5F9; }")
        blo.addWidget(tbtn); blo.addStretch(); ok = QPushButton("Tamam", clicked=self.accept)
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.setStyleSheet("QPushButton { background: #4F46E5; color: white; border: none; border-radius: 10px; padding: 10px 32px; font-weight: 800; font-size: 14px; } QPushButton:hover { background: #4338CA; }")
        blo.addWidget(ok); 
        
        blo.addStretch()
        self.add_size_grip(blo)
        self.layout.addLayout(blo)

    def _translate_content(self):
        from llm_engine import OpenRouterEngine
        try: engine = OpenRouterEngine()
        except Exception: return
        progress = QProgressDialog("Metin çevriliyor...", None, 0, 0, self); progress.show(); QApplication.processEvents()
        try:
            res = engine.generate_completion(self.message_text, system_prompt="Translate between TR/EN. Output ONLY translated markdown.", model="google/gemini-2.5-flash")
            self.message_text = res; self.text_edit.setMarkdown(res)
        except Exception: pass
        finally: progress.close()

class ModernMessageBox(ModernBaseDialog):
    """A simple modern info/warning message box."""
    def __init__(self, parent=None, title: str = "Bilgi", message: str = "", icon_str: str = "ℹ️"):
        super().__init__(parent, min_width=380, min_height=200)
        self.title_text = title; self.message_text = message; self.icon_str = icon_str
        self._setup_ui()

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Ribbon Header
        header = self.build_ribbon_header(self.icon_str, self.title_text)
        self.layout.addWidget(header)
        
        # Message Label
        self.msg_lbl = QLabel(self.message_text)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("font-size: 14px; color: #334155; line-height: 1.5; padding: 10px 0;")
        self.layout.addWidget(self.msg_lbl, 1)
        
        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        
        ok_btn = QPushButton("Tamam")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #4F46E5;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 40px;
                font-weight: 800;
                font-size: 14px;
            }
            QPushButton:hover { background: #4338CA; }
        """)
        footer.addWidget(ok_btn)
        
        footer.addStretch()
        self.layout.addLayout(footer)

    @staticmethod
    def show_info(parent, title, message, icon="ℹ️"):
        """Static helper to show info dialog."""
        dlg = ModernMessageBox(parent, title, message, icon)
        return dlg.exec()
