"""
Browser Widget Components for LexiScholar Document Browser.
Helper widgets: CodingStripesWidget, LineNumberArea, CodableTextEdit.
"""

from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QFrame, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize, QPoint
from PyQt6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QPainter, QPen, QFont,
    QDragEnterEvent, QDropEvent, QTextFormat
)

from .styles import CODING_STRIPES_STYLE


class CodingStripesWidget(QFrame):
    """Widget that displays coding stripes in the margin."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(48)
        self.segments = []  # List of (start_y, end_y, color, name)
        self.line_height = 20
        self.setStyleSheet(CODING_STRIPES_STYLE)
        self.setMouseTracking(True) # Enable mouse tracking for tooltips
    
    def set_segments(self, segments: list, text_edit: QTextEdit):
        """
        Update coding stripes based on coded segments.
        
        Args:
            segments: List of dicts with start_pos, end_pos, code_color, code_name
            text_edit: The text edit to calculate positions from
        """
        self.segments = []
        viewport = text_edit.viewport()
        
        # Guard against invisible/not-yet-shown widgets
        if not viewport.isVisible():
            return

        for seg in segments:
            # Start Position
            cursor_start = text_edit.textCursor()
            cursor_start.setPosition(seg['start_pos'])
            rect_start = text_edit.cursorRect(cursor_start)
            
            # Map start to global then local
            start_global = viewport.mapToGlobal(rect_start.topLeft())
            start_local = self.mapFromGlobal(start_global)
            
            # End Position
            cursor_end = text_edit.textCursor()
            cursor_end.setPosition(min(seg['end_pos'], len(text_edit.toPlainText())))
            rect_end = text_edit.cursorRect(cursor_end)
            
            # Map end to global then local
            end_global = viewport.mapToGlobal(rect_end.bottomLeft())
            end_local = self.mapFromGlobal(end_global)
            
            self.segments.append({
                'start_y': start_local.y(),
                'end_y': end_local.y(),
                'color': seg.get('code_color', '#4F46E5'),
                'name': seg.get('code_name', 'Kod'),
                'weight': seg.get('weight', 0)
            })
        
        self.update()
    
    def mouseMoveEvent(self, event):
        """Show value-added tooltip with code name and weight."""
        y = event.pos().y()
        x = event.pos().x()
        
        # Find segment under mouse
        hovered_segment = None
        bracket_width = 8
        
        # Search relative to painting order or just find the best match
        # Reverse order to find "top-most" if overlapping?
        for i, seg in enumerate(self.segments):
            start_y = seg['start_y']
            end_y = seg['end_y']
            
            col = i % 4
            bracket_x = 8 + (col * 8)
            
            is_vert = (start_y <= y <= end_y) and (abs(x - bracket_x) <= 4)
            is_top = (abs(y - start_y) <= 4) and (bracket_x <= x <= bracket_x + bracket_width)
            is_bottom = (abs(y - end_y) <= 4) and (bracket_x <= x <= bracket_x + bracket_width)
            
            if is_vert or is_top or is_bottom:
                hovered_segment = seg
                break 
        
        from PyQt6.QtWidgets import QToolTip
        if hovered_segment:
            # Create rich tooltip similar to user request
            name = hovered_segment['name']
            weight = hovered_segment['weight']
            color = hovered_segment['color']
            
            # HTML Tooltip
            tooltip_html = f"""
            <div style='font-family: Segoe UI, sans-serif; padding: 4px;'>
                <div style='font-weight: bold; font-size: 12px; margin-bottom: 4px; color: #1E293B;'>
                    <span style='color: {color};'>●</span> {name}
                </div>
                <div style='color: #475569; font-size: 11px;'>
                    Ağırlık: {weight} ⭐
                </div>
            </div>
            """
            
            QToolTip.showText(event.globalPosition().toPoint(), tooltip_html, self)
        else:
            QToolTip.hideText()
            
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        """Paint the coding stripes as brackets."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bracket_width = 8 # Width of the horizontal part of the bracket
        
        for i, seg in enumerate(self.segments):
            start_y = seg['start_y']
            end_y = seg['end_y']
            color = seg['color']
            
            # Reset pen for each segment
            painter.setPen(QPen(QColor(color), 2, Qt.PenStyle.SolidLine))
            
            col = i % 4
            x = 8 + (col * 8) 
            
            # Draw Bracket [
            # Top arm
            painter.drawLine(x, start_y, x + bracket_width, start_y)
            # Vertical line
            painter.drawLine(x, start_y, x, end_y)
            # Bottom arm
            painter.drawLine(x, end_y, x + bracket_width, end_y)



