from typing import List, Dict
from ..core_utils import (
    save_html, _generate_empty_html, COMMON_STYLES,
    ENTITY_COLORS, ENTITY_LABELS
)

def generate_entities_html(ner_data: Dict) -> str:
    """Generate HTML visualization for NER results."""
    documents = ner_data.get("documents", [])
    all_entities = ner_data.get("all_entities", {})
    summary = ner_data.get("summary", {})
    
    if not documents or all(len(d.get("entities", [])) == 0 for d in documents):
        return _generate_empty_html("Varlık Tanıma", "Adlandırılmış varlık bulunamadı.")
    
    total = sum(summary.values())
    stats_html = f'<div class="stat-box"><div class="stat-value" style="color:#1E293B">{{total}}</div><div class="stat-label">Toplam Varlık</div></div>'
    for label, count in sorted(summary.items(), key=lambda x: -x[1]):
        if count == 0: continue
        color = ENTITY_COLORS.get(label, "#64748B")
        stats_html += f'<div class="stat-box"><div class="stat-value" style="color:{{color}}">{{count}}</div><div class="stat-label">{{ENTITY_LABELS.get(label, label)}}</div></div>'
    
    category_html = ""
    for label in ["PER", "LOC", "ORG", "DATE", "MISC"]:
        entities = all_entities.get(label, [])
        if not entities: continue
        color = ENTITY_COLORS.get(label, "#64748B")
        tags = "".join(f'<span class="tag" style="background:{{color}}22;color:{{color}}">{{e}}</span>' for e in sorted(set(entities)))
        category_html += f'<div style="margin-bottom:16px"><h3 style="font-size:16px;color:{{color}};margin-bottom:8px">{{ENTITY_LABELS.get(label, label)}}</h3><div style="line-height:2">{{tags}}</div></div>'
    
    doc_rows = ""
    for doc in documents:
        entities = doc.get("entities", [])
        if not entities: continue
        tags = "".join(f'<span class="badge" style="background:{{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}}22;color:{{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}};margin:2px">{{ent.get("text","")}}</span>' for ent in entities)
        doc_rows += f"<tr><td style='font-weight:600;white-space:nowrap'>{{doc.get('title', 'Belge')}}</td><td style='font-size:13px'>{{len(entities)}}</td><td>{{tags}}</td></tr>"
    
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Varlık Tanıma (NER)</title>
<style>{{COMMON_STYLES}}</style></head><body>
<div class="container">
    <div class="card"><div class="stat-row">{{stats_html}}</div></div>
    <div class="card"><h2>Varlık Kategorileri</h2>{{category_html}}</div>
    <div class="card"><h2>Belge Bazlı Dağılım</h2><table><thead><tr><th>Belge</th><th>Sayı</th><th>Varlıklar</th></tr></thead><tbody>{{doc_rows}}</tbody></table></div>
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
            local_tags = "".join(f'<span class="tag" style="background:{{color}}22;color:{{color}}">{{e}}</span>' for e in sorted(set(local_items)))
            local_category_html += f'<div style="margin-bottom:16px"><h3 style="font-size:16px;color:{{color}};margin-bottom:8px">{{ENTITY_LABELS.get(label, label)}}</h3><div style="line-height:2">{{local_tags}}</div></div>'
        if online_items:
            online_tags = "".join(f'<span class="tag" style="background:{{color}}22;color:{{color}}">{{e}}</span>' for e in sorted(set(online_items)))
            online_category_html += f'<div style="margin-bottom:16px"><h3 style="font-size:16px;color:{{color}};margin-bottom:8px">{{ENTITY_LABELS.get(label, label)}}</h3><div style="line-height:2">{{online_tags}}</div></div>'

    for doc in documents:
        comparison = doc.get("comparison", {})
        shared_total += comparison.get("shared_count", 0)
        local_only_total += comparison.get("local_only_count", 0)
        online_only_total += comparison.get("online_only_count", 0)

        local_entities = doc.get("local_entities", [])
        online_entities = doc.get("online_entities", [])
        local_tags = "".join(f'<span class="badge" style="background:{{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}}22;color:{{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}};margin:2px">{{ent.get("text","")}}</span>' for ent in local_entities)
        online_tags = "".join(f'<span class="badge" style="background:{{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}}22;color:{{ENTITY_COLORS.get(ent.get("label","MISC"), "#64748B")}};margin:2px">{{ent.get("text","")}}</span>' for ent in online_entities)
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
            entity_details += f'<div style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:4px 0"><span class="badge" style="background:{{color}}22;color:{{color}};margin:0">{{entity_text}}</span>{{status_badge}}<span class="badge" style="background:#0F172A12;color:#334155;margin:0">Güven: {{confidence}}</span></div>'
        comp_rows += f"<tr><td style='font-weight:600'>{{doc.get('title', 'Belge')}}</td><td>{{local_tags or '-'}}</td><td>{{online_tags or '-'}}</td><td>{{comparison.get('shared_count', 0)}}</td></tr><tr><td></td><td colspan='3' style='background:#F8FAFC'>{{entity_details or '-'}}</td></tr>"

    stat_row += f'<div class="stat-box"><div class="stat-value" style="color:#10B981">{{shared_total}}</div><div class="stat-label">Ortak</div></div>'
    stat_row += f'<div class="stat-box"><div class="stat-value" style="color:#0369A1">{{local_only_total}}</div><div class="stat-label">Sadece Lokal</div></div>'
    stat_row += f'<div class="stat-box"><div class="stat-value" style="color:#7C3AED">{{online_only_total}}</div><div class="stat-label">Sadece AI</div></div>'

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Hibrit Varlık Tanıma (NER)</title>
<style>{{COMMON_STYLES}}</style></head><body>
<div class="container">
    <div class="card" style="background: linear-gradient(135deg, #1e293b, #334155); color: white;">
        <h2 style="color: white;">🔄 Hibrit Varlık Tanıma (NER + Yapay Zeka)</h2>
        <div class="stat-row">{{stat_row}}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
        <div class="card" style="background:#f0f9ff">
            <h2>🧮 Lokal Varlık Kategorileri</h2>
            {{local_category_html or '<p>Kategori bulunamadı.</p>'}}
        </div>
        <div class="card" style="background:#faf5ff">
            <h2>🤖 Yapay Zeka Varlık Kategorileri</h2>
            {{online_category_html or '<p>Kategori bulunamadı.</p>'}}
        </div>
    </div>
    <div class="card">
        <h2>Belge Bazlı Karşılaştırma</h2>
        <table>
            <thead><tr><th>Belge</th><th>Lokal</th><th>Yapay Zeka</th><th>Ortak</th></tr></thead>
            <tbody>{{comp_rows}}</tbody>
        </table>
    </div>
</div></body></html>"""
    return save_html(html, "entities_hybrid")
