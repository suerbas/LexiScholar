"""
Semantic Analytics Visualizations
Generates HTML for Sentiment Analysis, Topic Modeling, and NER.
"""

from typing import List, Dict
from datetime import datetime
from .core_utils import (
    _save_html, _generate_empty_html, COMMON_STYLES,
    SENTIMENT_COLORS, ENTITY_COLORS, ENTITY_LABELS, TOPIC_COLORS
)

def generate_sentiment_html(results: List[Dict]) -> str:
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
    <div class="card">
        <h2>Belge Bazlı Sonuçlar</h2>
        <table>
            <thead><tr><th>Belge</th><th>Duygu</th><th>Skor</th><th></th><th>Özet</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</div>
{tooltip_js}
</body></html>"""
    return _save_html(html, "sentiment")

def generate_topics_html(topic_data: Dict) -> str:
    """Generate HTML visualization for topic modeling results."""
    topics = topic_data.get("topics", [])
    doc_topics = topic_data.get("doc_topics", [])
    error = topic_data.get("error", "")
    
    if error: return _generate_empty_html("Konu Modelleme", error)
    if not topics: return _generate_empty_html("Konu Modelleme", "Konu bulunamadı.")
    
    topic_cards = ""
    for i, topic in enumerate(topics):
        color = TOPIC_COLORS[i % len(TOPIC_COLORS)]
        words = topic.get("words", [])
        max_w = words[0][1] if words else 1
        word_tags = ""
        for word, weight in words:
            norm = weight / max_w if max_w > 0 else 0.5
            size = int(13 + norm * 12)
            opacity = 0.5 + norm * 0.5
            word_tags += f'<span class="tag" style="font-size:{size}px;background:{color}22;color:{color};opacity:{opacity}">{word}</span>'
        topic_cards += f"""
        <div class="card" style="border-left:4px solid {color}">
            <h2 style="color:{color}">{topic.get('label', f'Konu {i+1}')}</h2>
            <div style="line-height:2.2">{word_tags}</div>
        </div>"""
    
    doc_rows = ""
    for doc in doc_topics:
        weights = doc.get("topic_weights", [])
        dominant = doc.get("dominant_topic", 0)
        dom_color = TOPIC_COLORS[dominant % len(TOPIC_COLORS)]
        bars = "".join(f'<div style="display:inline-block;width:{max(int(w*100), 2)}%;height:20px;background:{TOPIC_COLORS[j % len(TOPIC_COLORS)]};border-radius:3px;margin-right:1px" title="Konu {j+1}: {int(w*100)}%"></div>' for j, w in enumerate(weights))
        doc_rows += f"""
        <tr>
            <td style="font-weight:600">{doc.get('title', 'Belge')}</td>
            <td><span class="badge" style="background:{dom_color}22;color:{dom_color}">Konu {dominant + 1}</span></td>
            <td><div style="display:flex;border-radius:6px;overflow:hidden">{bars}</div></td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Konu Modelleme</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    {topic_cards}
    <div class="card">
        <h2>Belge-Konu Dağılımı</h2>
        <table>
            <thead><tr><th>Belge</th><th>Baskın Konu</th><th>Konu Dağılımı</th></tr></thead>
            <tbody>{doc_rows}</tbody>
        </table>
    </div>
</div></body></html>"""
    return _save_html(html, "topics")

def generate_entities_html(ner_data: Dict) -> str:
    """Generate HTML visualization for NER results."""
    documents = ner_data.get("documents", [])
    all_entities = ner_data.get("all_entities", {})
    summary = ner_data.get("summary", {})
    
    if not documents or all(len(d.get("entities", [])) == 0 for d in documents):
        return _generate_empty_html("Varlık Tanıma", "Adlandırılmış varlık bulunamadı.")
    
    total = sum(summary.values())
    stats_html = f'<div class="stat-box"><div class="stat-value" style="color:#1E293B">{total}</div><div class="stat-label">Toplam Varlık</div></div>'
    for label, count in sorted(summary.items(), key=lambda x: -x[1]):
        if count == 0: continue
        color = ENTITY_COLORS.get(label, "#64748B")
        stats_html += f'<div class="stat-box"><div class="stat-value" style="color:{color}">{count}</div><div class="stat-label">{ENTITY_LABELS.get(label, label)}</div></div>'
    
    category_html = ""
    for label in ["PER", "LOC", "ORG", "DATE", "MISC"]:
        entities = all_entities.get(label, [])
        if not entities: continue
        color = ENTITY_COLORS.get(label, "#64748B")
        tags = "".join(f'<span class="tag" style="background:{color}22;color:{color}">{e}</span>' for e in sorted(set(entities)))
        category_html += f'<div style="margin-bottom:16px"><h3 style="font-size:16px;color:{color};margin-bottom:8px">{ENTITY_LABELS.get(label, label)}</h3><div style="line-height:2">{tags}</div></div>'
    
    doc_rows = ""
    for doc in documents:
        entities = doc.get("entities", [])
        if not entities: continue
        tags = "".join(f'<span class="badge" style="background:{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}22;color:{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")};margin:2px">{ent.get("text","")}</span>' for ent in entities)
        doc_rows += f"<tr><td style='font-weight:600;white-space:nowrap'>{doc.get('title', 'Belge')}</td><td style='font-size:13px'>{len(entities)}</td><td>{tags}</td></tr>"
    
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Varlık Tanıma (NER)</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    <div class="card"><div class="stat-row">{stats_html}</div></div>
    <div class="card"><h2>Varlık Kategorileri</h2>{category_html}</div>
    <div class="card"><h2>Belge Bazlı Dağılım</h2><table><thead><tr><th>Belge</th><th>Sayı</th><th>Varlıklar</th></tr></thead><tbody>{doc_rows}</tbody></table></div>
</div></body></html>"""
    return _save_html(html, "entities")
