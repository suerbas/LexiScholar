"""
Word Cloud Visualization for LexiScholar.
"""

import json
import tempfile
from pathlib import Path
from typing import List, Tuple
from .common import _get_js_content

def generate_word_cloud_html(word_freq: List[Tuple[str, int]], output_path: str = None) -> str:
    """
    Generate an interactive HTML word cloud visualization using D3.js.
    """
    
    # Prepare data for JS
    words_data = [{"text": w[0], "size": w[1]} for w in word_freq[:300]]
    
    # D3.js and d3-cloud library content
    d3_js = _get_js_content("d3.min.js")
    d3_cloud_js = _get_js_content("d3.layout.cloud.js")
    
    # Fallback to CDN if local files missing
    scripts = ""
    if d3_js:
        scripts += f"<script>{d3_js}</script>"
    else:
        scripts += '<script src="https://d3js.org/d3.v7.min.js"></script>'
        
    if d3_cloud_js:
        scripts += f"<script>{d3_cloud_js}</script>"
    else:
        scripts += '<script src="https://cdn.jsdelivr.net/npm/d3-cloud/3"></script>'

    html_content = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LexiScholar - Profesyonel Kelime Bulutu</title>
    {scripts}
    <style>
        * {{
            box-sizing: border-box;
        }}
        body, html {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: white;
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        
        .canvas-container {{
            width: 100%;
            height: 100vh;
            background: white;
            position: relative;
            overflow: hidden;
        }}
        
        #word-cloud {{
            width: 100%;
            height: 100%;
        }}
        
        .tooltip {{
            position: fixed;
            background: rgba(15, 23, 42, 0.95);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 11px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.1s;
            z-index: 1000;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .excluded-list {{
            position: absolute;
            bottom: 10px;
            left: 20px;
            font-size: 11px;
            color: #64748B;
            background: rgba(255, 255, 255, 0.9);
            padding: 4px 10px;
            border-radius: 8px;
            pointer-events: none;
            border: 1px solid #E2E8F0;
        }}
        
        .restore-word {{
            cursor: pointer;
            text-decoration: underline;
            margin: 0 4px;
            color: #EF4444;
            pointer-events: auto;
        }}
    </style>
</head>
<body>

    <div class="canvas-container" id="container">
        <div id="word-cloud"></div>
        <div class="tooltip" id="tooltip"></div>
    </div>
    
    <div class="excluded-list" id="excludedList" style="display:none">
        Gizlenen kelimeler: <span id="excludedWords">-</span>
    </div>

    <script>
        // Data from Python
        const rawData = {json.dumps(words_data)};
        
        // State
        let excluded = new Set();
        let currentMaxWords = 50;
        let currentScale = 80;
        let minFrequency = 1;
        
        // Config based on MAXQDA Blue Theme
        const colors = [
            "#1E3A8A", "#1E40AF", "#1D4ED8", "#2563EB", "#3B82F6", 
            "#0F766E", "#0D9488", "#14B8A6", "#059669", "#10B981"
        ];
        
        // Global JS API for Python
        window.setWordCount = function(val) {{
            currentMaxWords = parseInt(val);
            regenerate();
        }};
        
        window.setScale = function(val) {{
            currentScale = parseInt(val);
            regenerate();
        }};
        
        window.setMinFreq = function(val) {{
            minFrequency = parseInt(val);
            regenerate();
        }};

        window.reshuffle = function() {{
            regenerate();
        }};

        window.exportAsImage = function() {{
            exportImage();
        }};

        window.clearExclusions = function() {{
            excluded.clear();
            updateExcludedList();
            regenerate();
        }};
        
        // Initialize
        regenerate();
        
        function regenerate() {{
            const maxWords = currentMaxWords;
            const targetMaxFontSize = currentScale;
            const minFontSize = Math.max(8, targetMaxFontSize / 6);
            
            // Filter and sort
            let filtered = rawData
                .filter(d => !excluded.has(d.text) && d.size >= minFrequency)
                .sort((a, b) => b.size - a.size);
            
            let dataForCloud = filtered.slice(0, maxWords);
                
            if (dataForCloud.length === 0) {{
                document.getElementById('word-cloud').innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#94A3B8;font-weight:600">Gösterilecek kelime kalmadı</div>';
                return;
            }}
            
            const maxVal = dataForCloud[0].size;
            const minVal = dataForCloud[dataForCloud.length - 1].size;
            
            // Scale font size
            const fontScale = d3.scaleLinear()
                .domain([minVal, maxVal])
                .range([minFontSize, targetMaxFontSize]);
                
            // Clear previous
            document.getElementById('word-cloud').innerHTML = '';
            
            const container = document.getElementById('container');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            // Layout
            d3.layout.cloud()
                .size([width - 40, height - 40])
                .words(dataForCloud.map(d => ({{ 
                    text: d.text, 
                    size: fontScale(d.size), 
                    rawCount: d.size 
                }})))
                .padding(2) // Compact layout
                .rotate(() => (~~(Math.random() * 2) * 90)) 
                .font("Segoe UI")
                .fontWeight("700")
                .fontSize(d => d.size)
                .spiral("archimedean")
                .on("end", draw)
                .start();
        }}
        
        function draw(words) {{
            const container = document.getElementById('container');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            const svg = d3.select("#word-cloud").append("svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
                
            svg.selectAll("text")
                .data(words)
                .enter().append("text")
                .style("font-size", d => d.size + "px")
                .style("font-family", "Segoe UI")
                .style("font-weight", "700")
                .style("fill", (d, i) => colors[i % colors.length])
                .attr("text-anchor", "middle")
                .attr("transform", d => "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")")
                .text(d => d.text)
                .style("cursor", "pointer")
                .on("mouseover", function(event, d) {{
                    d3.select(this).style("opacity", 0.7);
                    showTooltip(event, d.text, d.rawCount);
                }})
                .on("mousemove", moveTooltip)
                .on("mouseout", function() {{
                    d3.select(this).style("opacity", 1);
                    hideTooltip();
                }})
                .on("click", function(event, d) {{
                    excludeWord(d.text);
                }});
        }}
        
        const tooltip = document.getElementById('tooltip');
        function showTooltip(e, text, count) {{
            tooltip.style.opacity = 1;
            tooltip.innerHTML = `<strong>${{text}}</strong>: ${{count}} kez`;
            moveTooltip(e);
        }}
        function moveTooltip(e) {{
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        }}
        function hideTooltip() {{
            tooltip.style.opacity = 0;
        }}
        
        function excludeWord(word) {{
            excluded.add(word);
            updateExcludedList();
            regenerate();
        }}
        
        function restoreWord(word) {{
            excluded.delete(word);
            updateExcludedList();
            regenerate();
        }}
        
        function updateExcludedList() {{
            const listEl = document.getElementById('excludedList');
            const container = document.getElementById('excludedWords');
            
            if (excluded.size === 0) {{
                listEl.style.display = "none";
                return;
            }}
            
            listEl.style.display = "block";
            container.innerHTML = "";
            Array.from(excluded).forEach(word => {{
                const span = document.createElement('span');
                span.className = 'restore-word';
                span.textContent = word + " ✕";
                span.onclick = () => restoreWord(word);
                container.appendChild(span);
            }});
        }}
        
        function exportImage() {{
            const svgElement = document.querySelector("#word-cloud svg");
            if (!svgElement) return;
            
            const svgData = new XMLSerializer().serializeToString(svgElement);
            const canvas = document.createElement("canvas");
            const svgSize = svgElement.getBoundingClientRect();
            
            canvas.width = svgSize.width * 2;
            canvas.height = svgSize.height * 2;
            const ctx = canvas.getContext("2d");
            ctx.scale(2, 2);

            const img = new Image();
            const svgBlob = new Blob([svgData], {{type: "image/svg+xml;charset=utf-8"}});
            const url = URL.createObjectURL(svgBlob);

            img.onload = function() {{
                ctx.fillStyle = "white";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                URL.revokeObjectURL(url);
                
                const pngUrl = canvas.toDataURL("image/png");
                const downloadLink = document.createElement("a");
                downloadLink.href = pngUrl;
                downloadLink.download = "lexischolar_wordcloud.png";
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
            }};
            img.src = url;
        }}
        
        let resizeTimer;
        window.addEventListener('resize', () => {{
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(regenerate, 200);
        }});
    </script>
</body>
</html>
'''
    
    if output_path:
        file_path = Path(output_path)
    else:
        file_path = Path(tempfile.gettempdir()) / "lexischolar_wordcloud_pro.html"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return str(file_path)
