"""
Crosstab Visualization for LexiScholar.
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
from .common import _get_js_content

def generate_crosstab_html(codes: list, groups: list, matrix: list, output_path: str = None) -> str:
    """
    Generate an interactive HTML/D3.js visualization for Crosstab matrix.
    """
    # Prepare data for JS
    js_data = []
    max_val = 0
    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if val > 0:
                js_data.append({"row": r, "col": c, "value": val})
                if val > max_val:
                    max_val = val

    # D3.js library content
    d3_js = _get_js_content("d3.min.js")
    
    # Fallback to CDN if local files missing
    scripts = ""
    if d3_js:
        scripts += f"<script>{d3_js}</script>"
    else:
        scripts += '<script src="https://d3js.org/d3.v7.min.js"></script>'

    html_content = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LexiScholar - Çapraz Tablo Analizi</title>
    {scripts}
    <style>
        body {{
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            overflow: hidden;
            background-color: #f8fafc;
            color: #1e293b;
        }}
        #container {{
            width: 100vw;
            height: 100vh;
        }}
        .grid-line {{ stroke: #e2e8f0; stroke-width: 1px; stroke-dasharray: 2,2; }}
        .header-bg {{ fill: #f1f5f9; }}
        .col-label {{ font-size: 11px; fill: #64748b; font-weight: 600; cursor: default; }}
        .row-label {{ font-size: 12px; fill: #334155; font-weight: 500; cursor: default; }}
        .row-label.parent {{ font-weight: 700; fill: #0f172a; }}
        .cell-hover {{ fill: #f1f5f9; opacity: 0; transition: opacity 0.2s; pointer-events: none; }}
        
        #tooltip {{
            position: fixed;
            padding: 12px;
            background: rgba(15, 23, 42, 0.95);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            pointer-events: none;
            opacity: 0;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            font-size: 12px;
            z-index: 1000;
            backdrop-filter: blur(4px);
        }}
        .count-badge {{
            display: inline-block;
            background: #6366f1;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        }}
    </style>
</head>
<body>
    <div id="tooltip"></div>
    <div id="container"></div>

    <script>
        const codes = {json.dumps(codes)};
        const groups = {json.dumps(groups)};
        const data = {json.dumps(js_data)};
        const maxVal = {max_val};

        const rowHeight = 45;
        const colWidth = 100;
        
        // Dynamic margin based on code names
        const maxCodeLength = Math.max(...codes.map(c => c.name.length));
        const leftMargin = Math.min(Math.max(200, maxCodeLength * 8), 400);
        const margin = {{top: 150, right: 80, bottom: 50, left: leftMargin}};
        
        const container = document.getElementById('container');
        let width = container.clientWidth;
        let height = container.clientHeight;
        
        const totalWidth = groups.length * colWidth + margin.left + margin.right;
        const totalHeight = codes.length * rowHeight + margin.top + margin.bottom;

        const zoom = d3.zoom()
            .scaleExtent([0.2, 5])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        const svg = d3.select("#container").append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(zoom)
            .style("cursor", "move");
            
        const g = svg.append("g");
            
        // Scales
        const x = d3.scaleBand()
            .range([margin.left, groups.length * colWidth + margin.left])
            .domain(groups)
            .padding(0);

        const y = d3.scaleBand()
            .range([margin.top, codes.length * rowHeight + margin.top])
            .domain(codes.map((d, i) => i))
            .padding(0);

        // Helper: Get code level (hierarchy depth)
        function getCodeLevel(codeId, allCodes) {{
            let level = 0;
            let current = allCodes.find(c => c.id === codeId);
            while (current && current.parent_id) {{
                level++;
                current = allCodes.find(c => c.id === current.parent_id);
            }}
            return level;
        }}

        // Grid Lines & Row Background Hovers
        g.selectAll(".row-hover")
            .data(codes)
            .enter()
            .append("rect")
            .attr("class", "cell-hover")
            .attr("x", margin.left)
            .attr("y", (d, i) => y(i))
            .attr("width", groups.length * colWidth)
            .attr("height", rowHeight)
            .attr("id", (d, i) => `row-hover-${{i}}`);

        // Vertical Grid Lines
        g.selectAll(".v-line")
            .data(groups)
            .enter()
            .append("line")
            .attr("class", "grid-line")
            .attr("x1", d => x(d) + colWidth)
            .attr("y1", margin.top - 20)
            .attr("x2", d => x(d) + colWidth)
            .attr("y2", margin.top + codes.length * rowHeight);

        // Horizontal Grid Lines
        g.selectAll(".h-line")
            .data(codes)
            .enter()
            .append("line")
            .attr("class", "grid-line")
            .attr("x1", margin.left - 20)
            .attr("y1", (d, i) => y(i) + rowHeight)
            .attr("x2", margin.left + groups.length * colWidth)
            .attr("y2", (d, i) => y(i) + rowHeight);

        // Labels
        g.append("g")
            .selectAll(".col-label")
            .data(groups)
            .enter()
            .append("text")
            .attr("class", "col-label")
            .attr("transform", d => `translate(${{x(d) + colWidth/2}}, ${{margin.top - 10}}) rotate(-45)`)
            .text(d => d.length > 25 ? d.substring(0, 22) + "..." : d);

        g.append("g")
            .selectAll(".row-label")
            .data(codes)
            .enter()
            .append("text")
            .attr("class", d => "row-label " + (codes.some(c => c.parent_id === d.id) ? "parent" : ""))
            .attr("x", d => margin.left - 20 - (getCodeLevel(d.id, codes) * 20))
            .attr("y", (d, i) => y(i) + rowHeight/2)
            .attr("dy", ".35em")
            .attr("text-anchor", "end")
            .text(d => {{
                const maxLen = 35;
                return d.name.length > maxLen ? d.name.substring(0, maxLen-3) + "..." : d.name;
            }});

        // Cells
        const tooltip = d3.select("#tooltip");
        const radiusScale = d3.scaleSqrt()
            .domain([0, maxVal])
            .range([2, Math.min(rowHeight, colWidth)/2 * 0.85]);

        g.selectAll(".bubble")
            .data(data)
            .enter()
            .append("circle")
            .attr("class", "bubble")
            .attr("cx", d => x(groups[d.col]) + colWidth/2)
            .attr("cy", d => y(d.row) + rowHeight/2)
            .attr("r", d => radiusScale(d.value))
            .style("fill", d => codes[d.row].color || "#6366f1")
            .style("fill-opacity", 0.7)
            .style("stroke", d => codes[d.row].color || "#6366f1")
            .style("stroke-width", "2px")
            .on("mouseover", function(event, d) {{
                d3.select(this).style("fill-opacity", 1).attr("r", radiusScale(d.value) + 2);
                d3.select(`#row-hover-${{d.row}}`).style("opacity", 1);
                
                tooltip.style("opacity", 1)
                    .html(`
                        <div style="font-weight:700; border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:6px; margin-bottom:6px; font-size:13px">${{codes[d.row].name}}</div>
                        <div style="color:#cbd5e1; margin-bottom:4px">Grup: <span style="color:white; font-weight:600">${{groups[d.col]}}</span></div>
                        <div style="margin-top:8px"><span class="count-badge">${{d.value}}</span> segment</div>
                    `)
                    .style("left", (event.clientX + 20) + "px")
                    .style("top", (event.clientY + 20) + "px");
            }})
            .on("mousemove", (event) => {{
                tooltip.style("left", (event.clientX + 20) + "px")
                       .style("top", (event.clientY + 20) + "px");
            }})
            .on("mouseout", function(event, d) {{
                d3.select(this).style("fill-opacity", 0.7).attr("r", radiusScale(d.value));
                d3.select(`#row-hover-${{d.row}}`).style("opacity", 0);
                tooltip.style("opacity", 0);
            }});
            
        // Window Resize
        window.addEventListener('resize', () => {{
            width = container.clientWidth;
            height = container.clientHeight;
            svg.attr("width", width).attr("height", height);
        }});

        // JS API
        window.fitToScreen = function() {{
            const scaleX = (width - 40) / totalWidth;
            const scaleY = (height - 40) / totalHeight;
            let scale = Math.min(scaleX, scaleY, 1.2);
            if (scale < 0.2) scale = 0.2;
            
            const transform = d3.zoomIdentity
                .translate((width - totalWidth * scale) / 2, (height - totalHeight * scale) / 2)
                .scale(scale);
            
            svg.transition().duration(1000).ease(d3.easeCubicInOut).call(zoom.transform, transform);
        }};

        window.exportAsImage = function() {{
            const svgElement = document.querySelector("#container svg");
            const serializer = new XMLSerializer();
            let source = serializer.serializeToString(svgElement);
            
            if(!source.match(/^<svg[^>]+xmlns="http:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)){{
                source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
            }}
            if(!source.match(/^<svg[^>]+xmlns:xlink="http:\\/\\/www\\.w3\\.org\\/1999\\/xlink"/)){{
                source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
            }}

            const canvas = document.createElement("canvas");
            canvas.width = totalWidth * 2;
            canvas.height = totalHeight * 2;
            const ctx = canvas.getContext("2d");
            
            const img = new Image();
            const svgBlob = new Blob([source], {{type: "image/svg+xml;charset=utf-8"}});
            const url = URL.createObjectURL(svgBlob);
            
            img.onload = () => {{
                ctx.fillStyle = "white";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.scale(2, 2);
                ctx.drawImage(img, 0, 0);
                const a = document.createElement("a");
                a.download = "lexischolar_crosstab_" + new Date().getTime() + ".png";
                a.href = canvas.toDataURL("image/png");
                a.click();
                URL.revokeObjectURL(url);
            }};
            img.src = url;
        }};

        // Initial fit
        setTimeout(window.fitToScreen, 150);

    </script>
</body>
</html>
'''
    
    if output_path:
        file_path = Path(output_path)
    else:
        file_path = Path(tempfile.gettempdir()) / "lexischolar_crosstab.html"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return str(file_path)
