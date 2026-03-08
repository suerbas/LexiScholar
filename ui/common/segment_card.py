"""
Standardized Segment Card component for LexiScholar.
Focused on compactness and MAXQDA-like aesthetics.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QSizeF
from ..styles import COLORS

class ModernSegmentCard(QFrame):
    """
    A compact, professional card for displaying coded segments.
    Features a color-coded vertical stripe and minimal metadata.
    """
    clicked = pyqtSignal(int, int) # doc_id, seg_id
    
    def __init__(self, segment_data: dict, code_name: str = None, code_color: str = "#4F46E5", parent=None):
        super().__init__(parent)
        self.data = segment_data
        self.code_name = code_name
        self.code_color = code_color
        self._is_active = False
        self._setup_ui()

    def _setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left stripe
        self.stripe = QFrame()
        self.stripe.setFixedWidth(4)
        main_layout.addWidget(self.stripe)

        # Content
        content_parent = QWidget()
        self.content_layout = QVBoxLayout(content_parent)
        self.content_layout.setContentsMargins(10, 6, 10, 8)
        self.content_layout.setSpacing(2)

        # Meta Header
        meta_layout = QHBoxLayout(); meta_layout.setSpacing(8)
        
        doc_title = self.data.get('document_title', 'Bilinmeyen')
        folder = self.data.get('folder_name', '')
        display_path = f"{folder} > {doc_title}" if folder else doc_title
        
        doc_lbl = QLabel(f"📄 {display_path}")
        doc_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; border: none;")
        meta_layout.addWidget(doc_lbl)
        
        # Stars/Weight
        weight = self.data.get('weight', 0)
        if weight > 0:
            stars = "⭐" * min(weight, 5)
            weight_lbl = QLabel(stars)
            weight_lbl.setStyleSheet("font-size: 10px; border: none;")
            meta_layout.addWidget(weight_lbl)
            
        meta_layout.addStretch()
        
        if self.code_name:
            code_lbl = QLabel(self.code_name.upper())
            code_lbl.setWordWrap(False)
            code_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            code_lbl.setStyleSheet(f"""
                font-size: 9px; font-weight: 800; color: white; 
                background-color: {self.code_color}; padding: 2px 8px; border-radius: 4px; border: none;
                min-height: 16px;
            """)
            meta_layout.addWidget(code_lbl, 0, Qt.AlignmentFlag.AlignTop)
            
        self.content_layout.addLayout(meta_layout)

        # Text area - Now scrollable with fixed height
        self.text_display = QTextEdit()
        text = self.data.get('segment_text', '')
        self.text_display.setPlainText(text)
        self.text_display.setReadOnly(True)
        self.text_display.setFrameShape(QFrame.Shape.NoFrame)
        # Enable scrollbar but keep it slim if possible via styling
        self.text_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.text_display.setStyleSheet("""
            QTextEdit { 
                background: transparent; color: #1E293B; font-size: 12px; border: none; padding: 0;
            }
            QToolTip {
                background-color: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; font-size: 11px; padding: 4px;
            }
            QScrollBar:vertical {
                border: none; background: #F8FAFC; width: 6px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1; min-height: 20px; border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        
        # Fixed height for visual consistency (approx 2-3 lines of text)
        self.text_display.setFixedHeight(50)
        
        doc = self.text_display.document()
        doc.setDocumentMargin(0)
        self.content_layout.addWidget(self.text_display)
        
        main_layout.addWidget(content_parent)
        self._update_style()

    def _update_style(self):
        bg = "#EFF6FF" if self._is_active else "white"
        border = self.code_color if self._is_active else "#E2E8F0"
        stripe_color = self.code_color
        
        self.setStyleSheet(f"""
            ModernSegmentCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 5px;
                margin: 1px 4px;
            }}
            ModernSegmentCard:hover {{
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }}
            QToolTip {{
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                font-size: 11px;
                padding: 4px;
            }}
        """)
        if hasattr(self, 'stripe'):
            self.stripe.setStyleSheet(f"background-color: {stripe_color}; border-top-left-radius: 4px; border-bottom-left-radius: 4px;")

    def set_active(self, active: bool):
        self._is_active = active
        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data.get('document_id', 0), self.data.get('id', 0))
        super().mousePressEvent(event)

    def adjust_height_to_content(self):
        # We now use it primarily for tooltips since height is mostly fixed
        doc = self.text_display.document()
        width = self.text_display.viewport().width()
        if width < 100: width = 500 
        doc.setTextWidth(float(width))
        doc_height = doc.size().height()
        
        full_text = self.text_display.toPlainText()
        # Threshold for clipping now based on our new fixed height (60)
        if doc_height > 65: 
             tip = f"<b>Segment Tam Metni:</b><br><br>{full_text}"
             self.setToolTip(tip)
             self.text_display.setToolTip(tip)
        else:
             self.setToolTip("") 
             self.text_display.setToolTip("")
             
        self.updateGeometry()
