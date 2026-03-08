"""
Icon Provider for LexiScholar
Generates icons dynamically using QPainter and Emojis/Text.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QBrush, QPen
from PyQt6.QtCore import Qt, QRect

class IconProvider:
    """Generates standard icons for the application."""
    
    @staticmethod
    def get_icon(emoji: str, color: str = "#4F46E5", size: int = 64, overlay_emoji: str = None) -> QIcon:
        """
        Generates a QIcon with a colored rounded square background and an emoji centered.
        Optionally draws an overlay emoji in the corner.
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # No background container (Transparent)
        
        # Margin
        margin = 2 # Reduced margin
        rect = QRect(margin, margin, size - 2*margin, size - 2*margin)
        
        # Draw Main Emoji
        # Safety check for size
        if size <= 0: size = 64
        
        # Proportional font size (approx 75% of container height)
        font_size = max(1, int(size * 0.75))
        font = QFont("Segoe UI Emoji", font_size)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        painter.setFont(font)
        painter.setPen(QColor(color)) # Use the requested color
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, emoji)
        
        # Draw Overlay Emoji
        if overlay_emoji:
            overlay_size = int(size * 0.4) # Reasonable size for the drawing rectangle
            overlay_font_size = max(1, int(size * 0.3)) if size > 0 else 14
            overlay_font = QFont("Segoe UI Emoji", overlay_font_size)
            overlay_font.setBold(True)
            painter.setFont(overlay_font)
            
            # Position: Bottom Right? Top Right? Let's go with Top Right
            # Adjust rect
            overlay_rect = QRect(size - overlay_size - margin, margin, overlay_size + 5, overlay_size + 5)
            
            # Draw overlay shadow/outline for better visibility?
            # Or just draw it directly. Let's try white text if background is dark,
            # but usually overlays like "+" are green or specific colors.
            # Let's keep it white for now as per style, maybe make it bold.
            # Actually, standard "+" might be thin. Let's use a heavy plus sign emoji "➕" or text "+"
            
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(overlay_rect, Qt.AlignmentFlag.AlignCenter, overlay_emoji)
            
        painter.end()
        return QIcon(pixmap)
    @staticmethod
    def get_layout_icon(orientation: str = "vertical", color: str = "#475569", size: int = 48) -> QIcon:
        """Draws a box split either vertically or horizontally."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(color), 3)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        
        margin = 4
        rect = QRect(margin, margin, size - 2*margin, size - 2*margin)
        
        # Draw outer box
        painter.drawRect(rect)
        
        # Draw split line
        if orientation == "vertical":
            # Split vertically (Side-by-side)
            painter.drawLine(size // 2, margin, size // 2, size - margin)
        else:
            # Split horizontally (Top-bottom)
            painter.drawLine(margin, size // 2, size - margin, size // 2)
            
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def get_action_icon(action: str, color: str = "#4F46E5", size: int = 64) -> QIcon:
        mapping = {
            "undo": "↩",
            "redo": "↪",
            "search": "🔍",
            "export": "📤",
            "ai": "🤖",
            "guide": "🎓",
            "detach": "↗",
            "dock": "↙",
            "close": "✕",
            "maximize": "◻",
            "minimize": "—",
            "help": "💡",
        }
        symbol = mapping.get(action, action)
        return IconProvider.get_icon(symbol, color=color, size=size)
