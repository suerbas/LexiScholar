"""
Main Application Stylesheets for LexiScholar
"""

from .palette import COLORS, SPACING, get_color

CONTEXT_MENU_STYLE = f"""
QMenu {{
    background-color: {get_color('bg_panel')};
    color: {get_color('text_primary')};
    border: 1px solid {get_color('border')};
    border-radius: 6px;
    padding: 4px;
    font-family: 'Segoe UI', sans-serif;
}}

QMenu::item {{
    background: transparent;
    padding: 6px 24px;
    margin: 1px;
    border-radius: 4px;
    font-size: 9.5pt;
    font-weight: 500;
}}

QMenu::item:selected {{
    background-color: {get_color('bg_hover')};
    color: {get_color('text_primary')};
}}

QMenu::item:disabled {{
    color: {get_color('text_muted')};
}}

QMenu::separator {{
    height: 1px;
    background: {get_color('border')};
    margin: 4px 8px;
}}
"""

MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {get_color('bg_main')};
}}

QSplitter {{
    background-color: {get_color('bg_main')};
}}

QSplitter::handle {{
    background-color: {get_color('border_hover')};
    width: 1px;
}}

QSplitter::handle:hover {{
    background-color: {get_color('primary')};
    width: 2px;
}}

QCheckBox {{
    color: {get_color('text_primary')};
    spacing: {SPACING['sm']}px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {get_color('border_strong')};
    border-radius: {SPACING['xs']}px;
    background-color: {get_color('bg_panel')};
}}

QCheckBox::indicator:hover {{
    border-color: {get_color('primary_600')};
    background-color: {get_color('bg_main')};
}}

QCheckBox::indicator:checked {{
    background-color: {get_color('accent_500')};
    border-color: {get_color('accent_500')};
}}

QCheckBox::indicator:checked:hover {{
    background-color: {get_color('accent_600')};
    border-color: {get_color('accent_600')};
}}

QToolTip {{
    background-color: {get_color('bg_panel')};
    color: {get_color('text_primary')};
    border: 1px solid {get_color('border_hover')};
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 9pt;
}}

QPushButton:focus, QToolButton:focus, QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QTextBrowser:focus, QTreeView:focus, QTableWidget:focus, QTabBar::tab:focus {{
    border: 1px solid {get_color('primary_500')};
    outline: none;
}}
""" + CONTEXT_MENU_STYLE

STATUSBAR_STYLE = f"""
QStatusBar {{
    background-color: {get_color('ribbon_bg')};
    color: {get_color('text_secondary')};
    padding: {SPACING['sm']}px {SPACING['lg']}px;
    border-top: 1px solid {get_color('border_hover')};
    font-size: 9pt;
}}

QStatusBar::item {{
    border: none;
}}
"""

TREE_VIEW_STYLE = f"""
QTreeView {{
    background-color: {get_color('bg_panel')};
    color: {get_color('text_primary')};
    border: none;
    font-size: 9pt;
    outline: none;
    show-decoration-selected: 1;
}}

QTreeView::branch:has-siblings:!adjoins-item {{
    border-image: url(ui/assets/vline.png) 0;
}}

QTreeView::branch:has-siblings:adjoins-item {{
    border-image: url(ui/assets/branch_more.png) 0;
}}

QTreeView::branch:!has-children:!has-siblings:adjoins-item {{
    border-image: url(ui/assets/branch_end.png) 0;
}}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {{
    border-image: none;
    image: url(ui/assets/branch_closed.png);
}}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {{
    border-image: none;
    image: url(ui/assets/branch_open.png);
}}

QTreeView::item {{
    padding: {SPACING['xs']}px {SPACING['sm']}px;
    border-radius: {SPACING['xs']}px;
    margin: 1px {SPACING['xs']}px;
}}

QTreeView::item:hover {{
    background-color: {get_color('bg_hover')};
}}

QTreeView::item:selected {{
    background-color: {get_color('bg_selected')};
    color: {get_color('text_primary')};
    border-left: 3px solid {get_color('accent_500')};
}}

QTreeView::item:selected:hover {{
    background-color: {get_color('accent_200')};
}}

QTreeView::branch {{
    background: transparent;
}}

