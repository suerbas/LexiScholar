"""
Text Analytics Visualizations
Generates HTML for Keywords, Word Frequency, and KWIC.
"""

from typing import List, Dict
from datetime import datetime
import re
from .core_utils import _save_html, _generate_empty_html, COMMON_STYLES

def generate_keywords_html(keywords: List[Dict], doc_title: str = "Tüm Belgeler") -> str:
    """Generate HTML visualization for keyword extraction results."""
    if not keywords:
        return _generate_empty_html("Anahtar Kelime", "Anahtar kelime bulunamadı.")
    
    tags_html = ""
    for kw in keywords:
        score = kw.get("score", 0.5)
        # Reduced font sizes by 10% as requested
        size = int((14 + score * 18) * 0.9)
        opacity = 0.5 + score * 0.5
        hue = int(220 + score * 40)
        color = f"hsl({hue}, 70%, 40%)"
        bg = f"hsla({hue}, 70%, 40%, 0.12)"
        tags_html += f'<span class="tag" style="font-size:{size}px;color:{color};background:{bg};opacity:{opacity}">{kw["keyword"]}</span>\n'
    
    rows_html = ""
    for i, kw in enumerate(keywords, 1):
        score = kw.get("score", 0)
        pct = int(score * 100)
        color = f"hsl({int(220 + score * 40)}, 70%, 40%)"
        rows_html += f"""
        <tr>
            <td style="width:40px;color:#64748B">{i}</td>
            <td style="font-weight:600">{kw['keyword']}</td>
            <td style="width:200px">
                <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>
            </td>
            <td style="width:80px;text-align:right;color:{color}">{score:.2f}</td>
        </tr>"""
    
    # Help tooltip preserved from previous design or general context
    help_tooltip = "Anahtar Kelime Analizi: Metindeki en önemli kavramları YAKE algoritması kullanarak belirler. Üzerinde durulan konuları skorlarına göre listeler."

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Anahtar Kelime Analizi</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    <div class="card">
        <div style="text-align:center;padding:20px;line-height:2.2">{tags_html}</div>
    </div>
    <div class="card">
        <h2>Detaylı Sıralama</h2>
        <table>
            <thead><tr><th>#</th><th>Anahtar Kelime</th><th>Önem</th><th>Skor</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</div></body></html>"""
    return _save_html(html, "keywords")

def generate_word_frequency_html(frequency_data: List[tuple], doc_title: str = "Tüm Belgeler") -> str:
    """Generate HTML visualization for word frequency results."""
    if not frequency_data:
        return _generate_empty_html("Kelime Frekansı", "Frekans verisi bulunamadı.")
    
    max_count = max(c for w, c in frequency_data) if frequency_data else 1
    rows_html = ""
    for i, (word, count) in enumerate(frequency_data, 1):
        pct = (count / max_count) * 100
        hue = int(200 - (i / len(frequency_data)) * 40)
        color = f"hsl({hue}, 70%, 50%)"
        rows_html += f"""
        <tr>
            <td style="width:40px;color:#64748B">{i}</td>
            <td style="font-weight:600">{word}</td>
            <td style="width:250px">
                <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>
            </td>
            <td style="width:80px;text-align:right;font-weight:700;color:{color}">{count}</td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Kelime Frekansı: {doc_title}</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    <div class="card">
        <table>
            <thead><tr><th>#</th><th>Kelime</th><th>Dağılım</th><th>Frekans</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</div></body></html>"""
    return _save_html(html, "frequency")

def generate_kwic_html(results: List[Dict], keyword: str, doc_title: str = "") -> str:
    """Generate HTML for KWIC analysis."""
    if not results:
        return _generate_empty_html("KWIC Analizi", f"'{keyword}' için sonuç bulunamadı.")
        
    rows_html = ""
    for i, res in enumerate(results, 1):
        rows_html += f"""
        <tr>
            <td style="color:#64748B;font-size:11px;width:50px;white-space:nowrap;text-align:center">{i}</td>
            <td style="text-align:right;width:45%;color:#334155">{res['left']}</td>
            <td style="text-align:center;width:10%;font-weight:700;color:#DC2626;background:#FEF2F2;border-radius:4px">{res['keyword']}</td>
            <td style="text-align:left;width:45%;color:#334155">{res['right']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>KWIC: {keyword}</title>
<style>{COMMON_STYLES}
    td {{
        padding: 8px 10px;
        border-bottom: 1px solid #F1F5F9;
        line-height: 1.45;
        vertical-align: top;
        overflow-wrap: anywhere;
        word-break: break-word;
    }}
</style></head><body>
<div class="container">
    <div class="card">
        <table style="table-layout:fixed">
            <thead>
                <tr>
                    <th style="width:50px;text-align:center">#</th>
                    <th style="text-align:right">Sol Bağlam</th>
                    <th style="text-align:center">KW</th>
                    <th style="text-align:left">Sağ Bağlam</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</div></body></html>"""
    return _save_html(html, "kwic")
