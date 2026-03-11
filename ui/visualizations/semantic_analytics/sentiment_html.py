from typing import List, Dict
from ..core_utils import (
    save_html, _generate_empty_html, COMMON_STYLES,
    SENTIMENT_COLORS
)

def generate_sentiment_html(results: List[Dict], model_name: str = "BERT") -> str:
    """Generate HTML visualization for sentiment analysis results."""
    if not results:
        return _generate_empty_html("Duygu Analizi", "Analiz sonucu bulunamadı.")

    label_counts: Dict[str, int] = {}
    for r in results:
        lbl = r.get("label", "neutral")
        label_counts[lbl] = label_counts.get(lbl, 0) + 1

    scores = [r.get("score", 0.5) for r in results]
    avg_score = sum(scores) / len(scores)
    min_score = min(scores)
    max_score = max(scores)

    pos_total = label_counts.get("very positive", 0) + label_counts.get("positive", 0)
    neg_total = label_counts.get("very negative", 0) + label_counts.get("negative", 0)

    label_map = {
        "very positive": "🌟 Çok Pozitif",
        "positive":      "😊 Pozitif",
        "neutral":       "😐 Nötr",
        "negative":      "😟 Negatif",
        "very negative": "🚨 Çok Negatif",
        "mixed":         "🤔 Karışık",
        "error":         "⚠️ Hata",
    }

    def _label_tip(label: str, score: float, summary: str) -> str:
        pct = int(score * 100)
        tips = {
            "very negative": f"BERT modeli bu metni %{pct} güven ile 'çok negatif' olarak sınıflandırdı.",
            "negative": f"Model bu metni %{pct} güven ile 'negatif' olarak değerlendirdi.",
            "neutral": f"Model bu metni %{pct} güven ile 'nötr' buldu.",
            "positive": f"Model bu metni %{pct} güven ile 'pozitif' olarak sınıflandırdı.",
            "very positive": f"Model bu metni %{pct} güven ile 'çok pozitif' olarak işaretledi.",
            "mixed": f"Model metinde hem olumlu hem olumsuz sinyaller tespit etti (%{pct} güven).",
        }
        tip = tips.get(label, f"Model bu metni %{pct} güven ile '{label}' olarak sınıflandırdı.")
        if summary: tip += f" | Özet: {summary}"
        return tip.replace('"', '&quot;').replace("'", "&#39;")

    avg_tip = f"Ort. Duygu Skoru: %{avg_score:.0%} | Min: %{min_score:.0%} Max: %{max_score:.0%}".replace('"', '&quot;')
    bar_tip = "Ham güven skoru — BERT modelinin bu sınıflandırmaya ne kadar güvendiğini gösterir.".replace('"', '&quot;')

    stats_html = f"""
    <div class="stat-box">
        <div class="stat-value">{len(results)}</div>
        <div class="stat-label">BELGE</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:#10B981">{pos_total}</div>
        <div class="stat-label">POZİTİF</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:#EF4444">{neg_total}</div>
        <div class="stat-label">NEGATİF</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:#64748B">{label_counts.get("neutral", 0)}</div>
        <div class="stat-label">NÖTR</div>
    </div>
    <div class="stat-box tip" data-tip="{avg_tip}" style="cursor:help">
        <div class="stat-value" style="color:#F59E0B">{avg_score:.0%}</div>
        <div class="stat-label">ORT. SKOR ℹ</div>
    </div>"""

    rows_html = ""
    for r in results:
        label    = r.get("label", "neutral")
        color    = SENTIMENT_COLORS.get(label, "#64748B")
        score    = r.get("score", 0.5)
        pct      = int(score * 100)
        summary  = r.get("summary", "")
        label_tr = label_map.get(label, label.capitalize())
        tip      = _label_tip(label, score, summary)

        rows_html += f"""
        <tr>
            <td style="font-weight:600">{r.get("title", "Belge")}</td>
            <td>
                <span class="badge tip" data-tip="{tip}" style="background:{color}22;color:{color};cursor:help">
                    {label_tr}
                </span>
            </td>
            <td style="width:200px">
                <div class="bar-bg tip" data-tip="{bar_tip}" style="cursor:help">
                    <div class="bar-fill" style="width:{pct}%;background:{color}"></div>
                </div>
            </td>
            <td style="width:60px;text-align:right;color:{color};font-weight:bold">{pct}%</td>
            <td style="color:#64748B;font-size:12px">{summary}</td>
        </tr>"""

    tooltip_js = """
<div id="tt" style="display:none; position:fixed; z-index:99999; background:#1E293B; color:#F1F5F9; padding:10px 14px; border-radius:8px; font-size:12px; line-height:1.6; max-width:320px; box-shadow:0 4px 20px rgba(0,0,0,0.35); pointer-events:none; white-space:normal;"></div>
<script>
(function(){
    var tt = document.getElementById('tt');
    document.addEventListener('mouseover', function(e){
        var el = e.target.closest ? e.target.closest('.tip') : null;
        if (!el) { tt.style.display='none'; return; }
        var msg = el.getAttribute('data-tip');
        if (!msg) { tt.style.display='none'; return; }
        tt.innerHTML = msg;
        tt.style.display = 'block';
    });
    document.addEventListener('mousemove', function(e){
        if (tt.style.display === 'none') return;
        var x = e.clientX + 14, y = e.clientY - 10;
        var w = tt.offsetWidth, h = tt.offsetHeight;
        if (x + w > window.innerWidth  - 8) x = e.clientX - w - 14;
        if (y + h > window.innerHeight - 8) y = e.clientY - h - 10;
        tt.style.left = x + 'px';
        tt.style.top  = y + 'px';
    });
    document.addEventListener('mouseout', function(e){
        var el = e.target.closest ? e.target.closest('.tip') : null;
        if (el) tt.style.display = 'none';
    });
})();
</script>"""

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Duygu Analizi</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    <div class="card"><div class="stat-row">{stats_html}</div></div>
        <h2>Belge Bazlı Sonuçlar</h2>
        <table>
            <thead><tr><th>Belge</th><th>Duygu</th><th>Skor</th><th></th><th>Özet</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</div>
{tooltip_js}
</body></html>"""
    
    return save_html(html, "sentiment")

def generate_hybrid_sentiment_html(results: List[Dict], model_name: str = "Yapay Zeka") -> str:
    """Generate HTML visualization for hybrid sentiment analysis results (comparison)."""
    if not results:
        return _generate_empty_html("Hibrit Duygu Analizi", "Analiz sonucu bulunamadı.")

    label_map = {
        "very positive": "🌟 Çok Pozitif",
        "positive":      "😊 Pozitif",
        "neutral":       "😐 Nötr",
        "negative":      "😟 Negatif",
        "very negative": "🚨 Çok Negatif",
        "mixed":         "🤔 Karışık",
        "error":         "⚠️ Hata",
    }

    rows_html = ""
    for r in results:
        local = r.get("local", {})
        online = r.get("online", {})
        
        # Local (BERT)
        l_label = local.get("label", "neutral")
        l_color = SENTIMENT_COLORS.get(l_label, "#64748B")
        l_score = local.get("score", 0.5)
        l_pct   = int(l_score * 100)
        l_summary = local.get("summary", "")
        
        # Online (LLM)
        o_label = online.get("label", "neutral")
        o_color = SENTIMENT_COLORS.get(o_label, "#64748B")
        o_score = online.get("score", 0.5)
        o_pct   = int(o_score * 100)
        o_summary = online.get("summary", "")
        o_conf  = int(online.get("confidence", 0.5) * 100)

        # Match check
        is_match = l_label == o_label
        match_style = "background:#10B98122;color:#10B981" if is_match else "background:#F59E0B22;color:#F59E0B"
        match_text = "✓ Uyumlu" if is_match else "⚠ Farklı"

        rows_html += f"""
        <tr style="border-bottom: 1px solid #E2E8F0">
            <td style="font-weight:600; vertical-align:middle">{r.get("title", "Belge")}</td>
            
            <!-- Local BERT -->
            <td style="background: #F8FAFC; padding: 12px">
                <span class="badge" style="background:{l_color}22;color:{l_color}">{label_map.get(l_label, l_label)}</span>
                <div class="bar-bg" style="margin-top:4px"><div class="bar-fill" style="width:{l_pct}%;background:{l_color}"></div></div>
                <div style="font-size:11px; color:#64748B; margin-top:4px">{l_summary}</div>
            </td>
            
            <!-- Online AI -->
            <td style="background: #FFFFFF; padding: 12px">
                <span class="badge" style="background:{o_color}22;color:{o_color}">{label_map.get(o_label, o_label)}</span>
                <div class="bar-bg" style="margin-top:4px"><div class="bar-fill" style="width:{o_pct}%;background:{o_color}"></div></div>
                <div style="font-size:11px; color:#64748B; margin-top:4px"><b>Güven: %{o_conf}</b> | {o_summary}</div>
            </td>
            
            <td style="text-align:center; vertical-align:middle">
                <span class="badge" style="{match_style}">{match_text}</span>
            </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Hibrit Duygu Analizi</title>
<style>
    {COMMON_STYLES}
    table {{ border-collapse: separate; border-spacing: 0; }}
    th {{ background: #F1F5F9; position: sticky; top: 0; }}
    .bar-bg {{ height: 6px; background: #E2E8F0; border-radius: 3px; overflow: hidden; }}
    .bar-fill {{ height: 100%; }}
</style></head><body>
<div class="container">
    <div class="card">
        <h2>Model Karşılaştırması (BERT vs. Yapay Zeka)</h2>
        <p style="color:#64748B; font-size:14px; margin-bottom:20px">
            Bu tablo, yerel BERT modeli ile online Yapay Zeka modelinin sonuçlarını yan yana getirir. 
            Modeller arasındaki farklar, metindeki nüansları veya ironiyi yakalamak açısından değerlidir.
        </p>
        <table>
            <thead>
                <tr>
                    <th style="width:20%">Belge</th>
                    <th style="width:35%">Lokal Model (BERT)</th>
                    <th style="width:35%">Online Model (AI)</th>
                    <th style="width:10%">Durum</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</div>
</body></html>"""
    return save_html(html, "sentiment_hybrid")