class LineNumberArea(QWidget):
    """Widget to display line numbers/paragraphs."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)
        
    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodableTextEdit(QTextBrowser):
    """QTextEdit with drop support and line numbers."""
    
    code_dropped = pyqtSignal(dict)  # Emits code info when dropped on selection
    mouse_moved = pyqtSignal(int, QPoint) # Pos in doc, Global pos
    resized = pyqtSignal() # New signal for resize events
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True) # Required for tooltip detection
        self.viewport().setMouseTracking(True) # Required for QTextEdit viewport
        self._non_empty_prefix = [0]
        
        # Line Number Area
        self.line_number_area = LineNumberArea(self)
        
        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(lambda: self.line_number_area.update())
        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        
        self._rebuild_paragraph_index()
        self.updateLineNumberAreaWidth(0)

    def _on_text_changed(self):
        self._rebuild_paragraph_index()
        self.line_number_area.update()

    def _rebuild_paragraph_index(self):
        prefix = [0]
        count = 0
        block = self.document().begin()
        while block.isValid():
            if block.text().strip():
                count += 1
            prefix.append(count)
            block = block.next()
        self._non_empty_prefix = prefix

    def mouseMoveEvent(self, event):
        """Handle mouse move for tooltips."""
        super().mouseMoveEvent(event)
        cursor = self.cursorForPosition(event.pos())
        self.mouse_moved.emit(cursor.position(), event.globalPosition().toPoint())
    
    def lineNumberAreaWidth(self):
        digits = 1
        max_val = max(1, self.document().blockCount())
        while max_val >= 10:
            max_val //= 10
            digits += 1
        
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))
        self.resized.emit() # Emit signal

    def highlightCurrentLine(self):
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        # Preserve existing extra selections (highlights/memos) might be tricky here
        # For now, skipping full line highlight to avoid conflict with memos/codes
        pass

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#F1F5F9")) # Light gray background

        cursor = self.cursorForPosition(QPoint(0, 0))
        start_block = cursor.block()
        if not start_block.isValid():
            return
        block = start_block
        block_number = block.blockNumber()

        offset = self.verticalScrollBar().value()
        layout = self.document().documentLayout()
        if len(self._non_empty_prefix) <= block_number:
            self._rebuild_paragraph_index()
        current_number = self._non_empty_prefix[block_number] + 1

        while block.isValid():
            rect = layout.blockBoundingRect(block)
            top = rect.top() - offset
            bottom = rect.bottom() - offset
            
            if top > event.rect().bottom():
                break # Below view
            
            if bottom >= event.rect().top():
                # Only draw number if the block has content (is a real paragraph)
                if block.text().strip():
                    number = str(current_number)
                    painter.setPen(QColor("#64748B"))
                    painter.setFont(self.font()) 
                    painter.drawText(0, int(top), self.line_number_area.width() - 5, self.fontMetrics().height(),
                                   Qt.AlignmentFlag.AlignRight, number)
                    current_number += 1
            
            block = block.next()
            block_number += 1

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept drag if it contains code data."""
        if event.mimeData().hasText():
            # Check if we have a selection to code
            if self.textCursor().hasSelection():
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move."""
        if self.textCursor().hasSelection():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle code drop on selected text."""
        if event.mimeData().hasText():
            try:
                import json
                code_data = json.loads(event.mimeData().text())
                if 'id' in code_data and 'name' in code_data:
                    self.code_dropped.emit(code_data)
                    event.acceptProposedAction()
                    return
            except (ValueError, KeyError) as e:
                import logging
                logging.getLogger(__name__).debug(f"MIME veri parse hatası: {e}")
        event.ignore()