QHeaderView::section {{
    background-color: {get_color('primary_50')};
    color: {get_color('text_secondary')};
    padding: {SPACING['md']}px {SPACING['lg']}px;
    border: none;
    border-bottom: 2px solid {get_color('border_hover')};
    font-weight: 700;
    font-size: 8.5pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QHeaderView::section:hover {{
    background-color: {get_color('bg_hover')};
}}
"""

TEXT_EDIT_STYLE = f"""
QTextEdit {{
    background-color: {get_color('bg_panel')};
    color: {get_color('text_primary')};
    border: none;
    font-size: 11pt;
    padding: {SPACING['xl']}px;
    selection-background-color: {get_color('bg_selected')};
    selection-color: {get_color('text_primary')};
}}
"""

TABLE_STYLE = f"""
QTableWidget {{
    background-color: {get_color('bg_panel')};
    alternate-background-color: {get_color('primary_50')};
    gridline-color: {get_color('border')};
    border: 1px solid {get_color('border')};
    border-radius: 8px;
    font-size: 9pt;
    outline: none;
}}

QTableWidget::item {{
    padding: 8px;
}}

QTableWidget::item:hover {{
    background-color: {get_color('bg_hover')};
}}

QTableWidget::item:selected {{
    background-color: {get_color('bg_selected')};
    color: {get_color('text_primary')};
}}

QHeaderView::section {{
    background-color: {get_color('primary_100')};
    color: {get_color('text_secondary')};
    padding: 8px;
    border: none;
    border-bottom: 2px solid {get_color('border_hover')};
    font-weight: 700;
    font-size: 8.5pt;
}}
"""

SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background: {get_color('bg_main')};
    width: {SPACING['md']}px;
    border-radius: 6px;
    margin: {SPACING['xs']}px;
}}

QScrollBar::handle:vertical {{
    background: {get_color('border_hover')};
    border-radius: 6px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background: {get_color('border_strong')};
}}

QScrollBar::handle:vertical:pressed {{
    background: {get_color('primary_500')};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {get_color('bg_main')};
    height: {SPACING['md']}px;
    border-radius: 6px;
    margin: {SPACING['xs']}px;
}}

QScrollBar::handle:horizontal {{
    background: {get_color('border_hover')};
    border-radius: 6px;
    min-width: 40px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {get_color('border_strong')};
}}

QScrollBar::handle:horizontal:pressed {{
    background: {get_color('primary_500')};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""

PANEL_HEADER_STYLE = f"""
QLabel {{
    background-color: {get_color('bg_main')};
    color: {get_color('text_secondary')};
    font-weight: 700;
    padding: 14px {SPACING['lg']}px;
    font-size: 8.5pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid {get_color('border_hover')};
}}
"""

SCROLL_AREA_STYLE = f"""
QScrollArea {{
    background-color: {get_color('bg_panel')};
    border: none;
}}
"""

PANEL_HEADER_CONTAINER_STYLE = f"""
QFrame#PanelHeader {{
    background-color: {get_color('bg_main')};
    border-bottom: 2px solid {get_color('border_hover')};
}}
"""

PANEL_HEADER_LABEL_STYLE = f"""
QLabel {{
    color: {get_color('text_secondary')};
    font-weight: 700;
    font-size: 8.5pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: none;
    padding: {SPACING['md']}px 14px;
}}
"""

WINDOW_CONTROL_BTN_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {get_color('text_secondary')};
    border: none;
    border-radius: {SPACING['xs']}px;
    font-size: 13px;
    font-weight: 600;
    padding: 2px 6px;
    margin: {SPACING['xs']}px 2px;
    min-width: 26px;
    min-height: 26px;
}}
QPushButton:hover {{
    background-color: {get_color('border_hover')};
    color: {get_color('text_primary')};
}}
QPushButton#DockBtn {{
    color: {get_color('success')};
}}
QPushButton#DockBtn:hover {{
    background-color: {get_color('success_bg')};
}}
QPushButton#CloseBtn {{
    color: {get_color('error')};
}}
QPushButton#CloseBtn:hover {{
    background-color: {get_color('error_bg')};
    color: {get_color('error')};
}}
"""

MINIMIZED_WIDGET_STYLE = f"""
QPushButton {{
    background-color: {get_color('bg_panel')};
    color: {get_color('accent_500')};
    border: 2px solid {get_color('accent_200')};
    border-radius: {SPACING['md']}px;
    padding: 3px {SPACING['md']}px;
    margin: 0 {SPACING['xs']}px;
    font-size: 11px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {get_color('accent_50')};
    border-color: {get_color('accent_500')};
}}
"""
