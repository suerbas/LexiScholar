"""
Sentiment Export Utilities
Shared helper functions for exporting sentiment analysis reports.
"""

from typing import List, Dict

def _translate_label(label: str) -> str:
    """Translate sentiment labels to Turkish."""
    translations = {
        'very positive': 'Çok Pozitif',
        'positive': 'Pozitif',
        'neutral': 'Nötr',
        'negative': 'Negatif',
        'very negative': 'Çok Negatif',
        'mixed': 'Karışık',
        'error': 'Hata'
    }
    return translations.get(label, label.capitalize())

def _get_sentiment_color(label: str) -> str:
    """Get hex color for sentiment label."""
    colors = {
        'Çok Pozitif': '059669',
        'Pozitif': '10B981',
        'Nötr': '64748B',
        'Negatif': 'EF4444',
        'Çok Negatif': 'B91C1C',
        'Karışık': 'F59E0B',
        'Hata': '94A3B8'
    }
    return colors.get(label, '64748B')

def _build_html_shell(page_title: str, header_title: str, meta_text: str, stat_cards: List[tuple], section_title: str, section_body: str, footer_text: str) -> str:
    cards_html = "".join(
        f"""
        <div class="stat-card {variant}">
            <div class="stat-value">{value}</div>
            <div class="stat-title">{title}</div>
            <div class="stat-subtitle">{subtitle}</div>
        </div>
        """
        for title, value, subtitle, variant in stat_cards
    )
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>
        :root {{
            --bg: #eef2f7;
            --panel: #ffffff;
            --panel-soft: #f8fafc;
            --text: #0f172a;
            --muted: #64748b;
            --line: #dbe3ee;
            --brand: #4f46e5;
            --brand-2: #7c3aed;
            --positive: #059669;
            --warning: #d97706;
            --negative: #dc2626;
            --neutral: #475569;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
        }}
        .container {{
            max-width: 1180px;
            margin: 0 auto;
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 12px 36px rgba(15, 23, 42, 0.08);
        }}
        .header {{
            background: linear-gradient(135deg, var(--brand), var(--brand-2));
            color: #fff;
            padding: 24px 28px 20px;
        }}
        .header h1 {{
            margin: 0 0 6px 0;
            font-size: 30px;
            line-height: 1.2;
        }}
        .meta {{
            font-size: 14px;
            color: rgba(255,255,255,0.92);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            padding: 18px 20px;
            background: var(--panel-soft);
            border-bottom: 1px solid var(--line);
        }}
        .stat-card {{
            border-radius: 14px;
            padding: 16px 14px;
            color: #fff;
            min-height: 96px;
        }}
        .stat-card.positive {{ background: linear-gradient(135deg, #10b981, #059669); }}
        .stat-card.warning {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
        .stat-card.negative {{ background: linear-gradient(135deg, #ef4444, #dc2626); }}
        .stat-card.neutral {{ background: linear-gradient(135deg, #64748b, #475569); }}
        .stat-card.accent {{ background: linear-gradient(135deg, #3b82f6, #4f46e5); }}
        .stat-value {{ font-size: 30px; font-weight: 800; line-height: 1.1; }}
        .stat-title {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 8px; opacity: 0.95; }}
        .stat-subtitle {{ font-size: 12px; margin-top: 4px; opacity: 0.9; }}
        .section {{ padding: 22px 20px 20px; }}
        .section h2 {{ margin: 0 0 14px 0; font-size: 24px; }}
        .result-table {{ width: 100%; border-collapse: separate; border-spacing: 0; table-layout: fixed; }}
        .result-table th {{
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            background: var(--panel-soft);
            border-bottom: 1px solid var(--line);
            padding: 12px 14px;
        }}
        .result-table td {{
            padding: 14px;
            border-bottom: 1px solid var(--line);
            vertical-align: top;
            background: #fff;
        }}
        .result-table tr:nth-child(even) td {{ background: #fcfdff; }}
        .idx {{ width: 72px; color: var(--muted); font-weight: 700; }}
        .doc {{ font-weight: 700; }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
        }}
        .badge.compare {{ min-width: 78px; justify-content: center; }}
        .score {{ font-size: 18px; font-weight: 800; margin: 8px 0 6px; }}
        .bar {{ width: 100%; height: 8px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }}
        .fill {{ height: 100%; border-radius: 999px; }}
        .summary {{ margin-top: 8px; color: var(--muted); line-height: 1.5; font-size: 13px; }}
        .meta-inline {{ margin-top: 8px; color: var(--muted); font-size: 12px; font-weight: 600; }}
        .model-cell {{ min-width: 0; }}
        .footer {{ padding: 16px 20px; background: #111827; color: #e5e7eb; font-size: 12px; text-align: center; }}
        @media (max-width: 900px) {{
            .result-table, .result-table thead, .result-table tbody, .result-table th, .result-table td, .result-table tr {{ display: block; }}
            .result-table thead {{ display: none; }}
            .result-table td {{ border-bottom: none; padding: 10px 14px; }}
            .result-table tr {{ border-bottom: 1px solid var(--line); padding: 6px 0; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{header_title}</h1>
            <div class="meta">{meta_text}</div>
        </div>
        <div class="stats">{cards_html}</div>
        <div class="section">
            <h2>{section_title}</h2>
            {section_body}
        </div>
        <div class="footer">{footer_text}</div>
    </div>
</body>
</html>"""

def _compute_sentiment_stats(labels: List[str], scores: List[float]) -> Dict:
    label_counts = {}
    for label in labels:
        label_counts[label] = label_counts.get(label, 0) + 1
    total = len(labels)
    pos_total = label_counts.get("very positive", 0) + label_counts.get("positive", 0)
    neg_total = label_counts.get("very negative", 0) + label_counts.get("negative", 0)
    neu_total = label_counts.get("neutral", 0)
    avg_score = sum(scores) / len(scores) if scores else 0.5
    if pos_total > neg_total and pos_total > neu_total:
        overall_sentiment = "Genel olumlu"
    elif neg_total > pos_total and neg_total > neu_total:
        overall_sentiment = "Genel olumsuz"
    else:
        overall_sentiment = "Genel nötr"
    return {
        'pos_total': pos_total,
        'neg_total': neg_total,
        'neu_total': neu_total,
        'pos_pct': _ratio_text(pos_total, total),
        'neg_pct': _ratio_text(neg_total, total),
        'neu_pct': _ratio_text(neu_total, total),
        'avg_percentage': f"{avg_score:.0%}",
        'overall_sentiment': overall_sentiment,
    }

def _ratio_text(part: int, total: int) -> str:
    return f"{(part / total * 100):.1f}%" if total else "0.0%"

def _get_label_hex(label: str) -> str:
    mapping = {
        'very positive': '#059669',
        'positive': '#10B981',
        'neutral': '#64748B',
        'negative': '#EF4444',
        'very negative': '#B91C1C',
        'mixed': '#D97706',
        'error': '#94A3B8'
    }
    return mapping.get(label, '#64748B')

def _score_color(score: float) -> str:
    if score >= 0.7:
        return '#10B981'
    if score >= 0.4:
        return '#64748B'
    return '#EF4444'

def _compare_sentiment_labels(label_a: str, label_b: str) -> Dict:
    if label_a == label_b:
        return {'state': 'exact', 'label': 'Uyumlu'}
    sentiment_scale = {
        'very negative': 0,
        'negative': 1,
        'neutral': 2,
        'positive': 3,
        'very positive': 4,
    }
    if label_a in sentiment_scale and label_b in sentiment_scale:
        if abs(sentiment_scale[label_a] - sentiment_scale[label_b]) == 1:
            return {'state': 'close', 'label': 'Yakın'}
    return {'state': 'different', 'label': 'Farklı'}

def _comparison_color(state: str) -> str:
    if state == 'exact':
        return '#059669'
    if state == 'close':
        return '#D97706'
    return '#DC2626'
