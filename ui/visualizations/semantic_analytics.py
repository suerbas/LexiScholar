"""
Semantic Analytics Visualizations
Generates HTML for Sentiment Analysis, Topic Modeling, and NER.
"""

from typing import List, Dict
from datetime import datetime
from .core_utils import (
    save_html, _generate_empty_html, COMMON_STYLES,
    SENTIMENT_COLORS, ENTITY_COLORS, ENTITY_LABELS, TOPIC_COLORS
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
    return save_html(html, "topics")


def generate_online_topics_html(topic_data: Dict, model_name: str = "AI") -> str:
    """Generate HTML visualization for online topic modeling results."""
    topics = topic_data.get("topics", [])
    doc_topics = topic_data.get("doc_topics", [])
    error = topic_data.get("error", "")
    
    if error: return _generate_empty_html("Online Konu Modelleme", error)
    if not topics: return _generate_empty_html("Online Konu Modelleme", "Konu bulunamadı.")
    
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
        weights = doc.get("topic_weights", []) or []
        dominant = doc.get("dominant_topic", 0)
        if dominant is None: dominant = 0
        dom_color = TOPIC_COLORS[dominant % len(TOPIC_COLORS)]
        
        bars = ""
        if weights:
            bars = "".join(f'<div style="display:inline-block;width:{max(int(w*100), 2)}%;height:20px;background:{TOPIC_COLORS[j % len(TOPIC_COLORS)]};border-radius:3px;margin-right:1px" title="Konu {j+1}: {int(w*100)}%"></div>' for j, w in enumerate(weights))
            
        doc_rows += f"""
        <tr>
            <td style="font-weight:600">{doc.get('title', 'Belge')}</td>
            <td><span class="badge" style="background:{dom_color}22;color:{dom_color}">Konu {dominant + 1}</span></td>
            <td><div style="display:flex;border-radius:6px;overflow:hidden">{bars}</div></td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Online Konu Modelleme</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    <div class="card" style="background: linear-gradient(135deg, #4F46E5, #7C3AED); color: white;">
        <h2 style="color: white;">🤖 Yapay Zeka Konu Modelleme Sonuçları</h2>
        <p>Bu analiz Yapay Zeka modeli tarafından gerçekleştirilmiştir.</p>
    </div>
    {topic_cards}
    <div class="card">
        <h2>Belge-Konu Dağılımı</h2>
        <table>
            <thead><tr><th>Belge</th><th>Baskın Konu</th><th>Konu Dağılımı</th></tr></thead>
            <tbody>{doc_rows}</tbody>
        </table>
    </div>
</div></body></html>"""
    return save_html(html, "topics")


def generate_hybrid_topics_html(topic_data: Dict, model_name: str = "AI") -> str:
    """Generate HTML visualization for hybrid topic modeling results with comparison."""
    local = topic_data.get("local", {})
    online = topic_data.get("online", {})
    comparison = topic_data.get("comparison", {})
    
    local_topics = local.get("topics", [])
    online_topics = online.get("topics", [])
    local_doc_topics = local.get("doc_topics", [])
    online_doc_topics = online.get("doc_topics", [])
    doc_differences = comparison.get("doc_differences", [])
    
    # Local topics section
    local_topic_cards = ""
    for i, topic in enumerate(local_topics):
        color = TOPIC_COLORS[i % len(TOPIC_COLORS)]
        words = topic.get("words", [])
        max_w = words[0][1] if words else 1
        word_tags = ""
        for word, weight in words:
            norm = weight / max_w if max_w > 0 else 0.5
            size = int(13 + norm * 12)
            opacity = 0.5 + norm * 0.5
            word_tags += f'<span class="tag" style="font-size:{size}px;background:{color}22;color:{color};opacity:{opacity}">{word}</span>'
        local_topic_cards += f"""
        <div class="card" style="border-left:4px solid {color}; margin-bottom:10px;">
            <h3 style="color:{color};margin:0">{topic.get('label', f'Konu {i+1}')}</h3>
            <div style="line-height:2">{word_tags}</div>
        </div>"""
    
    # Online topics section
    online_topic_cards = ""
    for i, topic in enumerate(online_topics):
        color = TOPIC_COLORS[i % len(TOPIC_COLORS)]
        words = topic.get("words", [])
        max_w = words[0][1] if words else 1
        word_tags = ""
        for word, weight in words:
            norm = weight / max_w if max_w > 0 else 0.5
            size = int(13 + norm * 12)
            opacity = 0.5 + norm * 0.5
            word_tags += f'<span class="tag" style="font-size:{size}px;background:{color}22;color:{color};opacity:{opacity}">{word}</span>'
        online_topic_cards += f"""
        <div class="card" style="border-left:4px solid {color}; margin-bottom:10px;">
            <h3 style="color:{color};margin:0">{topic.get('label', f'Konu {i+1}')}</h3>
            <div style="line-height:2">{word_tags}</div>
        </div>"""
    
    # Document comparison rows
    comp_rows = ""
    for diff in doc_differences:
        local_dom = diff.get("local_dominant", 0)
        online_dom = diff.get("online_dominant", 0)
        status = diff.get("status", "farklı")
        
        if status == "uyumlu":
            status_color = "#10B981"
            status_text = "✓ Uyumlu"
        elif status == "yakın":
            status_color = "#F59E0B"
            status_text = "~ Yakın"
        else:
            status_color = "#EF4444"
            status_text = "✗ Farklı"
        
        local_color = TOPIC_COLORS[local_dom % len(TOPIC_COLORS)]
        online_color = TOPIC_COLORS[online_dom % len(TOPIC_COLORS)]
        
        comp_rows += f"""
        <tr>
            <td style="font-weight:600">{diff.get('title', 'Belge')}</td>
            <td><span class="badge" style="background:{local_color}22;color:{local_color}">Konu {local_dom + 1}</span></td>
            <td><span class="badge" style="background:{online_color}22;color:{online_color}">Konu {online_dom + 1}</span></td>
            <td><span class="badge" style="background:{status_color}22;color:{status_color};font-weight:bold">{status_text}</span></td>
        </tr>"""
    
    # Summary stats
    summary = comparison.get("summary", {})
    uyumlu = summary.get("uyumlu", 0)
    yakin = summary.get("yakin", 0)
    farkli = summary.get("farklı", 0)
    total = uyumlu + yakin + farkli
    
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Hibrit Konu Modelleme</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    <div class="card" style="background: linear-gradient(135deg, #1e293b, #334155); color: white;">
        <h2 style="color: white;">🔄 Hibrit Konu Modelleme (LDA + Yapay Zeka)</h2>
        <div style="display:flex;gap:20px;margin-top:15px;">
            <div style="text-align:center"><div style="font-size:24px;font-weight:bold;color:#10B981">{uyumlu}</div><div style="font-size:12px">Uyumlu</div></div>
            <div style="text-align:center"><div style="font-size:24px;font-weight:bold;color:#F59E0B">{yakin}</div><div style="font-size:12px">Yakın</div></div>
            <div style="text-align:center"><div style="font-size:24px;font-weight:bold;color:#EF4444">{farkli}</div><div style="font-size:12px">Farklı</div></div>
            <div style="text-align:center"><div style="font-size:24px;font-weight:bold;color:#64748B">{total}</div><div style="font-size:12px">Toplam</div></div>
        </div>
    </div>
    
    <!-- Açıklama Bölümü -->
    <div class="card" style="background:#f8fafc;border-left:4px solid #3b82f6;">
        <h3 style="color:#1e293b;margin-bottom:12px;">📖 Bu Görselleştirme Nedir?</h3>
        <div style="font-size:13px;line-height:1.7;color:#475569;">
            <p style="margin-bottom:10px;"><strong>Konular (Topics):</strong> Belge koleksiyonunuzdaki gizli temaları temsil eder. 
            Her konu, belgelerde birlikte geçen kelime gruplarıdır. Örneğin "eğitim", "öğrenci", "üniversite" kelimeleri 
            bir arada görünüyorsa, bu "Eğitim" temasını oluşturur.</p>
            
            <p style="margin-bottom:10px;"><strong>Kelimeler (Keywords):</strong> Her konunun en karakteristik kelimeleridir. 
            Kelime kutusunun <strong>büyüklüğü</strong> o kelimenin konu için ne kadar önemli olduğunu gösterir (ağırlık/puan). 
            Renkler sadece konuları birbirinden ayırt etmek içindir.</p>
            
            <p style="margin-bottom:10px;"><strong>Konu Numaralandırma:</strong> Konular sırayla numaralanır (Konu 1, Konu 2, vb.) 
            çünkü algoritmalar temaları kendi iç mantığına göre gruplar; bu numaralar sadece referans içindir. 
            Önemli olan konunun etiketi (başlığı) ve içerdiği kelimelerdir.</p>
            
            <p style="margin-bottom:0;"><strong>Uyumlu / Yakın / Farklı:</strong> Sol taraftaki <em>LDA (lokal)</em> ve sağ taraftaki 
            <em>Yapay Zeka (online)</em> modellerin aynı belge için hangi konuyu atadığını karşılaştırır. 
            "Uyumlu" = aynı konu, "Farklı" = farklı konu.</p>
        </div>
    </div>
    
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
        <div class="card" style="background:#f0f9ff">
            <h3 style="color:#0369a1">🧮 LDA (Lokal Model)</h3>
            {local_topic_cards}
        </div>
        <div class="card" style="background:#faf5ff">
            <h3 style="color:#7c3aed">🤖 Yapay Zeka (Online AI)</h3>
            {online_topic_cards}
        </div>
    </div>
    
    <div class="card">
        <h2>Belge Bazlı Karşılaştırma</h2>
        <table>
            <thead><tr><th>Belge</th><th>LDA Baskın</th><th>AI Baskın</th><th>Durum</th></tr></thead>
            <tbody>{comp_rows}</tbody>
        </table>
    </div>
</div></body></html>"""
    return save_html(html, "topics")


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
    return save_html(html, "entities")


def generate_online_entities_html(ner_data: Dict, model_name: str = "AI") -> str:
    documents = []
    for doc in ner_data.get("documents", []):
        documents.append({
            "doc_id": doc.get("doc_id"),
            "title": doc.get("title", "Belge"),
            "entities": doc.get("entities", [])
        })
    payload = {
        "documents": documents,
        "all_entities": ner_data.get("all_entities", {}),
        "summary": ner_data.get("summary", {})
    }
    base_path = generate_entities_html(payload)
    with open(base_path, 'r', encoding='utf-8') as src:
        body = src.read()
    body = body.replace("<div class=\"container\">", f"<div class=\"container\"><div class=\"card\" style=\"background: linear-gradient(135deg, #4F46E5, #7C3AED); color: white;\"><h2 style=\"color: white;\">🤖 Yapay Zeka Varlık Tanıma Sonuçları</h2><p>Bu analiz Yapay Zeka modeli tarafından üretildi.</p></div>", 1)
    return save_html(body, "entities_online")


def generate_hybrid_entities_html(ner_data: Dict, model_name: str = "AI") -> str:
    documents = ner_data.get("documents", [])
    if not documents:
        return _generate_empty_html("Hibrit Varlık Tanıma", "Belge bulunamadı.")

    local_categories = ner_data.get("local_entities", {})
    online_categories = ner_data.get("online_entities", {})
    stat_row = ""
    shared_total = 0
    local_only_total = 0
    online_only_total = 0
    comp_rows = ""

    local_category_html = ""
    online_category_html = ""

    for label in ["PER", "LOC", "ORG", "DATE", "MISC"]:
        local_items = local_categories.get(label, [])
        online_items = online_categories.get(label, [])
        color = ENTITY_COLORS.get(label, "#64748B")
        if local_items:
            local_tags = "".join(f'<span class="tag" style="background:{color}22;color:{color}">{e}</span>' for e in sorted(set(local_items)))
            local_category_html += f'<div style="margin-bottom:16px"><h3 style="font-size:16px;color:{color};margin-bottom:8px">{ENTITY_LABELS.get(label, label)}</h3><div style="line-height:2">{local_tags}</div></div>'
        if online_items:
            online_tags = "".join(f'<span class="tag" style="background:{color}22;color:{color}">{e}</span>' for e in sorted(set(online_items)))
            online_category_html += f'<div style="margin-bottom:16px"><h3 style="font-size:16px;color:{color};margin-bottom:8px">{ENTITY_LABELS.get(label, label)}</h3><div style="line-height:2">{online_tags}</div></div>'

    for doc in documents:
        comparison = doc.get("comparison", {})
        shared_total += comparison.get("shared_count", 0)
        local_only_total += comparison.get("local_only_count", 0)
        online_only_total += comparison.get("online_only_count", 0)

        local_entities = doc.get("local_entities", [])
        online_entities = doc.get("online_entities", [])
        local_tags = "".join(f'<span class="badge" style="background:{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}22;color:{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")};margin:2px">{ent.get("text","")}</span>' for ent in local_entities)
        online_tags = "".join(f'<span class="badge" style="background:{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}22;color:{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")};margin:2px">{ent.get("text","")}</span>' for ent in online_entities)
        entity_details = ""
        for item in comparison.get("entities", []):
            label = item.get("label", "MISC")
            color = ENTITY_COLORS.get(label, "#64748B")
            status = item.get("status", "local_only")
            if status == "shared":
                status_badge = '<span class="badge" style="background:#10B98122;color:#10B981;margin:2px">Ortak</span>'
            elif status == "online_only":
                status_badge = '<span class="badge" style="background:#7C3AED22;color:#7C3AED;margin:2px">Sadece AI</span>'
            else:
                status_badge = '<span class="badge" style="background:#0369A122;color:#0369A1;margin:2px">Sadece Lokal</span>'
            confidence = item.get("confidence_level", "Düşük")
            entity_text = item.get("text", "")
            entity_details += f'<div style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:4px 0"><span class="badge" style="background:{color}22;color:{color};margin:0">{entity_text}</span>{status_badge}<span class="badge" style="background:#0F172A12;color:#334155;margin:0">Güven: {confidence}</span></div>'
        comp_rows += f"<tr><td style='font-weight:600'>{doc.get('title', 'Belge')}</td><td>{local_tags or '-'}</td><td>{online_tags or '-'}</td><td>{comparison.get('shared_count', 0)}</td></tr><tr><td></td><td colspan='3' style='background:#F8FAFC'>{entity_details or '-'}</td></tr>"

    stat_row += f'<div class="stat-box"><div class="stat-value" style="color:#10B981">{shared_total}</div><div class="stat-label">Ortak</div></div>'
    stat_row += f'<div class="stat-box"><div class="stat-value" style="color:#0369A1">{local_only_total}</div><div class="stat-label">Sadece Lokal</div></div>'
    stat_row += f'<div class="stat-box"><div class="stat-value" style="color:#7C3AED">{online_only_total}</div><div class="stat-label">Sadece AI</div></div>'

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Hibrit Varlık Tanıma (NER)</title>
<style>{COMMON_STYLES}</style></head><body>
<div class="container">
    <div class="card" style="background: linear-gradient(135deg, #1e293b, #334155); color: white;">
        <h2 style="color: white;">🔄 Hibrit Varlık Tanıma (NER + Yapay Zeka)</h2>
        <div class="stat-row">{stat_row}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
        <div class="card" style="background:#f0f9ff">
            <h2>🧮 Lokal Varlık Kategorileri</h2>
            {local_category_html or '<p>Kategori bulunamadı.</p>'}
        </div>
        <div class="card" style="background:#faf5ff">
            <h2>🤖 Yapay Zeka Varlık Kategorileri</h2>
            {online_category_html or '<p>Kategori bulunamadı.</p>'}
        </div>
    </div>
    <div class="card">
        <h2>Belge Bazlı Karşılaştırma</h2>
        <table>
            <thead><tr><th>Belge</th><th>Lokal</th><th>Yapay Zeka</th><th>Ortak</th></tr></thead>
            <tbody>{comp_rows}</tbody>
        </table>
    </div>
</div></body></html>"""
    return save_html(html, "entities_hybrid")
