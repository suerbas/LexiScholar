"""
Frameless Window Mixin for LexiScholar
Provides common drag and resize functionality for frameless windows.
"""

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QWidget
from ui.styles import get_color


class FramelessMixin:
    """
    Mixin class that provides frameless window functionality.
    Can be used with any QWidget subclass.
    """
    
    def __init_frameless__(self, margin: int = 6):
        """Initialize frameless functionality."""
        self._margin = margin
        self._resize_mode = None
        self._old_pos = QPoint()
        
        # Set frameless window flags
        if hasattr(self, 'setWindowFlags'):
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
        
        # Set transparent background
        if hasattr(self, 'setAttribute'):
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def _get_resize_mode(self, pos: QPoint) -> str:
        """Determine which edge or corner the mouse is over."""
        if not hasattr(self, 'width') or not hasattr(self, 'height'):
            return None
            
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = self._margin
        
        mode = ""
        if y < m: 
            mode += "top"
        elif y > h - m: 
            mode += "bottom"
        
        if x < m: 
            mode += "left"
        elif x > w - m: 
            mode += "right"
        
        return mode if mode else None
    
    def _update_cursor(self, pos: QPoint):
        """Update cursor based on mouse position."""
        if not hasattr(self, 'setCursor'):
            return
            
        mode = self._get_resize_mode(pos)
        
        cursor_map = {
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "topleft": Qt.CursorShape.SizeFDiagCursor,
            "topright": Qt.CursorShape.SizeBDiagCursor,
            "bottomleft": Qt.CursorShape.SizeBDiagCursor,
            "bottomright": Qt.CursorShape.SizeFDiagCursor,
        }
        
        cursor = cursor_map.get(mode, Qt.CursorShape.ArrowCursor)
        self.setCursor(cursor)
    
    def _handle_resize(self, global_pos: QPoint):
        """Handle window resizing."""
        if not hasattr(self, 'resize') or not hasattr(self, 'move'):
            return
            
        if self._resize_mode and self._old_pos:
            dx = global_pos.x() - self._old_pos.x()
            dy = global_pos.y() - self._old_pos.y()
            
            old_geo = self.geometry()
            new_geo = old_geo
            
            if "top" in self._resize_mode:
                new_geo.setTop(old_geo.top() + dy)
            if "bottom" in self._resize_mode:
                new_geo.setBottom(old_geo.bottom() + dy)
            if "left" in self._resize_mode:
                new_geo.setLeft(old_geo.left() + dx)
            if "right" in self._resize_mode:
                new_geo.setRight(old_geo.right() + dx)
            
            # Ensure minimum size
            if hasattr(self, 'minimumSize'):
                min_size = self.minimumSize()
                if new_geo.width() < min_size.width():
                    if "left" in self._resize_mode:
                        new_geo.setLeft(old_geo.left())
                    else:
                        new_geo.setRight(old_geo.right())
                if new_geo.height() < min_size.height():
                    if "top" in self._resize_mode:
                        new_geo.setTop(old_geo.top())
                    else:
                        new_geo.setBottom(old_geo.bottom())
            
            self.setGeometry(new_geo)
            self._old_pos = global_pos
    
    def _handle_drag(self, global_pos: QPoint):
        """Handle window dragging."""
        if not hasattr(self, 'move'):
            return
            
        if self._old_pos:
            dx = global_pos.x() - self._old_pos.x()
            dy = global_pos.y() - self._old_pos.y()
            new_pos = self.pos() + QPoint(dx, dy)
            self.move(new_pos)
            self._old_pos = global_pos
    
    # Event handlers
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self._resize_mode = self._get_resize_mode(pos)
            self._old_pos = event.globalPosition().toPoint()
            
            # If not resizing, we might be dragging
            if not self._resize_mode and hasattr(self, 'setCursor'):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        self._resize_mode = None
        self._old_pos = QPoint()
        if hasattr(self, 'setCursor'):
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()
        
        # Update cursor
        self._update_cursor(pos)
        
        # Handle resize or drag
        if self._resize_mode:
            self._handle_resize(global_pos)
        elif hasattr(self, '_old_pos') and self._old_pos:
            self._handle_drag(global_pos)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click events - maximize/restore."""
        if hasattr(self, 'isMaximized') and hasattr(self, 'showMaximized') and hasattr(self, 'showNormal'):
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()


class FramelessWindow(QWidget, FramelessMixin):
    """
    Complete frameless window implementation.
    Inherits from QWidget and includes FramelessMixin.
    """
    
    def __init__(self, parent=None, margin: int = 6):
        super().__init__(parent)
        self.__init_frameless__(margin)
        
        # Set default styling
        self.setStyleSheet(f"""
            FramelessWindow {{
                background-color: {get_color('bg_main')};
                border: 1px solid {get_color('border')};
                border-radius: 8px;
            }}
        """)
