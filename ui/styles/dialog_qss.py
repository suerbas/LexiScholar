"""
Dialog Stylesheets for LexiScholar
"""

from .palette import COLORS, SPACING

DIALOG_STYLE = f"""
QDialog {{
    background-color: {COLORS['bg_panel']};
}}

QLabel {{
    color: {COLORS['text_primary']};
    font-size: 10pt;
}}

QLineEdit {{
    background-color: {COLORS['bg_main']};
    border: 2px solid {COLORS['border']};
    border-radius: {SPACING['sm']}px;
    padding: 6px 12px;
    color: {COLORS['text_primary']};
    font-size: 10pt;
}}

QLineEdit:focus {{
    border-color: {COLORS['accent_500']};
    background-color: {COLORS['bg_panel']};
}}

QLineEdit:hover {{
    border-color: {COLORS['border_hover']};
}}

QPushButton {{
    background-color: {COLORS['accent_500']};
    color: {COLORS['bg_panel']};
    border: none;
    border-radius: {SPACING['sm']}px;
    padding: 6px 16px;
    font-size: 10pt;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {COLORS['accent_600']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_700']};
}}

QPushButton:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}

QPushButton[flat="true"] {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: 2px solid {COLORS['border']};
}}

QPushButton[flat="true"]:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['border_hover']};
}}
"""

SEGMENT_CARD_STYLE = f"""
QFrame {{{{
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-left: 4px solid {{color}};
    border-radius: {SPACING['sm']}px;
    margin: 6px {SPACING['sm']}px;
    padding: 2px;
}}}}

QFrame:hover {{{{
    background-color: {COLORS['bg_main']};
    border-color: {COLORS['border_hover']};
    box-shadow: 0 2px 4px rgba(15, 23, 42, 0.08);
}}}}
"""

CODING_STRIPES_STYLE = f"""
QFrame {{
    background-color: {COLORS['bg_main']};
    border-right: 2px solid {COLORS['border_hover']};
}}
"""

MEMO_DIALOG_STYLE = f"""
QDialog {{
    background-color: {COLORS['bg_main']};
}}

QLabel {{
    color: {COLORS['text_primary']};
    font-size: 10pt;
}}

QLineEdit {{
    background-color: {COLORS['bg_panel']};
    border: 2px solid {COLORS['border']};
    border-radius: {SPACING['sm']}px;
    padding: {SPACING['sm']}px {SPACING['md']}px;
    color: {COLORS['text_primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['accent_500']};
}}

QTextEdit {{
    background-color: {COLORS['bg_panel']};
    border: 2px solid {COLORS['border']};
    border-radius: {SPACING['sm']}px;
    padding: {SPACING['sm']}px;
    color: {COLORS['text_primary']};
}}

QTextEdit:focus {{
    border-color: {COLORS['accent_500']};
}}

QListWidget {{
    background-color: {COLORS['bg_panel']};
    border: 2px solid {COLORS['border']};
    border-radius: {SPACING['sm']}px;
}}

QPushButton {{
    background-color: {COLORS['bg_panel']};
    border: 2px solid {COLORS['border']};
    border-radius: {SPACING['sm']}px;
    padding: 6px {SPACING['md']}px;
    color: {COLORS['text_primary']};
}}

QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['border_hover']};
}}

QPushButton[primary="true"] {{
    background-color: {COLORS['accent_500']};
    color: {COLORS['bg_panel']};
    border: none;
}}

QPushButton[primary="true"]:hover {{
    background-color: {COLORS['accent_600']};
}}
"""

AI_DIALOG_BROWSER_STYLE = f"""
QTextBrowser {{
    font-size: 14px;
    padding: 15px;
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    color: {COLORS['text_primary']};
}}
"""

AI_DIALOG_BTN_SECONDARY = (
    f"padding: 10px 15px; font-weight: 500; "
    f"background-color: {COLORS['bg_hover']}; "
    f"color: {COLORS['text_secondary']}; "
    f"border: 1px solid {COLORS['border_hover']}; "
    f"border-radius: 6px;"
)

AI_DIALOG_BTN_PRIMARY = (
    f"padding: 10px 24px; font-weight: bold; "
    f"background-color: {COLORS['action_export']}; "
    f"color: white; border: none; border-radius: 6px;"
)

AI_DIALOG_BTN_SUCCESS = (
    f"padding: 10px 24px; font-weight: bold; "
    f"background-color: {COLORS['success']}; "
    f"color: white; border: none; border-radius: 6px;"
)

AI_DIALOG_BTN_CLOSE = (
    f"padding: 10px 24px; font-weight: bold; "
    f"background-color: {COLORS['action_help']}; "
    f"color: white; border: none; border-radius: 6px;"
)
