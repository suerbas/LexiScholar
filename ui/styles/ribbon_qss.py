"""
Ribbon Stylesheets for LexiScholar
"""

from .palette import COLORS, SPACING, get_color

MENUBAR_STYLE = f"""
QMenuBar {{
    background-color: {get_color('ribbon_bg')};
    color: {get_color('ribbon_text')};
    padding: {SPACING['xs']}px {SPACING['sm']}px;
    border-bottom: 1px solid {get_color('ribbon_border')};
    font-size: 10pt;
}}

QMenuBar::item {{
    padding: {SPACING['sm']}px {SPACING['lg']}px;
    border-radius: 6px;
    margin: 2px;
    background-color: transparent;
    color: {get_color('ribbon_text_muted')};
}}

QMenuBar::item:selected {{
    background-color: {get_color('ribbon_hover')};
    color: {get_color('ribbon_text')};
}}

QMenuBar::item:pressed {{
    background-color: {get_color('ribbon_active')};
    color: {get_color('ribbon_text')};
}}

QMenu {{
    background-color: {get_color('ribbon_bg')};
    color: {get_color('ribbon_text')};
    border: 1px solid {get_color('ribbon_border')};
    border-radius: {SPACING['sm']}px;
    padding: {SPACING['sm']}px;
}}

QMenu::item {{
    padding: 10px {SPACING['xl']}px;
    border-radius: 6px;
    margin: 2px;
}}

QMenu::item:selected {{
    background-color: {get_color('ribbon_hover')};
}}

QMenu::separator {{
    height: 1px;
    background: {get_color('ribbon_border')};
    margin: {SPACING['sm']}px {SPACING['lg']}px;
}}
"""

TOOLBAR_STYLE = f"""
QToolBar {{
    background-color: {get_color('ribbon_bg')};
    border-bottom: 1px solid {get_color('ribbon_border')};
    padding: {SPACING['sm']}px;
    spacing: {SPACING['md']}px;
}}

QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 10px;
    color: {get_color('ribbon_text')};
    font-size: 9pt;
    font-weight: 500;
}}

QToolButton:hover {{
    background-color: {get_color('ribbon_hover')};
    border: 1px solid {get_color('ribbon_hover')};
    color: {get_color('ribbon_text')};
}}

QToolButton:pressed {{
    background-color: {get_color('ribbon_active')};
    border: 1px solid {get_color('ribbon_hover')};
}}

QLabel {{
    color: {get_color('ribbon_text_muted')};
    font-size: 8.5pt;
    font-weight: 600;
    padding-left: {SPACING['sm']}px;
    padding-right: {SPACING['sm']}px;
}}
"""

RIBBON_GROUP_STYLE = f"""
QFrame {{
    background-color: transparent;
    border: none;
    border-right: 1px solid {get_color('border_hover')};
    margin: 0px {SPACING['sm']}px;
    padding: 0px {SPACING['xs']}px;
}}
"""

RIBBON_GROUP_NO_BORDER_STYLE = RIBBON_GROUP_STYLE.replace(f"border-right: 1px solid {get_color('border_hover')};", "border: none;")

RIBBON_BUTTON_STYLE = f"""
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 2px 2px;
    color: {get_color('text_primary')};
    font-size: 7.5pt;
    font-weight: 500;
    margin: 0px 1px;
    min-width: 50px;
}}

QToolButton:hover {{
    background-color: {get_color('bg_hover')};
    border: 1px solid {get_color('border_hover')};
    color: {get_color('text_primary')};
}}

QToolButton:pressed {{
    background-color: {get_color('border_hover')};
    border: 1px solid {get_color('ribbon_hover')};
    color: {get_color('text_primary')};
}}

QToolButton:disabled {{
    color: {get_color('text_muted')};
    background-color: transparent;
}}

QToolButton:focus {{
    border: 1px solid {get_color('primary_500')};
    background-color: {get_color('bg_hover')};
}}

QToolTip {{
    background-color: {get_color('bg_panel')};
    color: {get_color('text_primary')};
    border: 1px solid {get_color('border_hover')};
}}
"""

RIBBON_LABEL_STYLE = f"""
QLabel {{
    background-color: transparent;
    color: {get_color('text_secondary')};
    font-size: 7.5pt;
    font-weight: 600;
    padding: 2px;
    border: none;
    margin-top: 2px;
    qproperty-alignment: AlignCenter;
}}
"""

TAB_WIDGET_STYLE = f"""
QTabWidget::pane {{
    border-top: 2px solid {get_color('ribbon_hover')};
    background-color: {get_color('ribbon_bg')};
}}

QTabBar::tab {{
    background: {get_color('ribbon_bg')};
    color: {get_color('ribbon_text_muted')};
    padding: 7px 22px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: {SPACING['xs']}px;
    font-weight: 600;
    border: 1px solid transparent;
}}

QTabBar::tab:selected {{
    background: {get_color('ribbon_hover')};
    color: {get_color('ribbon_text')};
    border: 1px solid {get_color('ribbon_hover')};
    border-bottom: 2px solid {get_color('ribbon_hover')};
}}

QTabBar::tab:hover:!selected {{
    background: {get_color('ribbon_active')};
    color: {get_color('ribbon_text')};
}}

QTabBar::tab:focus {{
    border: 1px solid {get_color('primary_500')};
}}
"""
