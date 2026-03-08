"""
Core Utilities for NLP Visualizations
Shared constants, HTML templates, and file savers.
"""

import os
import tempfile
from datetime import datetime

# ============================================================================
# Color Palettes
# ============================================================================

SENTIMENT_COLORS = {
    "very positive": "#059669",
    "positive": "#10B981",
    "neutral": "#64748B",
    "negative": "#EF4444",
    "very negative": "#B91C1C",
    "mixed": "#F59E0B",
    "error": "#94A3B8"
}

ENTITY_COLORS = {
    "PER": "#8B5CF6",
    "LOC": "#3B82F6",
    "ORG": "#F59E0B",
    "DATE": "#10B981",
    "MISC": "#64748B"
}

ENTITY_LABELS = {
    "PER": "👤 Kişi",
    "LOC": "📍 Yer",
    "ORG": "🏢 Kurum",
    "DATE": "📅 Tarih",
    "MISC": "🏷️ Diğer"
}

TOPIC_COLORS = [
    "#4F46E5", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
    "#3B82F6", "#EC4899", "#14B8A6", "#F97316", "#6366F1"
]

# ============================================================================
# Common HTML Styles
# ============================================================================

COMMON_STYLES = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body, html {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: #F1F5F9;
        color: #1E293B; margin: 0; padding: 0;
        width: 100%; height: 100%;
    }
    .container { width: 100%; padding: 12px; }
    .card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px; padding: 16px; margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .header-card {
        background: linear-gradient(135deg, #6366F1, #60A5FA);
        color: white; text-align: left; padding: 18px 16px;
        display: flex; align-items: center; gap: 15px;
    }
    .header-card h1 { color: white; margin-bottom: 2px; }
    .header-card .subtitle { color: rgba(255,255,255,0.9); }
    .header-icon {
        font-size: 48px;
        line-height: 1;
        cursor: help;
        transition: transform 0.2s;
    }
    .header-icon:hover { transform: scale(1.1); }
    .header-content { flex: 1; }
    h1 { font-size: 20px; font-weight: 700; margin-bottom: 4px; color: #1E293B; }
    h2 { font-size: 15px; font-weight: 600; margin-bottom: 12px; color: #1E293B; }
    h3 { color: #334155; }
    .subtitle { color: #64748B; font-size: 12px; }
    .stat-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .stat-box {
        flex: 1; min-width: 80px; background: #F8FAFC;
        border-radius: 8px; padding: 10px; text-align: center;
        border: 1px solid #E2E8F0;
    }
    .stat-value { font-size: 24px; font-weight: 700; color: #1E293B; }
    .stat-label { font-size: 10px; color: #64748B; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }
    table { width: 100%; border-collapse: collapse; }
    th { text-align: left; padding: 8px 10px; font-size: 11px; color: #64748B;
         text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #E2E8F0; }
    td { padding: 8px 10px; border-bottom: 1px solid #F1F5F9; font-size: 13px; color: #334155; }
    tr:hover { background: #F8FAFC; }
    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 20px;
        font-size: 11px; font-weight: 600;
    }
    .bar-bg { background: #E2E8F0; border-radius: 6px; height: 6px; position: relative; }
    .bar-fill { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
    .tag {
        display: inline-block; padding: 4px 10px; border-radius: 6px;
        font-size: 12px; margin: 3px; font-weight: 500;
        transition: transform 0.2s, box-shadow 0.2s; cursor: default;
    }
    .tag:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
"""

def _save_html(html: str, prefix: str = "nlp") -> str:
    """Save HTML content to a temp file and return the path."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"lexischolar_{prefix}_{datetime.now().strftime('%H%M%S')}.html")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return file_path

def _save_plotly_html(fig, prefix: str) -> str:
    """Save Plotly figure to HTML file."""
    try:
        from plotly.offline import plot
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"lexischolar_{prefix}_{datetime.now().strftime('%H%M%S')}.html")
        plot(fig, filename=file_path, auto_open=False)
        return file_path
    except ImportError:
        return _generate_empty_html("Hata", "Plotly kütüphanesi yüklü değil.")

def _generate_empty_html(title: str, message: str) -> str:
    html = f"""<!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>{title}</title><style>{COMMON_STYLES}</style></head>
    <body><div class="container"><div class="card" style="text-align:center;padding:50px">
    <h3>{title}</h3><p>{message}</p>
    </div></div></body></html>"""
    return _save_html(html, "empty")
