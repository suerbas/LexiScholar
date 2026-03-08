"""
Main Window for LexiScholar - Refactored for Stage 4
Decomposition of "God Class" into Manager components.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QStatusBar, QTabWidget, QTabBar,
    QLabel, QStackedWidget, QToolButton, QFrame,
    QPushButton, QDialog
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

from database import init_db
from .document_tree import DocumentTree
from .code_tree import CodeTree
from .document_browser import DocumentBrowser
from .retrieved_segments import RetrievedSegments
from .icons import IconProvider
from .styles import MAIN_WINDOW_STYLE, STATUSBAR_STYLE, TAB_WIDGET_STYLE, COLORS
from .audio_player import AudioPlayerBar
from project_manager import ProjectManager
from __version__ import APP_NAME, APP_DISPLAY_VERSION

# Refactoring Managers
from .main_window_manager import DAOManager, UIBuilder, SignalRouter
from .commands import CommandStack
from .shortcuts import ShortcutManager

# Mixins (preserving for logic functionality)
from .handlers import EventHandlers
from .menu_actions import MenuActions
from .analysis import AnalysisActions
from .nlp_actions import NLPActions
from .visualization_actions import VisualizationActions
from .ribbon_setup import RibbonMixin
from .panel_manager import PanelMixin
from .action_handlers import MainWindowActions

@dataclass
class MainWindowConfig:
    """Configuration state for the Main Window."""
    db_path: str = "lexischolar.db"
    project_name: str = ""
    current_coder_id: int = 1
    panel_states: Dict[str, Any] = field(default_factory=dict)
    is_dirty: bool = False


class AnalysisTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._prev_movable = True
        self.setMovable(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setUsesScrollButtons(True)
        self.setExpanding(False)

    def mousePressEvent(self, event):
        try:
            pos = event.position().toPoint()
        except Exception:
            pos = event.pos()
        idx = self.tabAt(pos)
        self._prev_movable = self.isMovable()
        if idx == 0:
            self.setMovable(False)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.setMovable(self._prev_movable)

class MainWindow(QMainWindow, EventHandlers, MenuActions, AnalysisActions, 
                 NLPActions, VisualizationActions, RibbonMixin, PanelMixin, 
                 MainWindowActions):
    """
    Main application window with four-pane QDA layout.
    Refactored with Decomposition of Concerns.
    """
    
    def __init__(self, db_path: str = "lexischolar.db", project_name: str = ""):
        super().__init__()
        self.setObjectName("MainWindow")
        
        # 1. Initialize State/Config
        self.config = MainWindowConfig(db_path=db_path, project_name=project_name)
        self._panel_states = self.config.panel_states
        self._detached_windows = {}
        self._enforcing_tab_order = False
        
        # 2. Database Initialization & DAO management
        init_db(db_path)
        self.daos = DAOManager(db_path)
        self._sync_dao_aliases() # Keep backward compatibility with mixins
        
        # 3. Project Management
        self.project_manager = ProjectManager(db_path)
        self.command_stack = CommandStack()
        self._auto_backup()
        
        # 4. Component Builders
        self.ui_builder = UIBuilder(self)
        self.signal_router = SignalRouter(self)
        
        # 5. Execution
        self.ui_builder.setup_ui()
        self.signal_router.connect_all()
        
        self.shortcut_manager = ShortcutManager(self)
        self._setup_shortcuts()
        
        self._load_initial_data()
        
        # 6. Post-launch: Onboarding
        from .onboarding import start_onboarding_if_needed
        QTimer.singleShot(1500, lambda: start_onboarding_if_needed(self))

    def _setup_shortcuts(self):
        """Register global keyboard shortcuts."""
        self.shortcut_manager.register_all()

    
    def _quick_code(self):
        """Apply currently selected code to current text selection."""
        # 1. Get selected code from code tree
        code = self.code_tree.get_selected_code()
        if not code:
            self.statusbar.showMessage("❌ HATA: Önce kod tepsisinden bir kod seçin!")
            return
            
        # 2. Check if browser has selection
        cursor = self.document_browser.text_edit.textCursor()
        if not cursor.hasSelection():
            self.statusbar.showMessage("❌ HATA: Önce kodlanacak metni seçin!")
            return
            
        # 3. Apply coding (simulating a drop)
        self.document_browser._on_code_dropped(code)
        self.statusbar.showMessage(f"✅ Kodlandı: {code['name']}")

    def _show_onboarding(self):
        """Manually trigger the tutorial."""
        from .onboarding import trigger_onboarding
        trigger_onboarding(self)

    def _show_ai_settings(self):
        """Open the AI settings dialog."""
        from .ai_settings_dialog import AISettingsDialog
        dlg = AISettingsDialog(self)
        dlg.exec()

    def _show_shortcuts_dialog(self):
        """Displays the keyboard shortcut cheat sheet dialog."""
        if hasattr(self, 'shortcut_manager'):
            self.shortcut_manager.show_cheat_sheet()

    def _delete_active_item(self):
        """Smart delete based on which panel has focus."""
        if self.code_tree.tree.hasFocus():
            self.code_tree._delete_selected()
        elif self.document_tree.tree.hasFocus():
            self.document_tree._delete_selected()
        elif self.document_browser.text_edit.hasFocus():
            self.document_browser._remove_code_from_selection()

    def _undo(self):
        """Undo last action."""
        if self.command_stack.undo():
            self.statusbar.showMessage("↩️ Geri alındı", 2000)
            self._refresh_ui_after_command()

    def _redo(self):
        """Redo last action."""
        if self.command_stack.redo():
            self.statusbar.showMessage("↪️ Yinele", 2000)
            self._refresh_ui_after_command()

    def _refresh_ui_after_command(self):
        """Force refresh relevant panels after an undo/redo."""
        # This is a broad refresh, can be optimized later
        self.document_browser._load_coded_segments()
        self._on_item_activated() # Refresh retrieved segments

    def _sync_dao_aliases(self):
        """Provide direct access to DAOs for mixin compatibility."""
        self.doc_dao = self.daos.documents
        self.code_dao = self.daos.codes
        self.segment_dao = self.daos.segments
        self.memo_dao = self.daos.memos
        self.var_dao = self.daos.variables
        self.var_value_dao = self.daos.variable_values
        self.folder_dao = self.daos.folders
        self.journal_dao = self.daos.journals
        self.summary_dao = self.daos.summaries
        self.coder_dao = self.daos.coders
        self.chat_dao = self.daos.chats
        self.current_coder_id = self.config.current_coder_id

    def _auto_backup(self):
        """Perform automatic startup backup."""
        success, info = self.project_manager.create_snapshot()
        if success:
            logging.info(f"Auto-backup created: {info}")
        else:
            logging.warning(f"Auto-backup failed: {info}")

    @property
    def db_path(self): return self.config.db_path

    @db_path.setter
    def db_path(self, value):
        self.config.db_path = value
    
    @property
    def _active_project_name(self): return self.config.project_name

    @_active_project_name.setter
    def _active_project_name(self, value):
        self.config.project_name = value
    
    @property
    def _is_dirty(self): return self.config.is_dirty

    def set_dirty(self, dirty=True):
        self.config.is_dirty = dirty
        self._update_project_label()

    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME} {APP_DISPLAY_VERSION} - Nitel Veri Analizi")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

    def _setup_ui(self):
        """Assembly of the ribbon and four-pane layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_v_layout = QVBoxLayout(central_widget)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(0)
        
        # Ribbon Area (Tabs + Persistent Controls)
        ribbon_area = QFrame()
        ribbon_area.setFixedHeight(110)
        # Match ribbon background and ensure tooltip styling is inherited/applied
        ribbon_area.setStyleSheet(f"""
            QFrame {{ 
                background-color: {COLORS['ribbon_bg']}; 
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        ribbon_area_layout = QHBoxLayout(ribbon_area)
        ribbon_area_layout.setContentsMargins(0, 0, 0, 0)
        ribbon_area_layout.setSpacing(0)

        # 1. Main Ribbon Tabs
        self.ribbon = QTabWidget()
        self.ribbon.setStyleSheet(TAB_WIDGET_STYLE)
        self._setup_ribbon_tabs()
        self._setup_corner_controls() # Add persistent controls
        ribbon_area_layout.addWidget(self.ribbon)
        

        
        main_v_layout.addWidget(ribbon_area)
        
        # Main Splitters
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setContentsMargins(8, 8, 8, 8)
        
        # Left: DocTree & CodeTree
        self.left_splitter = QSplitter(Qt.Orientation.Vertical)
        self.document_tree = DocumentTree(doc_dao=self.doc_dao, folder_dao=self.folder_dao)
        self.code_tree = CodeTree(code_dao=self.code_dao)
        self.left_splitter.addWidget(self.document_tree)
        self.left_splitter.addWidget(self.code_tree)
        self.left_splitter.setSizes([400, 400])
        
        # Right: Browser & Retrieved Segments
        # Default is Horizontal now (Side by Side)
        self.right_splitter = QSplitter(Qt.Orientation.Horizontal) 
        
        # Central Tabs (Document Browser + Analysis Results)
        self.central_tabs = QTabWidget()
        self.central_tabs.setTabsClosable(False)
        self.central_tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        self.central_tabs.setTabBar(AnalysisTabBar(self.central_tabs))
        self.central_tabs.tabBar().tabMoved.connect(self._on_central_tab_moved)
        self.central_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['central_tab_pane_border']};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background: {COLORS['central_tab_bg']};
                color: {COLORS['central_tab_text']};
                padding: 8px 12px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 120px;
                max-width: 220px;
                font-size: 9pt;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['central_tab_selected']};
                color: {COLORS['central_tab_text']};
                font-weight: 700;
            }}
            QTabBar::tab:hover:!selected {{
                background: {COLORS['central_tab_hover']};
            }}
            QTabBar::scroller {{
                width: 28px;
            }}
            QTabBar QToolButton {{
                background: {COLORS['central_tab_bg']};
                color: {COLORS['central_tab_text']};
                border: none;
                border-radius: 4px;
            }}
            QTabBar QToolButton:hover {{
                background: {COLORS['central_tab_hover']};
            }}
        """)

        self.document_browser = DocumentBrowser(db_path=self.db_path)
        self.central_tabs.addTab(self.document_browser, "📄 Belge Okuyucu")
        self.central_tabs.setTabToolTip(0, "📄 Belge Okuyucu")
        
        self.retrieved_segments = RetrievedSegments()
        
        # Right Splitter Configuration (Browser | Retrieved Segments)
        self.right_splitter = QSplitter(Qt.Orientation.Horizontal) # Default Horizontal Layout
        self.right_splitter.addWidget(self.central_tabs)
        self.right_splitter.addWidget(self.retrieved_segments)
        self.right_splitter.setSizes([800, 300]) # Give more space to browser
        
        self.audio_player = AudioPlayerBar(self)
        self.audio_player.hide()
        
        right_col_widget = QWidget()
        right_col_layout = QVBoxLayout(right_col_widget)
        right_col_layout.addWidget(self.right_splitter)
        right_col_layout.addWidget(self.audio_player)
        
        self.main_splitter.addWidget(self.left_splitter)
        self.main_splitter.addWidget(right_col_widget)
        self.main_splitter.setSizes([400, 1000])
        main_v_layout.addWidget(self.main_splitter)
        
        self.setMinimumWidth(800)
        self._setup_panel_configs()
        self._setup_accessibility_metadata()
        self._setup_tab_order()

    def _setup_panel_configs(self):
        """Define panels for PanelMixin management."""
        self._panel_config = {
            'documents': {'label': 'Belgeler', 'widget': self.document_tree, 'splitter': self.left_splitter, 'index': 0},
            'codes': {'label': 'Kodlar', 'widget': self.code_tree, 'splitter': self.left_splitter, 'index': 1},
            'browser': {'label': 'Okuyucu', 'widget': self.central_tabs, 'splitter': self.right_splitter, 'index': 0},
            'segments': {'label': 'Segmentler', 'widget': self.retrieved_segments, 'splitter': self.right_splitter, 'index': 1},
        }
        for key in self._panel_config:
            if key not in self._panel_states:
                self._panel_states[key] = {'visible': True, 'sizes': None}
        self.ribbon.setCurrentIndex(0)
        QTimer.singleShot(300, self._perform_virtual_click_wake_up)

    def _setup_accessibility_metadata(self):
        self.ribbon.setAccessibleName("Uygulama Şeridi")
        self.ribbon.setAccessibleDescription("Ana komut sekmeleri ve proje işlemleri.")
        self.central_tabs.setAccessibleName("Merkez Sekmeler")
        self.central_tabs.setAccessibleDescription("Belge okuyucu ve analiz sonuç sekmeleri.")
        self.main_splitter.setAccessibleName("Ana Düzen")
        self.left_splitter.setAccessibleName("Sol Paneller")
        self.right_splitter.setAccessibleName("Sağ Paneller")
        self.document_tree.setAccessibleName("Belge Ağacı Paneli")
        self.code_tree.setAccessibleName("Kod Ağacı Paneli")
        self.document_browser.setAccessibleName("Belge Okuyucu Paneli")
        self.retrieved_segments.setAccessibleName("Geri Çağrılan Bölümler Paneli")
        if hasattr(self.document_tree, "tree"):
            self.document_tree.tree.setAccessibleName("Belge Listesi")
            self.document_tree.tree.setAccessibleDescription("Belgeleri seçmek, etkinleştirmek ve yönetmek için ağaç görünümü.")
        if hasattr(self.code_tree, "tree"):
            self.code_tree.tree.setAccessibleName("Kod Listesi")
            self.code_tree.tree.setAccessibleDescription("Kodları seçmek ve düzenlemek için ağaç görünümü.")
        if hasattr(self.document_browser, "text_edit"):
            self.document_browser.text_edit.setAccessibleName("Belge Metin Alanı")
            self.document_browser.text_edit.setAccessibleDescription("Belge metnini okuma, seçim ve kodlama alanı.")
        if hasattr(self.retrieved_segments, "btn_query"):
            self.retrieved_segments.btn_query.setAccessibleName("Gelişmiş Sorgu")
            self.retrieved_segments.btn_query.setAccessibleDescription("Kodlu segmentlerde mantıksal sorgu başlatır.")
        if hasattr(self.retrieved_segments, "btn_export"):
            self.retrieved_segments.btn_export.setAccessibleName("Segment Dışa Aktar")
            self.retrieved_segments.btn_export.setAccessibleDescription("Geri çağrılan segmentleri dışa aktarır.")

    def _setup_tab_order(self):
        chain = []
        if hasattr(self, "btn_undo"):
            chain.append(self.btn_undo)
        if hasattr(self, "btn_redo"):
            chain.append(self.btn_redo)
        if hasattr(self, "btn_layout_toggle"):
            chain.append(self.btn_layout_toggle)
        if hasattr(self, "btn_ai_settings"):
            chain.append(self.btn_ai_settings)
        if hasattr(self, "btn_guide"):
            chain.append(self.btn_guide)
        if hasattr(self, "ribbon") and self.ribbon and self.ribbon.tabBar():
            chain.append(self.ribbon.tabBar())
        if hasattr(self.document_tree, "tree"):
            chain.append(self.document_tree.tree)
        if hasattr(self.code_tree, "tree"):
            chain.append(self.code_tree.tree)
        if hasattr(self.document_browser, "text_edit"):
            chain.append(self.document_browser.text_edit)
        if hasattr(self.retrieved_segments, "btn_query"):
            chain.append(self.retrieved_segments.btn_query)
        if hasattr(self.retrieved_segments, "btn_export"):
            chain.append(self.retrieved_segments.btn_export)
        if hasattr(self.retrieved_segments, "btn_prev_page"):
            chain.append(self.retrieved_segments.btn_prev_page)
        if hasattr(self.retrieved_segments, "btn_next_page"):
            chain.append(self.retrieved_segments.btn_next_page)
        if self.central_tabs and self.central_tabs.tabBar():
            chain.append(self.central_tabs.tabBar())
        for i in range(len(chain) - 1):
            self.setTabOrder(chain[i], chain[i + 1])

    def _on_tab_close_requested(self, index):
        """Handle tab close requests."""
        if index > 0: # Never close the first tab (Document Browser)
            widget = self.central_tabs.widget(index)
            self.central_tabs.removeTab(index)
            if widget:
                widget.deleteLater()

    def _on_central_tab_moved(self, from_index: int, to_index: int):
        if self._enforcing_tab_order:
            return
        doc_idx = self.central_tabs.indexOf(self.document_browser)
        if doc_idx != 0:
            self._enforcing_tab_order = True
            try:
                self.central_tabs.tabBar().moveTab(doc_idx, 0)
            finally:
                self._enforcing_tab_order = False

    def _close_tab_from_button(self):
        btn = self.sender()
        if not btn:
            return
        bar = self.central_tabs.tabBar()
        for i in range(self.central_tabs.count()):
            if bar.tabButton(i, QTabBar.ButtonPosition.RightSide) is btn:
                self._on_tab_close_requested(i)
                return

    def _install_tab_close_button(self, index: int):
        if index <= 0:
            self.central_tabs.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            return
        btn = QToolButton(self.central_tabs.tabBar())
        btn.setText("✕")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(18, 18)
        btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                border: none;
                color: {COLORS['central_tab_text']};
                font-size: 11px;
                font-weight: 700;
                padding: 0px;
                margin-right: 4px;
                border-radius: 3px;
            }}
            QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.20);
                color: white;
            }}
        """)
        btn.clicked.connect(self._close_tab_from_button)
        self.central_tabs.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, btn)

    def add_analysis_tab(self, widget: QWidget, title: str, help_tooltip: str = None, help_page: str = "analysis_tools.html", help_anchor: str = None, subtitle: str = None, is_analysis_mode: bool = True):
        """Add a new analysis result tab wrapped in a container with controls."""
        from .panel_header import PanelHeader
        
        container = QWidget()
        container.setObjectName("AnalysisTabContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = PanelHeader(title, container, has_minimize=False)
        
        if is_analysis_mode:
            header.set_analysis_mode(True, subtitle=subtitle or "")
            if hasattr(widget, "detach_requested"):
                widget.detach_requested.connect(lambda: self._detach_dynamic_tab(container, title))

        # Delegate custom header controls (like Export or Save buttons) to the widget itself
        if hasattr(widget, "setup_header_controls"):
            widget.setup_header_controls(header.custom_layout)
            # Auto-register all added widgets as persistent (survive detach/dock rebuilds)
            for i in range(header.custom_layout.count()):
                item = header.custom_layout.itemAt(i)
                if item and item.widget() and item.widget() not in header._persistent_widgets:
                    header._persistent_widgets.append(item.widget())
        
        if help_tooltip:
            header.set_help(help_tooltip, help_page, help_anchor)
        elif "AI:" in title:
            header.set_help(
                "AI Sohbet: Seçili belgenin içeriği üzerinden sorular sorun; yanıtlar belge bağlamına göre üretilir.",
                "analysis_tools.html",
                "ai-chat"
            )

        # Connect detach
        header.detach_requested.connect(lambda: self._detach_dynamic_tab(container, title))
        
        layout.addWidget(header)
        layout.addWidget(widget)
        
        # Store metadata on the container widget for later
        container.setProperty("original_widget", widget)
        container.setProperty("title", title)
        
        index = self.central_tabs.addTab(container, title)
        self.central_tabs.setTabToolTip(index, title)
        self._install_tab_close_button(index)
        self.central_tabs.setCurrentIndex(index)

    def _detach_dynamic_tab(self, container: QWidget, title: str):
        """Detach a dynamic analysis tab into a floating window."""
        from .panel_manager import FramelessPanelWindow
        from .panel_header import PanelHeader
        
        # 1. Create dialog
        dialog = FramelessPanelWindow(self)
        dialog.setMinimumSize(900, 600)
        dialog.setWindowTitle(f"LexiScholar — {title}")
        
        # 2. Update header state
        header = container.findChild(PanelHeader)
        if header:
            header.show() # Ensure header is visible when detached
            header.set_detached(True)
            try: header.detach_requested.disconnect()
            except: pass
        # Handle window closure
        container.is_docking = False
        
        def on_close():
            if not container.is_docking:
                # User literally wants to close/delete the analysis
                self._remove_detached_analysis(container, dialog)
            else:
                self._dock_dynamic_tab(container, dialog)

        header.close_requested.connect(dialog.close)
        header.dock_requested.connect(lambda: setattr(container, 'is_docking', True))
        header.dock_requested.connect(lambda: self._dock_dynamic_tab(container, dialog))
        header.maximize_requested.connect(dialog.toggle_maximize)

        # 3. Move widget
        # Remove from tabs
        idx = self.central_tabs.indexOf(container)
        if idx >= 0:
            self.central_tabs.removeTab(idx)
            
        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setContentsMargins(1, 1, 1, 1)
        container.setParent(dialog)
        dlg_layout.addWidget(container)
        container.show()
        
        # Store reference
        if not hasattr(self, '_detached_analysis_windows'):
            self._detached_analysis_windows = {}
        self._detached_analysis_windows[id(container)] = dialog
        
        dialog.finished.connect(lambda r: on_close())
        dialog.show()
        self.statusbar.showMessage(f"'{title}' ayrıldı.")

    def _remove_detached_analysis(self, container, dialog):
        """Completely close and delete a detached analysis window."""
        if not dialog: return
        
        # Remove reference
        if hasattr(self, '_detached_analysis_windows'):
            self._detached_analysis_windows.pop(id(container), None)
            
        title = container.property("title") or "Analiz"
        
        # Disconnect any lingering signals before deletion
        try: dialog.finished.disconnect()
        except: pass
        
        # Delete the widget and dialog
        container.deleteLater()
        dialog.close()
        dialog.deleteLater()
        
        self.statusbar.showMessage(f"'{title}' kapatıldı.")

    def _dock_dynamic_tab(self, container: QWidget, dialog: QDialog):
        """Dock a detached dynamic analysis tab back into the central tabs."""
        if not dialog: return
        from .panel_header import PanelHeader
        
        # 1. Update header
        header = container.findChild(PanelHeader)
        if header:
            header.set_detached(False)
            try: header.dock_requested.disconnect()
            except: pass
            title = container.property("title")
            header.detach_requested.connect(lambda: self._detach_dynamic_tab(container, title))
            
        # 2. Re-parent and hide dialog
        try:
            dialog.finished.disconnect()
        except: pass
        dialog.close()
        
        title = container.property("title") or "Analiz"
        index = self.central_tabs.addTab(container, title)
        self.central_tabs.setTabToolTip(index, title)
        self._install_tab_close_button(index)
        self.central_tabs.setCurrentIndex(index)
        
        # Remove reference
        if hasattr(self, '_detached_analysis_windows'):
            self._detached_analysis_windows.pop(id(container), None)
        
        self.statusbar.showMessage(f"'{title}' yerleştirildi.")

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.statusbar.setStyleSheet(STATUSBAR_STYLE)
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Hazır")

        self.minimized_container = QWidget()
        self.minimized_layout = QHBoxLayout(self.minimized_container)
        self.minimized_layout.setContentsMargins(0, 0, 0, 0)

        self.statusbar.addPermanentWidget(QLabel(""), 1)
        self.statusbar.addPermanentWidget(self.minimized_container)
        self.statusbar.addPermanentWidget(QLabel(""), 1)

        # ── NLP Model Durumu Göstergesi ──────────────────────────────────
        try:
            from .nlp_status_widget import NLPStatusWidget
            self.nlp_status = NLPStatusWidget()
            self.statusbar.addPermanentWidget(self.nlp_status)
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"NLPStatusWidget yüklenemedi: {e}")
        # ─────────────────────────────────────────────────────────────────

        self.project_name_label = QLabel("📂 Proje yüklenmedi")
        self.project_name_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-weight: bold; margin-right: 10px;"
        )
        self.statusbar.addPermanentWidget(self.project_name_label)


    def _perform_virtual_click_wake_up(self):
        """Ghost click to wake up OS hover states."""
        try:
            import ctypes
            from PyQt6.QtGui import QCursor
            pos = QCursor.pos()
            win_pos = self.mapToGlobal(self.rect().topLeft())
            ctypes.windll.user32.SetCursorPos(win_pos.x() + 20, win_pos.y() + 10)
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
            ctypes.windll.user32.SetCursorPos(pos.x(), pos.y())
        except Exception as e:
            logging.getLogger(__name__).warning(f"OS hover wake-up failed: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_sync_maximized_panels'):
            self._sync_maximized_panels()

    def moveEvent(self, event):
        super().moveEvent(event)
        if hasattr(self, '_sync_maximized_panels'):
            self._sync_maximized_panels()

    def closeEvent(self, event):
        if self._confirm_exit(): event.accept()
        else: event.ignore()

    def _check_updates(self):
        """Check for application updates."""
        from __version__ import APP_VERSION
        from PyQt6.QtWidgets import QMessageBox
        
        # In a real app, this would fetch from a remote URL.
        # For now, we simulate a check.
        QMessageBox.information(
            self, 
            "Güncelleme Kontrolü", 
            f"Mevcut sürümünüz: {APP_VERSION}\n\nUygulamanız günceldir. Yeni bir güncelleme bulunduğunda size bildirilecektir."
        )

    def _show_about(self):
        """Show about dialog."""
        from .help_window import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()
