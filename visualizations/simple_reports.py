"""
Simple HTML report generation for simple list data like Keywords, KWIC, etc.
"""
import os
import tempfile
from .common import get_template, save_html

def generate_keywords_html(keywords, doc_title="Belge"):
    """
    Generate an HTML report for extracted keywords.
    keywords: List of dicts with {'keyword', 'score', 'count'}
    """
    rows = ""
    for kw in keywords:
        score_pct = f"{kw['score']*100:.1f}%"
        rows += f"""
        <tr>
            <td>{kw['keyword']}</td>
            <td>{kw['count']}</td>
            <td>
                <div style="background-color: #e0e0e0; width: 100px; height: 10px; border-radius: 5px;">
                    <div style="background-color: #4CAF50; width: {score_pct}; height: 100%; border-radius: 5px;"></div>
                </div>
            </td>
        </tr>
        """
        
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Anahtar Kelimeler: {doc_title}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f8f9fa; color: #333; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #f1f1f1; }}
        </style>
    </head>
    <body>
        <p style="color:#64748B; font-size:12px; margin-bottom:15px">Analiz edilen en sık kullanılan anlamlı kelimeler.</p>
        <table>
            <thead>
                <tr>
                    <th>Kelime</th>
                    <th>Frekans</th>
                    <th>Yoğunluk</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    
    return save_html(html_content, "keywords")

def generate_kwic_html(results, keyword, doc_title="Belge"):
    """
    Generate KWIC (Keywords in Context) report.
    results: List of dicts with {'left', 'keyword', 'right', 'doc_title'}
    """
    rows = ""
    for r in results:
        rows += f"""
        <tr>
            <td class="doc">{r['doc_title']}</td>
            <td class="right-align">{r['left']}</td>
            <td class="keyword">{r['keyword']}</td>
            <td class="left-align">{r['right']}</td>
        </tr>
        """
        
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KWIC: {keyword}</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; padding: 20px; }}
            h2 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 14px; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .doc {{ color: #666; font-size: 12px; width: 15%; }}
            .right-align {{ text-align: right; width: 35%; color: #333; }}
            .keyword {{ text-align: center; font-weight: bold; color: #d32f2f; background-color: #ffebee; width: 10%; border-radius: 4px; }}
            .left-align {{ text-align: left; width: 35%; color: #333; }}
        </style>
    </head>
    <body>
        <p style="color:#64748B; font-size:12px; margin-bottom:15px">Kapsam: {doc_title}</p>
        <table>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return save_html(html_content, "kwic")

def generate_document_portrait_html(doc_title, colors):
    """
    Generate Document Portrait visualization (Grid of colors).
    colors: List of hex color strings valid in CSS.
    """
    
    # Create grid items
    grid_items = ""
    for color in colors:
        grid_items += f'<div class="segment" style="background-color: {color};"></div>'
        
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Belge Portresi: {doc_title}</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h2 {{ text-align: center; color: #333; margin-bottom: 30px; }}
            .grid {{ 
                display: flex; 
                flex-wrap: wrap; 
                gap: 2px; 
                justify-content: flex-start;
            }}
            .segment {{
                width: 20px;
                height: 20px;
                border-radius: 2px;
                transition: transform 0.1s;
            }}
            .segment:hover {{ transform: scale(1.5); border: 1px solid #333; }}
            .legend {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="grid">
                {grid_items}
            </div>
            <div class="legend">Her kare, belgedeki kodlanmış bir segmenti temsil eder (belge sırasına göre).</div>
        </div>
    </body>
    </html>
    """
    return save_html(html_content, "portrait")

def generate_sankey_html(data):
    """
    Generate Sankey Diagram using Plotly (via CDN).
    data: dict with 'labels', 'source', 'target', 'value' lists
    """
    # Convert lists to JS strings
    import json
    labels_json = json.dumps(data['labels'])
    source_json = json.dumps(data['source'])
    target_json = json.dumps(data['target'])
    value_json = json.dumps(data['value'])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sankey Diyagramı</title>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body, html {{ margin: 0; padding: 0; height: 100%; overflow: hidden; font-family: 'Segoe UI', sans-serif; }}
            #chart {{ width: 100%; height: 100vh; }}
        </style>
    </head>
    <body>
        <div id="chart"></div>
        <script>
            var data = {{
                type: "sankey",
                orientation: "h",
                node: {{
                    pad: 15,
                    thickness: 20,
                    line: {{ color: "black", width: 0.5 }},
                    label: {labels_json},
                    color: "#6366F1"
                }},
                link: {{
                    source: {source_json},
                    target: {target_json},
                    value: {value_json}
                }}
            }};

            var layout = {{
                font: {{ size: 12 }},
                margin: {{ l: 50, r: 50, b: 50, t: 50 }}
            }};

            Plotly.newPlot('chart', [data], layout, {{responsive: true}});
        </script>
    </body>
    </html>
    """
    return save_html(html_content, "sankey")
