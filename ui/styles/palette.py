"""
Design System Palette for LexiScholar
Defines colors, typography, spacing, and dimensions.
"""

COLORS = {
    'primary_50': '#f8fafc',
    'primary_100': '#f1f5f9',
    'primary_200': '#e2e8f0',
    'primary_300': '#cbd5e1',
    'primary_400': '#94a3b8',
    'primary_500': '#64748b',
    'primary_600': '#475569',
    'primary_700': '#334155',
    'primary_800': '#1e293b',
    'primary_900': '#0f172a',
    
    'primary': '#2E86AB',
    'primary_light': '#3A9CC0',      
    'primary_dark': '#34495E',       
    
    'accent_50': '#fffbeb',
    'accent_100': '#fef3c7',
    'accent_200': '#fde68a',
    'accent_400': '#fbbf24',
    'accent_500': '#f59e0b',
    'accent_600': '#d97706',
    'accent_700': '#b45309',
    
    # Convenience aliases
    'accent': '#f59e0b',  # accent_500
    'accent_dark': '#d97706',  # accent_600
    
    'bg_main': '#f8fafc',
    'bg_panel': '#ffffff',
    'bg_hover': '#f1f5f9',
    'bg_selected': '#fef3c7',
    'bg_sidebar': '#f8fafc',
    'bg_tertiary': '#e2e8f0',
    
    'text_primary': '#0f172a',
    'text_main': '#0f172a',
    'text_secondary': '#475569',
    'text_muted': '#94a3b8',
    'text_on_dark': '#f1f5f9',
    'text_inverse': '#ffffff',  # White text on colored backgrounds
    
    'border': '#BDC3C7',
    'border_hover': '#cbd5e1',
    'border_strong': '#94a3b8',
    
    'success': '#27AE60',
    'success_bg': '#d1fae5',
    'warning': '#ea580c',
    'warning_bg': '#ffedd5',
    'error': '#dc2626',
    'error_bg': '#fee2e2',
    'info': '#0284c7',
    'info_bg': '#e0f2fe',
    
    'action_new': '#F59E0B',
    'action_save': '#27AE60',
    'action_export': '#3B82F6',
    'action_delete': '#EF4444',
    'action_search': '#8B5CF6',
    'action_view': '#0EA5E9',
    'action_help': '#4F46E5',
    'action_undo': '#64748B',
    
    'code_bg_uncoded': '#ffffff',
    'code_bg_coded': '#fef3c7',
    'code_bg_hover': '#fef9e8',
    'code_border_default': '#e2e8f0',
    'code_border_selected': '#f59e0b',
    'code_text_primary': '#0f172a',
    'code_text_label': '#475569',
    
    'code_amber': '#f59e0b',
    'code_emerald': '#059669',
    'code_sky': '#0284c7',
    'code_violet': '#7c3aed',
    'code_rose': '#e11d48',
    'code_teal': '#0d9488',
    
    'ribbon_bg': '#F5F7FA',
    'ribbon_tab_bg': '#e2e8f0',
    'ribbon_tab_selected': '#ffffff',
    'ribbon_active': '#FFD8B1',  # Pastel orange for active ribbon items
    'ribbon_text': '#0f172a',
    'ribbon_text_muted': '#475569',
    'ribbon_hover': '#cbd5e1',
    'ribbon_border': '#cbd5e1',

    # ── Central Tabs (Belge Okuyucu + Analiz Sekmeleri) ──────────────────
    'central_tab_bg':           '#2E86AB',   # Normal tab arka planı (Akademik Mavi)
    'central_tab_selected':     '#34495E',   # Aktif/seçili tab (Gri-Mor)
    'central_tab_hover':        '#3A9CC0',   # Hover durumu (Akademik Mavi açık)
    'central_tab_text':         '#FFFFFF',   # Tab yazısı
    'central_tab_pane_border':  '#CBD5E1',   # Tab içerik çerçevesi

    # ── Browser Toolbar ──────────────────────────────────────────────────
    'browser_toolbar_bg':       '#EEF2FF',   # Tab'dan metin alanına geçiş tonu
    'browser_toolbar_border':   '#C7D2FE',   # Toolbar alt çizgisi
    # ─────────────────────────────────────────────────────────────────────
}

TYPOGRAPHY = {
    'font_body': 'Segoe UI, Inter, -apple-system, system-ui, sans-serif',
    'font_mono': 'Consolas, "Cascadia Code", "Courier New", monospace',
    'font_display': 'Segoe UI Semibold, sans-serif',
    
    'size_xs': '7.5pt',
    'size_sm': '8.5pt',
    'size_base': '9pt',
    'size_md': '10pt',
    'size_lg': '11pt',
    'size_xl': '12pt',
}

SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 24,
    '2xl': 32,
    '3xl': 48,
}

DIMENSIONS = {
    'sidebar_min': 280,
    'sidebar_default': 320,
    'sidebar_max': 480,
    'document_min': 600,
    'document_optimal': 800,
    'coding_stripes_width': 120,
    'ribbon_height': 100,
}

ICONS = {
    'size': 24,
    'size_sm': 16,
    'size_lg': 32,
    'color': '#475569',
    'color_hover': '#0f172a',
    'color_disabled': '#94a3b8',
}

# ── Helper Functions ───────────────────────────────────────────────────────

def get_color(name: str) -> str:
    """Get color by name from palette."""
    return COLORS.get(name, '#000000')

def get_spacing(size: str) -> int:
    """Get spacing size by name."""
    return SPACING.get(size, 0)

def get_dimension(name: str) -> int:
    """Get dimension by name."""
    return DIMENSIONS.get(name, 0)

def get_font(name: str) -> str:
    """Get font family by name."""
    return TYPOGRAPHY.get(name, TYPOGRAPHY['font_body'])

def get_font_size(name: str) -> str:
    """Get font size by name."""
    return TYPOGRAPHY.get(f'size_{name}', TYPOGRAPHY['size_base'])

def style_button(bg_color: str = None, text_color: str = None, border_color: str = None) -> str:
    """Generate consistent button style."""
    bg = bg_color or get_color('primary')
    text = text_color or '#FFFFFF'
    border = border_color or bg
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: {get_font_size('base')};
        }}
        QPushButton:hover {{
            background-color: {get_color('bg_hover')};
        }}
        QPushButton:pressed {{
            background-color: {get_color('bg_selected')};
        }}
    """

def style_panel(bg_color: str = None, border_color: str = None, border_radius: int = 8) -> str:
    """Generate consistent panel style."""
    bg = bg_color or get_color('bg_panel')
    border = border_color or get_color('border')
    return f"""
        QFrame {{
            background-color: {bg};
            border: 1px solid {border};
            border-radius: {border_radius}px;
        }}
    """
