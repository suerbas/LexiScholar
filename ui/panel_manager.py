"""
Panel Management for LexiScholar MainWindow.
Handles toggling, detaching, and docking of UI panels.
"""

from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QPushButton, QLabel, QStackedWidget
from PyQt6.QtCore import Qt, QPoint
from .icons import IconProvider
from .styles import MINIMIZED_WIDGET_STYLE, COLORS
from .common_ui import show_info, show_warning, show_error, ask_confirmation

class FramelessPanelWindow(QDialog):
    """A frameless dialog that supports resizing from edges."""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self._old_pos = None
        self._margin = 5
        self._resize_mode = None 
        self.setMouseTracking(True)
        # Add a subtle border to frameless window
        self.setStyleSheet("QDialog { border: 1px solid #CBD5E1; background: #FFFFFF; border-radius: 4px; }")

    def toggle_maximize(self):
        """Toggle size to match main window."""
        if hasattr(self, '_is_maximized') and self._is_maximized:
            if hasattr(self, '_normal_geometry'):
                self.setGeometry(self._normal_geometry)
            self._is_maximized = False
        else:
            self._normal_geometry = self.geometry()
            main_window = self.parent()
            if main_window:
                self.setGeometry(main_window.geometry())
            self._is_maximized = True

    def _get_resize_mode(self, pos):
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = self._margin
        mode = ""
        if y < m: mode += "top"
        elif y > h - m: mode += "bottom"
        if x < m: mode += "left"
        elif x > w - m: mode += "right"
        return mode if mode else None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self._resize_mode = self._get_resize_mode(pos)
            self._old_pos = event.globalPosition().toPoint()
            # If not resizing, we might be dragging
            if not self._resize_mode:
                self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mouseReleaseEvent(self, event):
        self._resize_mode = None
        self._old_pos = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()
        
        if not event.buttons():
            mode = self._get_resize_mode(pos)
            if mode == "top" or mode == "bottom": self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif mode == "left" or mode == "right": self.setCursor(Qt.CursorShape.SizeHorCursor)
            else: self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if self._old_pos:
            delta = global_pos - self._old_pos
            if self._resize_mode:
                # Handle Resizing
                geo = self.geometry()
                if "left" in self._resize_mode: geo.setLeft(geo.left() + delta.x())
                elif "right" in self._resize_mode: geo.setRight(geo.right() + delta.x())
                if "top" in self._resize_mode: geo.setTop(geo.top() + delta.y())
                elif "bottom" in self._resize_mode: geo.setBottom(geo.bottom() + delta.y())
                
                if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
                    self.setGeometry(geo)
            else:
                # Handle Dragging
                self.move(self.pos() + delta)
            
            self._old_pos = global_pos

