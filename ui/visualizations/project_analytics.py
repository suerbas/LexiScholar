"""
Project Analytics Visualizations
Generates HTML for Portrait, Heatmap, Timeline, Sankey, and Search Results.
"""

from typing import List, Dict
from datetime import datetime
from .core_utils import (
    save_html, _save_plotly_html, _generate_empty_html, 
    COMMON_STYLES
)

def generate_document_portrait_html(doc_title: str, grid_colors: List[str]) -> str:
    """Generate HTML for Document Portrait (grid of colored squares)."""
    if not grid_colors:
        return _generate_empty_html("Belge Portresi", "Görüntülenecek veri yok.")
        
    grid_html = "".join(f'<div style="background-color:{color};width:100%;padding-top:100%;border-radius:2px" title="{color}"></div>' for color in grid_colors)
        
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Belge Portresi: {doc_title}</title>
<style>{COMMON_STYLES}
    .portrait-grid {{
        display: grid;
        grid-template-columns: repeat(30, 1fr);
        gap: 2px;
        background: #F8FAFC;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }}
</style></head><body>
<div class="container">
    <div class="card header-card">
        <h1>🎨 Belge Portresi</h1>
        <p class="subtitle">{doc_title} • {len(grid_colors)} veri noktası</p>
    </div>
    <div class="card">
        <div class="portrait-grid">{grid_html}</div>
        <div style="margin-top:12px;text-align:center;color:#64748B;font-size:12px">
            Belge yapısının renk kodlu görselleştirmesi (Başlangıç → Bitiş)
        </div>
    </div>
</div></body></html>"""
    return save_html(html, "portrait")

def generate_coverage_heatmap_html(data: Dict) -> str:
    """Generate Code Coverage Heatmap using Plotly."""
    if not data or not data.get('z_values'):
        return _generate_empty_html("Kod Kapsa Haritası", "Görüntülenecek veri yok.")

    try:
        import plotly.graph_objects as go
        
        codes = data['codes']
        short_codes = [(c[:30] + '...') if len(c) > 30 else c for c in codes]

        fig = go.Figure(data=go.Heatmap(
            z=data['z_values'],
            x=data['documents'],
            y=codes, # Full names for hover and data points
            colorscale='Viridis',
            hoverongaps=False,
            hovertemplate='<b>Belge:</b> %{x}<br><b>Kod:</b> %{y}<br><b>Kapsam:</b> %{z:.1f}%<extra></extra>'
        ))
        fig.update_layout(
            xaxis_title='Belgeler',
            yaxis_title='Kodlar',
            yaxis=dict(
                tickmode='array',
                tickvals=codes,
                ticktext=short_codes,
                automargin=True
            ),
            height=600,
            margin=dict(l=10, t=20, b=20, r=20) # Reduce left margin if needed, plotly will auto-adjust based on ticktext
        )
        return _save_plotly_html(fig, "heatmap")
    except ImportError:
        return _generate_empty_html("Hata", "Plotly kütüphanesi yüklü değil.")

def generate_code_timeline_html(data: List[Dict], doc_title: str) -> str:
    """Generate Code Activity Timeline."""
    if not data:
        return _generate_empty_html("Kod Zaman Çizelgesi", "Bu belgede kodlanmış bölüm yok.")

    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        codes = sorted(list(set(d['Code'] for d in data)))
        
        for code_name in codes:
            segments = [d for d in data if d['Code'] == code_name]
            for s in segments:
                fig.add_trace(go.Bar(
                    x=[s['End'] - s['Start']],
                    y=[code_name],
                    base=[s['Start']],
                    orientation='h',
                    name=code_name,
                    legendgroup=code_name,
                    showlegend=True if s == segments[0] else False,
                    marker=dict(color=s.get('Color', '#4F46E5')),
                    hovertemplate=f"<b>{code_name}</b><br>Pos: {s['Start']}-{s['End']}<br>Ref: {s.get('Text','')[:30]}...<extra></extra>"
                ))

        short_codes = [(c[:30] + '...') if len(c) > 30 else c for c in codes]

        fig.update_layout(
            xaxis_title='Belge Konumu (Karakter)',
            yaxis_title='Kodlar',
            yaxis=dict(
                tickmode='array',
                tickvals=codes,
                ticktext=short_codes,
                automargin=True
            ),
            barmode='overlay',
            height=min(800, max(400, len(codes) * 40)),
            showlegend=False,
            margin=dict(l=10, t=20, b=20, r=20)
        )
        return _save_plotly_html(fig, "timeline")
    except ImportError:
        return _generate_empty_html("Hata", "Plotly kütüphanesi yüklü değil.")

def generate_sankey_html(data: Dict) -> str:
    """Generate Sankey diagram for code relations."""
    if not data or not data.get('source'):
        return _generate_empty_html("Kod İlişkileri", "Yeterli ilişki verisi bulunamadı.")
        
    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Sankey(
            node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=data['labels'], color="blue"),
            link=dict(source=data['source'], target=data['target'], value=data['value'])
        )])
        # Title removed as it's already in the window header
        fig.update_layout(font_size=12, height=600, margin=dict(t=20, b=20, l=20, r=20))
        return _save_plotly_html(fig, "sankey")
    except ImportError:
        return _generate_empty_html("Hata", "Plotly kütüphanesi yüklü değil.")

def generate_search_results_html(results: List[Dict], search_term: str) -> str:
    """Generate HTML visualization for advanced search results."""
    if not results:
        return _generate_empty_html("Arama Sonuçları", f"'{search_term}' için sonuç bulunamadı.")
    
    rows_html = ""
    for i, res in enumerate(results, 1):
        context = res.get('context', '')
        match = res.get('matched_text', '')
        if match and match in context:
            highlighted = context.replace(match, f'<span style="background:#FEF2F2;color:#DC2626;font-weight:700;padding:0 2px;border-radius:2px">{match}</span>')
        else:
            highlighted = context

        rows_html += f"""
        <tr>
            <td style="width:40px;color:#64748B">{i}</td>
            <td style="width:200px;font-weight:600">{res.get('doc_title', 'Belge')}</td>
            <td>{highlighted}</td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Arama Sonuçları: {search_term}</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    <div class="card header-card">
        <h1>🔍 Arama Sonuçları</h1>
        <p class="subtitle">"{search_term}" • {len(results)} sonuç • {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    </div>
    <div class="card">
        <table>
            <thead><tr><th>#</th><th>Belge</th><th>Bağlam</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</div></body></html>"""
    return save_html(html, "search")
