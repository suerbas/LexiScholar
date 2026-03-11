from typing import List, Dict
from ..core_utils import (
    save_html, _generate_empty_html, COMMON_STYLES,
    TOPIC_COLORS
)

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
