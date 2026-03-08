"""
Interactive Onboarding Tour for LexiScholar.
Helps researchers understand the Quad-Pane layout and basic workflow.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QPropertyAnimation, QEasingCurve, QSettings
from PyQt6.QtGui import QPainter, QColor, QFont, QRegion, QPainterPath

class OnboardingStep:
    def __init__(self, target_widget, title, text, position="bottom"):
        self.target_widget = target_widget
        self.title = title
        self.text = text
        self.position = position # 'top', 'bottom', 'left', 'right'

class OnboardingTour(QWidget):
    """Semi-transparent overlay with spotlight and instructions."""
    
    def __init__(self, parent=None, steps=None):
        super().__init__(parent)
        self.steps = steps or []
        self.current_step_idx = -1
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # UI Components
        self.info_box = QFrame(self)
        self.info_box.setObjectName("InfoBox")
        self.info_box.setFixedWidth(320)
        self.info_box.setStyleSheet("""
            #InfoBox {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #4F46E5;
            }
            QLabel#Title { font-size: 16px; font-weight: 800; color: #1E293B; }
            QLabel#Text { font-size: 13px; color: #475569; line-height: 1.5; }
            QPushButton { 
                background-color: #4F46E5; color: white; border: none; 
                border-radius: 6px; padding: 8px 16px; font-weight: 600; 
            }
            QPushButton:hover { background-color: #4338CA; }
            QPushButton#Skip { background-color: transparent; color: #64748B; }
        """)
        
        box_layout = QVBoxLayout(self.info_box)
        box_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("Title")
        self.lbl_title.setWordWrap(True)
        box_layout.addWidget(self.lbl_title)
        
        self.lbl_text = QLabel()
        self.lbl_text.setObjectName("Text")
        self.lbl_text.setWordWrap(True)
        box_layout.addWidget(self.lbl_text)
        
        box_layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        self.btn_skip = QPushButton("Atla")
        self.btn_skip.setObjectName("Skip")
        self.btn_skip.clicked.connect(self.finish_tour)
        
        self.btn_next = QPushButton("İleri →")
        self.btn_next.clicked.connect(self.next_step)
        
        btn_layout.addWidget(self.btn_skip)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_next)
        box_layout.addLayout(btn_layout)
        
        self.hide()

    def show_step(self, index):
        if index < 0 or index >= len(self.steps):
            self.finish_tour()
            return
            
        self.current_step_idx = index
        step = self.steps[index]
        
        self.lbl_title.setText(step.title)
        self.lbl_text.setText(step.text)
        self.btn_next.setText("Tamamla" if index == len(self.steps)-1 else "İleri →")
        
        # Force layout update to get correct sizeHint
        self.info_box.adjustSize()
        
        # Position info box relative to target
        self._position_info_box(step)
        self.show()
        self.update()

    def _position_info_box(self, step):
        target = step.target_widget
        box_w = self.info_box.width()
        box_h = self.info_box.height()
        
        if not target:
            # Center in window
            self.info_box.move(
                self.width() // 2 - box_w // 2,
                self.height() // 2 - box_h // 2
            )
            return
        
        # Map target geometry to window
        top_left = self.mapFromGlobal(target.mapToGlobal(QPoint(0, 0)))
        target_rect = QRect(top_left, target.size())
        
        if step.position == "bottom":
            x = target_rect.center().x() - box_w // 2
            y = target_rect.bottom() + 15
        elif step.position == "top":
            x = target_rect.center().x() - box_w // 2
            y = target_rect.top() - box_h - 15
        elif step.position == "left":
            x = target_rect.left() - box_w - 15
            y = target_rect.center().y() - box_h // 2
        else: # right
            x = target_rect.right() + 15
            y = target_rect.center().y() - box_h // 2
            
        # Keep inside window (not screen)
        x = max(20, min(x, self.width() - box_w - 20))
        y = max(20, min(y, self.height() - box_h - 20))
        
        self.info_box.move(x, y)

    def next_step(self):
        self.show_step(self.current_step_idx + 1)

    def finish_tour(self):
        self.hide()
        # Save preference
        settings = QSettings("LexiScholar", "Config")
        settings.setValue("onboarding_done", True)
        self.deleteLater()

    def paintEvent(self, event):
        if self.current_step_idx < 0: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define the dimmed overlay color
        overlay_color = QColor(0, 0, 0, 160)
        
        step = self.steps[self.current_step_idx]
        target = step.target_widget
        
        if target:
            # Plan: Draw overlay everywhere EXCEPT the target hole
            # This is much more robust than drawing and then clearing on Windows
            full_path = QPainterPath()
            full_path.addRect(QRectF(self.rect()))
            
            # Map target geometry to this overlay coordinate system
            top_left = self.mapFromGlobal(target.mapToGlobal(QPoint(0, 0)))
            target_rect = QRect(top_left, target.size()).adjusted(-8, -8, 8, 8)
            
            hole_path = QPainterPath()
            hole_path.addRoundedRect(QRectF(target_rect), 12, 12)
            
            # Subtract hole from overlay
            draw_path = full_path.subtracted(hole_path)
            
            painter.fillPath(draw_path, overlay_color)
            
            # Draw the accent border around the hole
            painter.setPen(Qt.PenStyle.SolidLine)
            painter.setPen(QColor(79, 70, 229, 200)) # Indigo with slight alpha
            painter.drawRoundedRect(target_rect, 12, 12)
        else:
            # If no target (like welcome step), just dim everything
            painter.fillRect(self.rect(), overlay_color)

    def start(self):
        self.setGeometry(self.parent().rect())
        self.move(self.parent().mapToGlobal(QPoint(0, 0)))
        self.show_step(0)

def start_onboarding_if_needed(window):
    settings = QSettings("LexiScholar", "Config")
    if not settings.value("onboarding_done", False, type=bool):
        return trigger_onboarding(window)
    return False

def trigger_onboarding(window):
    """Force start the tutorial steps."""
    steps = [
        OnboardingStep(None, "🎓 Hoş Geldiniz!", "LexiScholar'a hoş geldiniz. Araştırma yolculuğunuzu kolaylaştıracak kısa bir tura çıkalım mı?"),
        OnboardingStep(window.document_tree.tree, "📂 1. Belgeler", "Veri setinizi buraya yüklersiniz. Klasörler oluşturarak belgelerinizi düzenleyebilirsiniz.", "right"),
        OnboardingStep(window.code_tree.tree, "🏷️ 2. Kod Tepsisi", "Teorik veya veri odaklı kodlarınızı burada oluşturun. Akademik tanım eklemeyi unutmayın!", "right"),
        OnboardingStep(window.document_browser.text_edit, "📄 3. Çalışma Alanı", "Metinleri buradan okur, seçtiğiniz kısımları kodlara sürükleyerek analiz edersiniz.", "left"),
        OnboardingStep(window.document_browser.text_edit, "💡 Nasıl Kodlarım?", "Çalışma alanında bir metin seçin ve Kod Tepsisi'ndeki bir kodun üzerine sürükleyip bırakın. İşte bu kadar!", "bottom"),
        OnboardingStep(window.retrieved_segments, "📑 4. Analiz Çıktıları", "Seçili kodlarda neler dendiğini toplu halde burada karşılaştırabilirsiniz.", "top"),
        OnboardingStep(window.ribbon.widget(3), "🛠️ 5. Analiz Araçları", "Gelişmiş sorgular, matrisler ve istatistikler gibi güçlü analiz araçlarına bu sekmeden ulaşabilirsiniz.", "bottom"),
        OnboardingStep(window.persistent_controls_widget, "🎯 Kontrol Merkezi", "Geri al/yinele ve ekran düzeni gibi global ayarlara artık Ribbon'ın sağ üst köşesinden ulaşabilirsiniz.", "left")
    ]
    tour = OnboardingTour(window, steps)
    tour.start()
    return True
