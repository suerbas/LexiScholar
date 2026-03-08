"""
Styles for Search Dialog components.
"""

def input_style():
    return """
        QLineEdit, QComboBox, QSpinBox {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 4px 8px;
            color: #1E293B;
            min-height: 24px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border-color: #4F46E5;
        }
    """

def button_style(color, hover_color=None, text_color="white"):
    h_color = hover_color if hover_color else color
    return f"""
        QPushButton {{
            background-color: {color};
            color: {text_color};
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {h_color};
        }}
        QPushButton:disabled {{
            background-color: #F1F5F9;
            color: #94A3B8;
            border: 1px solid #E2E8F0;
        }}
    """

def group_style():
    return """
        QGroupBox {
            font-weight: bold;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            color: #475569;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
        }
    """
