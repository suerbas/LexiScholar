"""
Code Matrix Visualization for LexiScholar.
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict
from .common import _get_js_content

def generate_code_matrix_html(codes: List[Dict], documents: List[Dict], 
                               matrix: List[List[int]], output_path: str = None) -> str:
    """
    Generate an interactive HTML code matrix (heatmap) visualization.
    """
    
    # Prepare data for JS
    data_points = []
    max_val = 0
    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if val > 0:
                data_points.append({"row": r, "col": c, "value": val})
                if val > max_val: 
                    max_val = val
                    
    # Format codes and docs for JS
    js_codes = [{"id": c['id'], "name": c['name'], "color": c['color'], "parent_id": c.get('parent_id')} for c in codes]
    js_docs = [{"id": d['id'], "title": d['title']} for d in documents]
    
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
    <title>LexiScholar - Kod Matris Tarayıcısı</title>
    {scripts}
    <style>
        * {{
            box-sizing: border-box;
        }}
        body, html {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
        }}
        
        #container {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
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
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            max-width: 250px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .axis text {{
            font-family: 'Segoe UI';
            font-size: 10px;
            fill: #475569;
        }}
        
        .axis line, .axis path {{
            stroke: #E2E8F0;
        }}

        .grid-line {{ stroke: #e2e8f0; stroke-width: 1px; stroke-dasharray: 2,2; }}
        
        .row-label {{
            font-size: 11px;
            font-weight: 500;
            fill: #334155;
            cursor: pointer;
        }}
        .row-label.parent {{ font-weight: 700; fill: #0f172a; }}
        .row-label:hover {{
            fill: #2563EB;
            font-weight: 700;
        }}
        
        .col-label {{
            cursor: pointer;
        }}
        .col-label:hover {{
            fill: #2563EB;
            font-weight: 700;
        }}

        /* Visualization Modes */
        .circle-mode circle {{ display: block; }}
        .heatmap-mode rect.heatmap-cell {{ display: block; }}
        .circle-mode rect.heatmap-cell {{ display: none; }}
        .heatmap-mode circle {{ display: none; }}

        /* Legend Style */
        .legend {{ font-family: 'Segoe UI', sans-serif; opacity: 1; transition: opacity 0.5s; }}
        .legend-title {{ font-size: 11px; font-weight: bold; fill: #475569; }}
        .legend-label {{ font-size: 10px; fill: #64748B; }}
        .circle-legend {{ display: none; }}
        .heatmap-legend {{ display: none; }}
        .circle-mode .circle-legend {{ display: block; }}
        .heatmap-mode .heatmap-legend {{ display: block; }}
    </style>
</head>
<body class="circle-mode">

    <div id="container"></div>
    <div class="tooltip" id="tooltip"></div>

    <script>
        const codes = {json.dumps(js_codes)};
        const docs = {json.dumps(js_docs)};
        const data = {json.dumps(data_points)};
        const maxVal = {max_val};
        
        const container = document.getElementById('container');
        let width = container.clientWidth;
        let height = container.clientHeight;
        
        const rowHeight = 28;
        const colWidth = 40;
        
        // Dynamic margin based on code names
        const maxCodeLength = codes.length > 0 ? Math.max(...codes.map(c => c.name.length)) : 10;
        const leftMargin = Math.min(Math.max(200, maxCodeLength * 8), 400);
        const margin = {{top: 150, right: 80, bottom: 50, left: leftMargin}};
        
        const totalWidth = margin.left + margin.right + (docs.length * colWidth);
        const totalHeight = margin.top + margin.bottom + (codes.length * rowHeight);
        
        const handleZoom = d3.zoom()
            .scaleExtent([0.1, 5])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        const svg = d3.select("#container").append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(handleZoom)
            .style("cursor", "move");
            
        const g = svg.append("g");
            
        // Background for panning
        g.append("rect")
            .attr("width", totalWidth * 10)
            .attr("height", totalHeight * 10)
            .attr("fill", "transparent")
            .attr("x", -totalWidth * 5)
            .attr("y", -totalHeight * 5);

        const x = d3.scaleBand()
            .range([0, docs.length * colWidth])
            .domain(docs.map(d => d.title))
            .padding(0.05);

        const y = d3.scaleBand()
            .range([0, codes.length * rowHeight])
            .domain(codes.map(d => d.name))
            .padding(0.05);

        // Drawing inside a content group
        const content = g.append("g").attr("transform", `translate(${{margin.left}}, ${{margin.top}})`);

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

        // Horizontal Grid Lines
        content.selectAll(".h-line")
            .data(codes)
            .enter()
            .append("line")
            .attr("class", "grid-line")
            .attr("x1", -20)
            .attr("y1", (d, i) => y(d.name) + y.bandwidth())
            .attr("x2", docs.length * colWidth)
            .attr("y2", (d, i) => y(d.name) + y.bandwidth());

        // Vertical Grid Lines
        content.selectAll(".v-line")
            .data(docs)
            .enter()
            .append("line")
            .attr("class", "grid-line")
            .attr("x1", (d, i) => x(d.title) + x.bandwidth())
            .attr("y1", -20)
            .attr("x2", (d, i) => x(d.title) + x.bandwidth())
            .attr("y2", codes.length * rowHeight);

        content.append("g")
            .style("font-size", "11px")
            .attr("transform", "translate(0,0)")
            .call(d3.axisTop(x).tickSize(0))
            .selectAll("text")
            .attr("transform", "rotate(-45)")
            .style("text-anchor", "start")
            .attr("dx", "10px")
            .attr("dy", "-5px")
            .attr("class", "col-label")
            .text(d => d.length > 15 ? d.substring(0, 12) + "..." : d);

        content.append("g")
            .style("font-size", "11px")
            .call(d3.axisLeft(y).tickSize(0))
            .selectAll("text")
            .attr("class", (d, i) => "row-label " + (codes.some(c => c.parent_id === codes[i].id) ? "parent" : ""))
            .attr("dx", d => -(getCodeLevel(codes.find(c => c.name === d).id, codes) * 15))
            .text(d => {{
                const maxLen = 30;
                return d.length > maxLen ? d.substring(0, maxLen-3) + "..." : d;
            }});

        // Cell background / Heatmap mode
        const colorScale = d3.scaleSequential(d3.interpolateYlOrRd).domain([0, maxVal]);

        content.selectAll("rect.heatmap-cell")
            .data(data)
            .enter()
            .append("rect")
            .attr("class", "heatmap-cell")
            .attr("x", d => x(docs[d.col].title))
            .attr("y", d => y(codes[d.row].name))
            .attr("width", x.bandwidth())
            .attr("height", y.bandwidth())
            .attr("fill", d => colorScale(d.value));

        const maxRadius = Math.min(colWidth, rowHeight) / 2 * 0.9;
        const radiusScale = d3.scaleSqrt()
            .domain([0, maxVal])
            .range([2, maxRadius]);
            
        const tooltip = d3.select("#tooltip");

        content.selectAll("circle")
            .data(data)
            .enter()
            .append("circle")
            .attr("cx", d => x(docs[d.col].title) + x.bandwidth()/2)
            .attr("cy", d => y(codes[d.row].name) + y.bandwidth()/2)
            .attr("r", d => radiusScale(d.value))
            .style("fill", d => codes[d.row].color || "#3B82F6")
            .style("opacity", 0.8)
            .style("stroke", "white")
            .style("stroke-width", "1px")
            .on("mouseover", function(event, d) {{
                d3.select(this).style("opacity", 1).style("stroke", "#1E293B").style("stroke-width", "2px");
                tooltip.style("opacity", 1);
                tooltip.html(`
                    <div style="font-weight:700; color:#F8FAFC; margin-bottom:4px">${{codes[d.row].name}}</div>
                    <div style="color:#CBD5E1; font-size:10px">${{docs[d.col].title}}</div>
                    <div style="font-size:13px; margin-top:6px; font-weight:800">Frekans: ${{d.value}}</div>
                `);
                tooltip.style("left", (event.clientX + 15) + "px").style("top", (event.clientY + 15) + "px");
            }})
            .on("mousemove", (event) => {{
                tooltip.style("left", (event.clientX + 15) + "px").style("top", (event.clientY + 15) + "px");
            }})
            .on("mouseout", function() {{
                d3.select(this).style("opacity", 0.8).style("stroke", "white").style("stroke-width", "1px");
                tooltip.style("opacity", 0);
            }});
            
        // --- Legend Creation ---
        const legendArea = svg.append("g")
            .attr("class", "legend")
            .attr("transform", `translate(${{width - 150}}, 20)`);

        // Heatmap Legend
        const heatmapLegend = legendArea.append("g").attr("class", "heatmap-legend");
        heatmapLegend.append("text").attr("class", "legend-title").text("Sıklık Skalası").attr("y", 0);
        
        const gradient = svg.append("defs")
            .append("linearGradient")
            .attr("id", "legend-gradient")
            .attr("x1", "0%").attr("y1", "0%").attr("x2", "100%").attr("y2", "0%");
        
        [0, 0.25, 0.5, 0.75, 1].forEach(t => {{
            gradient.append("stop").attr("offset", (t * 100) + "%").attr("stop-color", d3.interpolateYlOrRd(t));
        }});

        heatmapLegend.append("rect")
            .attr("x", 0).attr("y", 8).attr("width", 120).attr("height", 10)
            .style("fill", "url(#legend-gradient)");

        heatmapLegend.append("text").attr("class", "legend-label").attr("x", 0).attr("y", 30).text("Düşük (1)");
        heatmapLegend.append("text").attr("class", "legend-label").attr("x", 120).attr("y", 30).attr("text-anchor", "end").text(`Yüksek (${{maxVal}})`);

        // Circle Legend
        const circleLegend = legendArea.append("g").attr("class", "circle-legend");
        circleLegend.append("text").attr("class", "legend-title").text("Frekans Dağılımı").attr("y", 0);

        const circleValues = [1, Math.ceil(maxVal / 2), maxVal].filter((v, i, a) => a.indexOf(v) === i);
        circleValues.forEach((v, i) => {{
            const r = radiusScale(v);
            const yPos = 25;
            const xPos = i * 45;
            circleLegend.append("circle").attr("cx", xPos + 10).attr("cy", yPos).attr("r", r).attr("fill", "#64748B").attr("opacity", 0.6);
            circleLegend.append("text").attr("class", "legend-label").attr("x", xPos + 10).attr("y", yPos + 25).attr("text-anchor", "middle").text(v);
        }});

        // Initial setup
        setTimeout(() => {{ window.fitToScreen(); }}, 150);

        window.addEventListener('resize', () => {{
            width = container.clientWidth;
            height = container.clientHeight;
            svg.attr("width", width).attr("height", height);
        }});

        // --- API ---
        window.fitToScreen = function() {{
            // Use the "content" group to get true visual bounds (ignoring the massive background rect in g)
            const bbox = content.node().getBBox();
            if (bbox.width === 0 || bbox.height === 0) return;
            
            // Map the content's tight bounding box to its coordinates within the main zoom group 'g'
            const visualX = margin.left + bbox.x;
            const visualY = margin.top + bbox.y;
            const visualWidth = bbox.width;
            const visualHeight = bbox.height;
            
            // Allow more padding and a dramatic max scale
            const availableWidth = width - 120; 
            const availableHeight = height - 120;
            
            const scaleX = availableWidth / visualWidth;
            const scaleY = availableHeight / visualHeight;
            let scale = Math.min(scaleX, scaleY, 2.5); // increased limit to 2.5
            if (scale < 0.2) scale = 0.2;
            
            // Calculate translation to exactly offset the BBox origin and center the scaled BBox in the viewport
            const xOffset = (width / 2) - ((visualX + visualWidth / 2) * scale);
            const yOffset = (height / 2) - ((visualY + visualHeight / 2) * scale);
            
            const transform = d3.zoomIdentity
                .translate(xOffset, yOffset) 
                .scale(scale);
            
            svg.transition()
                .duration(1000)
                .ease(d3.easeCubicInOut)
                .call(handleZoom.transform, transform);
        }};

        window.zoomReset = function() {{ window.fitToScreen(); }};

        window.toggleHeatmap = function(show) {{
            const bodies = document.getElementsByTagName('body')[0];
            if (show) {{
                bodies.classList.add('heatmap-mode');
                bodies.classList.remove('circle-mode');
            }} else {{
                bodies.classList.add('circle-mode');
                bodies.classList.remove('heatmap-mode');
            }}
        }}
        
        // Default mode
        window.toggleHeatmap(false);

        window.exportAsImage = function() {{
            const svgElement = document.querySelector("#container svg").cloneNode(true);
            const serializer = new XMLSerializer();
            
            // Add Stylesheest into the clone for offline rendering
            const style = document.createElement("style");
            style.innerHTML = document.querySelector("style").innerHTML;
            svgElement.prepend(style);
            
            let source = serializer.serializeToString(svgElement);
            
            // Fix missing namespaces for standalone SVGs
            if(!source.match(/^<svg[^>]+xmlns="http:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)){{
                source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
            }}
            if(!source.match(/^<svg[^>]+xmlns:xlink="http:\\/\\/www\\.w3\\.org\\/1999\\/xlink"/)){{
                source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
            }}

            const canvas = document.createElement("canvas");
            canvas.width = width * 2;
            canvas.height = height * 2;
            const ctx = canvas.getContext("2d");
            ctx.scale(2, 2);

            const img = new Image();
            const svgBlob = new Blob([source], {{type: "image/svg+xml;charset=utf-8"}});
            const url = URL.createObjectURL(svgBlob);

            img.onload = function() {{
                ctx.fillStyle = "white";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                URL.revokeObjectURL(url);
                
                const pngUrl = canvas.toDataURL("image/png");
                
                // Method 1: JS Link (Blocked in some browsers)
                const downloadLink = document.createElement("a");
                downloadLink.href = pngUrl;
                downloadLink.download = "lexischolar_matrix.png";
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                
                // Method 2: Python Signal (For PyQt to handle manually if Method 1 fails)
                console.log("DOWNLOAD_READY:" + pngUrl);
            }};
            img.src = url;
        }}
    </script>
</body>
</html>
'''

    if output_path:
        file_path = Path(output_path)
    else:
        file_path = Path(tempfile.gettempdir()) / "lexischolar_codematrix.html"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return str(file_path)
