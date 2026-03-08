"""
Co-occurrence Graph Visualization for LexiScholar.
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict
from .common import _get_js_content

def generate_cooccurrence_graph(codes: List[Dict], matrix: List[List[int]], 
                                 output_path: str = None) -> str:
    """
    Generate an interactive HTML graph showing code co-occurrence.
    """
    
    # Prepare nodes and edges for D3.js
    nodes = []
    for i, code in enumerate(codes):
        nodes.append({
            "id": i,
            "name": code['name'],
            "color": code['color'],
            "size": sum(matrix[i]) if i < len(matrix) else 1
        })
    
    edges = []
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            if i < len(matrix) and j < len(matrix[i]):
                weight = matrix[i][j]
                if weight > 0:
                    edges.append({
                        "source": i,
                        "target": j,
                        "weight": weight
                    })
    
    # D3.js library content
    d3_js = _get_js_content("d3.min.js")
    
    # Fallback to CDN if local files missing
    scripts = ""
    if d3_js:
        scripts += f"<script>{d3_js}</script>"
    else:
        scripts += '<script src="https://d3js.org/d3.v7.min.js"></script>'

    # Generate HTML
    html_content = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LexiScholar - Kod İlişki Grafiği</title>
    {scripts}
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body, html {{
            width: 100%;
            height: 100%;
            overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #FFFFFF;
        }}
        
        #graph {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
        }}

        .node {{ cursor: pointer; }}
        .node circle {{
            stroke: white;
            stroke-width: 2px;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
            transition: all 0.3s ease;
        }}
        .node circle:hover {{
            stroke-width: 4px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
            stroke: #3B82F6;
        }}
        .node text {{
            font-size: 11px;
            font-weight: 600;
            fill: #1E293B;
            pointer-events: none;
            text-shadow: 
                -2px -2px 0 #fff,  
                 2px -2px 0 #fff,
                -2px  2px 0 #fff,
                 2px  2px 0 #fff;
        }}
        
        .labels-hidden .node text {{ display: none; }}

        .link {{
            stroke: #94A3B8;
            stroke-opacity: 0.3;
            transition: all 0.3s ease;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(15, 23, 42, 0.95);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 11px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 1000;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }}

    </style>
</head>
<body>
    <div id="graph"></div>
    <div class="tooltip" id="tooltip"></div>

    <script>
        const nodes = {json.dumps(nodes)};
        const links = {json.dumps(edges)};
        
        const container = document.getElementById('graph');
        let width = container.clientWidth;
        let height = container.clientHeight;
        
        const handleZoom = d3.zoom()
            .scaleExtent([0.05, 10])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .call(handleZoom)
            .style("cursor", "move");
            
        const g = svg.append("g");
        
        // Simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('x', d3.forceX(width / 2).strength(0.04)) // Pull orphan nodes to center
            .force('y', d3.forceY(height / 2).strength(0.04))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => Math.max(35, Math.min(d.size * 5 + 20, 65))));
            
        window.addEventListener('resize', () => {{
            width = container.clientWidth;
            height = container.clientHeight;
            d3.select("svg").attr("width", width).attr("height", height);
            simulation.force("center", d3.forceCenter(width / 2, height / 2));
            simulation.force("x", d3.forceX(width / 2));
            simulation.force("y", d3.forceY(height / 2));
            simulation.alpha(0.3).restart();
        }});
        
        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke-width', d => Math.min(d.weight * 2, 8));
        
        const node = g.append('g')
            .selectAll('.node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        node.append('circle')
            .attr('r', d => Math.max(18, Math.min(d.size * 5 + 15, 45)))
            .attr('fill', d => d.color);
        
        node.append('text')
            .attr('dy', d => Math.max(18, Math.min(d.size * 5 + 15, 45)) + 15)
            .attr('text-anchor', 'middle')
            .text(d => d.name);
        
        const tooltip = d3.select("#tooltip");
        
        node.on('mouseover', function(event, d) {{
            tooltip.style("opacity", 1);
            tooltip.html(`<strong>${{d.name}}</strong><br>${{d.size}} bağlantı`);
            tooltip.style("left", (event.clientX + 15) + 'px').style("top", (event.clientY - 15) + 'px');
        }})
        .on('mousemove', (event) => {{
             tooltip.style("left", (event.clientX + 15) + 'px').style("top", (event.clientY - 15) + 'px');
        }})
        .on('mouseout', () => tooltip.style("opacity", 0));
        
        link.on('mouseover', function(event, d) {{
            tooltip.style("opacity", 1);
            tooltip.html(`${{nodes[d.source.id || d.source].name}} ↔ ${{nodes[d.target.id || d.target].name}}<br>${{d.weight}} kez birlikte`);
            tooltip.style("left", (event.clientX + 15) + 'px').style("top", (event.clientY - 15) + 'px');
        }})
        .on('mouseout', () => tooltip.style("opacity", 0));
        
        simulation.on('tick', () => {{
            link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
            node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
        }});

        // Initial automatic fit
        setTimeout(() => {{
            fitToScreen();
        }}, 500);

        // --- API ---
        function restartSimulation() {{
            simulation.alpha(1).restart();
        }}

        function toggleLabels(show) {{
            if (show) container.classList.remove('labels-hidden');
            else container.classList.add('labels-hidden');
        }}

        function fitToScreen() {{
            const bounds = g.node().getBBox();
            if (!bounds || bounds.width === 0) return;
            
            const fullWidth = container.clientWidth;
            const fullHeight = container.clientHeight;
            
            const midX = bounds.x + bounds.width / 2;
            const midY = bounds.y + bounds.height / 2;
            
            const padding = 40;
            const scale = 0.85 / Math.max(bounds.width / fullWidth, bounds.height / fullHeight);
            
            svg.transition().duration(750).call(
                handleZoom.transform,
                d3.zoomIdentity
                    .translate(fullWidth / 2, fullHeight / 2)
                    .scale(Math.min(scale, 2))
                    .translate(-midX, -midY)
            );
        }}

        window.exportAsImage = function() {{
            const svgElement = document.querySelector("#container svg");
            if (!svgElement) return;
            
            const svgData = new XMLSerializer().serializeToString(svgElement);
            const canvas = document.createElement("canvas");
            canvas.width = width * 2;
            canvas.height = height * 2;
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
                downloadLink.download = "lexischolar_graph.png";
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
            }};
            img.src = url;
        }}

        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}
        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}
        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
    </script>
</body>
</html>
'''
    
    if output_path:
        file_path = Path(output_path)
    else:
        file_path = Path(tempfile.gettempdir()) / "lexischolar_graph.html"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return str(file_path)
