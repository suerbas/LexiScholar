"""
Coding helper dialogs for LexiScholar.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class QuickCodeDialog(QDialog):
    """Quick dialog for selecting a code to apply."""
    def __init__(self, codes: list, parent=None):
        super().__init__(parent)
        self.codes = codes; self.selected_code = None; self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Kod Seç"); self.setMinimumSize(300, 400); self.setModal(True)
        layout = QVBoxLayout(self); layout.setSpacing(12); layout.setContentsMargins(16, 16, 16, 16)
        title = QLabel("🏷️ Uygulanacak Kodu Seçin"); title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1E293B; margin-bottom: 8px;"); layout.addWidget(title)
        
        for c in self.codes:
            btn = QPushButton(f"● {c['name']}"); btn.clicked.connect(lambda ch, code=c: self._select_code(code))
            btn.setStyleSheet(f"QPushButton {{ background: white; color: {c['color']}; border: 2px solid {c['color']}; border-radius: 8px; padding: 12px; font-weight: 600; text-align: left; }} QPushButton:hover {{ background: {c['color']}20; }}")
            layout.addWidget(btn)
        
        layout.addStretch(); cancel = QPushButton("İptal", clicked=self.reject); layout.addWidget(cancel); self.setStyleSheet("QDialog { background: #FFFFFF; }")
    
    def _select_code(self, code: dict): self.selected_code = code; self.accept()
    def get_selected_code(self) -> dict: return self.selected_code

class WeightDialog(QDialog):
    """Dialog for selecting code weight."""
    def __init__(self, code_name: str = "", segment_preview: str = "", parent=None):
        super().__init__(parent)
        self.code_name = code_name; self.segment_preview = segment_preview; self.selected_weight = 3; self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("⭐ Kod Ağırlığı"); self.setFixedSize(380, 280); self.setModal(True)
        layout = QVBoxLayout(self); layout.setSpacing(16); layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel(f"⭐ '{self.code_name}' için Ağırlık Seçin"); title.setStyleSheet("font-size: 15px; font-weight: 600;"); layout.addWidget(title)
        
        if self.segment_preview:
            p = self.segment_preview[:80] + "..." if len(self.segment_preview) > 80 else self.segment_preview
            pl = QLabel(f'"{p}"'); pl.setStyleSheet("color: #64748B; font-size: 11px; font-style: italic;"); pl.setWordWrap(True); layout.addWidget(pl)
        
        wlo = QHBoxLayout(); self.btns = []
        for i in range(1, 6):
            b = QPushButton("⭐" * i); b.setFixedSize(60, 50); b.clicked.connect(lambda ch, w=i: self._select_weight(w))
            b.setStyleSheet(self._style(i == 3)); self.btns.append(b); wlo.addWidget(b)
        layout.addLayout(wlo); self.desc = QLabel("Orta önem"); self.desc.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(self.desc); layout.addStretch()
        
        blo = QHBoxLayout(); slo = QPushButton("Atla (Varsayılan)", clicked=self.accept); alo = QPushButton("✓ Uygula", clicked=self.accept)
        alo.setStyleSheet("background: #4F46E5; color: white; padding: 10px 20px; font-weight: 600; border-radius: 6px;")
        blo.addWidget(slo); blo.addStretch(); blo.addWidget(alo); layout.addLayout(blo); self.setStyleSheet("QDialog { background: #FFFFFF; }")
    
    def _style(self, sel):
        if sel: return "QPushButton { background: #FEF3C7; border: 2px solid #F59E0B; border-radius: 8px; }"
        return "QPushButton { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; }"
    
    def _select_weight(self, w):
        self.selected_weight = w; labels = ["Çok düşük", "Düşük", "Orta", "Yüksek", "Çok yüksek"]
        self.desc.setText(labels[w-1]); [b.setStyleSheet(self._style(i+1 == w)) for i, b in enumerate(self.btns)]
    
    def get_weight(self) -> int: return self.selected_weight