class PanelMixin:
    """Mixin for managing panels in MainWindow."""

    def _sync_maximized_panels(self):
        """Syncs the geometry of all detached windows that are toggled to max size to match MainWindow."""
        if hasattr(self, '_detached_windows'):
            for dialog in self._detached_windows.values():
                if hasattr(dialog, '_is_maximized') and dialog._is_maximized:
                    dialog.setGeometry(self.geometry())
                    
        if hasattr(self, '_detached_analysis_windows'):
            for dialog in self._detached_analysis_windows.values():
                if hasattr(dialog, '_is_maximized') and dialog._is_maximized:
                    dialog.setGeometry(self.geometry())

    def _get_target_widget(self, widget):
        """Drill down into stacks, tabs, or containers to find the actual content widget."""
        from PyQt6.QtWidgets import QStackedWidget, QTabWidget, QWidget
        from .document_browser.base import DocumentBrowserBase
        
        if isinstance(widget, QStackedWidget) or isinstance(widget, QTabWidget):
            return widget.currentWidget()
            
        # Is it a generic container wrapping the real widget? (like DocumentBrowser container)
        if type(widget) is QWidget:
            for child in widget.children():
                if isinstance(child, DocumentBrowserBase) or hasattr(child, 'set_detached'):
                    return child
                    
        return widget

    def _minimize_panel(self, panel_key):
        """Minimize a panel to the status bar (Works for Docked or Detached)."""
        state = self._panel_states[panel_key]
        conf = self._panel_config[panel_key]
        widget = conf['widget']
        
        # Check if we can minimize (at least 1 must be active/visible across entire app)
        visible_count = sum(1 for s in self._panel_states.values() if s['visible'])
        if visible_count <= 1:
            show_info(self, "Bilgi", "En az bir panel açık kalmalıdır.")
            return

        if panel_key in self._detached_windows:
            # Handle Detached minimization: Hide the floating window
            self._detached_windows[panel_key].hide()
        else:
            # Handle Docked minimization: Save sizes and hide from splitter
            splitter = conf['splitter']
            state['sizes'] = splitter.sizes()
            widget.setVisible(False)
            
        state['visible'] = False
        
        # Add interactive label to status bar (Target center)
        btn = QPushButton(conf['label'].replace("\n", " "))
        btn.setStyleSheet(MINIMIZED_WIDGET_STYLE)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._restore_panel(panel_key, btn))
        
        self.minimized_layout.addWidget(btn)
        self.statusbar.showMessage(f"{btn.text()} durum çubuğuna küçültüldü.")

    def _restore_panel(self, panel_key, restore_btn):
        """Restore a minimized panel (Docked or Detached)."""
        state = self._panel_states[panel_key]
        conf = self._panel_config[panel_key]
        widget = conf['widget']
        
        # Remove from status bar
        if restore_btn:
            self.minimized_layout.removeWidget(restore_btn)
            restore_btn.deleteLater()
        
        if panel_key in self._detached_windows:
            # Restore Detached: Just show the window
            self._detached_windows[panel_key].show()
            self._detached_windows[panel_key].raise_()
            self._detached_windows[panel_key].activateWindow()
        else:
            # Restore Docked: Unhide and reset splitter sizes
            splitter = conf['splitter']
            widget.setVisible(True)
            if state['sizes']:
                splitter.setSizes(state['sizes'])
            
        state['visible'] = True
        self.statusbar.showMessage(f"{conf['label'].replace(chr(10), ' ')} geri yüklendi.")

    def _toggle_panel(self, panel_key):
        """Toggle from Ribbon/Shortcut: Restore if hidden, else minimize."""
        state = self._panel_states[panel_key]
        if state['visible']:
            self._minimize_panel(panel_key)
        else:
            self._restore_panel(panel_key, None)

    def _toggle_detach(self, panel_key):
        """Toggle between detaching and docking a panel."""
        if panel_key in self._detached_windows:
            self._dock_panel(panel_key)
        else:
            self._detach_panel(panel_key)

    def _detach_panel(self, panel_key):
        """Detach a panel into a floating frameless window."""
        if panel_key in self._detached_windows:
            self._detached_windows[panel_key].show()
            self._detached_windows[panel_key].raise_()
            self._detached_windows[panel_key].activateWindow()
            return

        conf = self._panel_config[panel_key]
        widget = conf['widget']
        splitter = conf['splitter']
        
        # Save splitter sizes
        current_sizes = splitter.sizes()
        if sum(current_sizes) > 0:
            self._panel_states[panel_key]['sizes'] = current_sizes
        
        # Create floating frameless dialog
        title = conf['label'].replace('\n', ' ')
        dialog = FramelessPanelWindow(self) # Use our custom frameless class
        dialog.setWindowTitle(f"LexiScholar — {title}")
        dialog.setMinimumSize(800, 500) # Increased min-width for toolbar stability
        dialog.resize(900, 700)
        
        # Drill down to actual content widget
        target = self._get_target_widget(widget)
        
        # Update header or toolbar to detached state
        if hasattr(target, 'header'):
            target.header.set_detached(True)
            # Connect Minimize signal for detached state
            try: target.header.minimize_requested.disconnect()
            except (RuntimeError, TypeError): pass
            target.header.minimize_requested.connect(lambda k=panel_key: self._minimize_panel(k))
            try: target.header.dock_requested.disconnect()
            except (RuntimeError, TypeError): pass
            target.header.dock_requested.connect(lambda: self._dock_panel(panel_key))

            try: target.header.maximize_requested.disconnect()
            except (RuntimeError, TypeError): pass
            target.header.maximize_requested.connect(dialog.toggle_maximize)
        
        # For Document Browser (no header), we need to update its internal button state
        if hasattr(target, 'set_detached'):
            target.set_detached(True)
            # Ensure the detach signal now docks it back
            try: target.detach_requested.disconnect()
            except (RuntimeError, TypeError): pass
            target.detach_requested.connect(lambda k=panel_key: self._dock_panel(k))

            # Connect maximize_requested
            try: target.maximize_requested.disconnect()
            except (RuntimeError, TypeError, AttributeError): pass
            if hasattr(target, 'maximize_requested'):
                target.maximize_requested.connect(dialog.toggle_maximize)

        # Move widget to dialog
        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setContentsMargins(1, 1, 1, 1) # Small margin for the border
        widget.setParent(dialog)
        dlg_layout.addWidget(widget)
        widget.show()
        
        # When dialog is closed (X button or close() call), dock back
        dialog.finished.connect(lambda r: self._dock_panel(panel_key))
        
        self._detached_windows[panel_key] = dialog
        dialog.show()
        self.statusbar.showMessage(f"{title} ayrıldı.")

    def _dock_panel(self, panel_key):
        """Restore a detached panel to the main window quadrant."""
        if panel_key not in self._detached_windows:
            return
        
        conf = self._panel_config[panel_key]
        widget = conf['widget']
        splitter = conf['splitter']
        index = conf['index']
        
        # Capture current main splitter state to handle expansion
        main_sizes = self.main_splitter.sizes()
        
        dialog = self._detached_windows.pop(panel_key)
        try:
            dialog.finished.disconnect()
        except RuntimeError:
            pass  # Zaten bağlı değil
        dialog.close()
        dialog.deleteLater()

        # Drill down to actual content widget for header reset
        target = self._get_target_widget(widget)
        if hasattr(target, 'header'):
            target.header.set_detached(False)
            try: target.header.minimize_requested.disconnect()
            except RuntimeError: pass
            target.header.minimize_requested.connect(lambda k=panel_key: self._minimize_panel(k))
            try: target.header.detach_requested.disconnect()
            except RuntimeError: pass
            target.header.detach_requested.connect(lambda k=panel_key: self._detach_panel(k))
        
        if hasattr(target, 'set_detached'):
            target.set_detached(False)
            try: target.detach_requested.disconnect()
            except (RuntimeError, TypeError): pass
            target.detach_requested.connect(lambda k=panel_key: self._detach_panel(k))

        # Re-parent to main splitter
        widget.setParent(splitter)
        splitter.insertWidget(index, widget)
        widget.show()
        
        # Stability: If the main side was collapsed to zero, expand it
        if sum(main_sizes) > 0:
            # If docking back to left and left side is 0
            if panel_key in ['documents', 'codes'] and main_sizes[0] == 0:
                main_sizes = [400, sum(main_sizes) - 400]
            # If docking back to right and right side is 0
            elif panel_key in ['browser', 'segments'] and main_sizes[1] == 0:
                main_sizes = [sum(main_sizes) - 800, 800]
            self.main_splitter.setSizes(main_sizes)

        # Restore internal splitter proportions
        from PyQt6.QtCore import QTimer
        def restore():
            if panel_key in self._panel_states:
                sizes = self._panel_states[panel_key].get('sizes')
                if sizes: splitter.setSizes(sizes)
        QTimer.singleShot(50, restore)
        
        self.statusbar.showMessage(f"{conf['label'].replace(chr(10), ' ')} yerleştirildi.")

    def _toggle_layout(self):
        """Toggle the layout of the right pane."""
        self.btn_layout_toggle.setText("") # Clear any text artifacts
        if self.right_splitter.orientation() == Qt.Orientation.Vertical:
            self.right_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.btn_layout_toggle.setIcon(IconProvider.get_layout_icon("horizontal", COLORS['text_secondary']))
            self.right_splitter.setSizes([600, 300]) 
            self.statusbar.showMessage("Görünüm: Yan Yana")
        else:
            self.right_splitter.setOrientation(Qt.Orientation.Vertical)
            self.btn_layout_toggle.setIcon(IconProvider.get_layout_icon("vertical", COLORS['text_secondary']))
            self.right_splitter.setSizes([500, 300])
            self.statusbar.showMessage("Görünüm: Alt Alta")
