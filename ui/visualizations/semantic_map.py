"""
Semantic map visualization using Plotly/ECharts for UMAP clusters.
"""
from typing import Dict, Any, List
import json
import logging
from .core_utils import build_html_template, save_html

logger = logging.getLogger(__name__)

def generate_semantic_map_html(cluster_data: Dict[str, Any]) -> str:
    """
    Generate an HTML string containing an interactive scatter plot of semantic clusters.
    
    Args:
        cluster_data: Dictionary containing 'points' list. 
                      Each point has: id, text, code, doc, x, y, cluster.
    """
    if not cluster_data or "points" not in cluster_data or not cluster_data["points"]:
        html = """
        <html><head><meta charset="utf-8"></head>
        <body style="font-family:sans-serif; text-align:center; padding:50px; color:#64748B;">
        <h2>Anlamsal Harita Oluşturulamadı</h2>
        <p>Görselleştirilecek yeterli veri bulunamadı. Lütfen analiz için en az birkaç segment kodlayın.</p>
        </body></html>
        """
        return save_html(html, "empty_map")

    points = cluster_data["points"]
    points_json = json.dumps(points, ensure_ascii=False)

    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    echarts_path = os.path.join(base_dir, "resources", "js", "echarts.min.js")
    echarts_js = ""
    if os.path.exists(echarts_path):
        with open(echarts_path, "r", encoding="utf-8") as f:
            echarts_js = f.read()

    head_content = f"""
    <!-- Local ECharts (Offline support completely bypassing WebEngine CORS) -->
    <script>{echarts_js}</script>

    <style>
        #main {{ width: 100%; height: 100vh; margin: 0; padding: 0; }}
        .echarts-tooltip {{ 
            max-width: 400px; white-space: normal !important; 
            font-family: 'Inter', sans-serif !important; font-size: 13px; line-height: 1.5;
        }}
        .tooltip-tag {{ 
            display: inline-block; padding: 2px 6px; border-radius: 4px; 
            font-size: 11px; font-weight: 600; margin-bottom: 6px; 
            background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0;
        }}
    </style>
    """

    body_content = f"""
    <div id="main"></div>
    <script>
        function initChart() {{
            if (typeof echarts === 'undefined') {{
                document.getElementById('main').innerHTML = `
                    <div style="text-align:center; padding:50px; color:#64748B;">
                        <h2>📊 Görselleştirme Kütüphanesi Yüklenemedi</h2>
                        <p>ECharts kütüphanesi (CDN) yüklenemedi. Lütfen internet bağlantınızı kontrol edin.</p>
                        <button onclick="location.reload()" style="padding:10px 20px; border-radius:6px; background:#4F46E5; color:white; border:none; cursor:pointer;">Tekrar Dene</button>
                    </div>
                `;
                return;
            }}

            var chartDom = document.getElementById('main');
            var myChart = echarts.init(chartDom);
            var rawData = {points_json};
            
            // Group points by Code for the legend/series
            var seriesData = {{}};
            rawData.forEach(function(pt) {{
                if (!seriesData[pt.code]) {{ seriesData[pt.code] = []; }}
                seriesData[pt.code].push([pt.x, pt.y, pt.text, pt.doc, pt.cluster]);
            }});

            var series = [];
            var colorPalette = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6'];
            var colorIdx = 0;

            Object.keys(seriesData).forEach(function(codeName) {{
                series.push({{
                    name: codeName,
                    type: 'scatter',
                    symbolSize: function (data) {{ return 14; }},
                    data: seriesData[codeName],
                    itemStyle: {{ 
                        color: colorPalette[colorIdx % colorPalette.length],
                        opacity: 0.8,
                        borderColor: '#fff',
                        borderWidth: 1
                    }},
                    emphasis: {{
                        focus: 'series',
                        itemStyle: {{ shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)', opacity: 1 }}
                    }}
                }});
                colorIdx++;
            }});

            var option = {{
                title: {{
                    text: 'Segment Anlamsal Kümeleme Haritası',
                    subtext: 'BGE-M3 + UMAP Algoritması Modeli',
                    left: 'center',
                    top: 10,
                    textStyle: {{ fontFamily: 'Inter', fontSize: 18, color: '#1E293B' }},
                    subtextStyle: {{ fontFamily: 'Inter', fontSize: 13, color: '#64748B' }}
                }},
                tooltip: {{
                    trigger: 'item',
                    className: 'echarts-tooltip',
                    formatter: function (params) {{
                        var x = params.value[0];
                        var y = params.value[1];
                        var text = params.value[2];
                        var doc = params.value[3];
                        var clus = params.value[4];
                        var code = params.seriesName;
                        
                        return `
                            <div class="tooltip-tag">${{code}}</div>
                            <div class="tooltip-tag" style="background:#E0F2FE; color:#0284C7; border-color:#BAE6FD;">📄 ${{doc}}</div>
                            <div class="tooltip-tag" style="background:#FEF3C7; color:#D97706; border-color:#FDE68A;">Küme: ${{clus}}</div>
                            <div style="color: #334155; margin-top: 4px;">"${{text}}"</div>
                        `;
                    }}
                }},
                legend: {{
                    type: 'scroll',
                    orient: 'vertical',
                    right: 10,
                    top: 60,
                    bottom: 20,
                    textStyle: {{ fontFamily: 'Inter', fontSize: 12, color: '#475569' }}
                }},
                grid: {{ left: '5%', right: '15%', bottom: '5%', top: '15%', containLabel: true }},
                xAxis: {{ type: 'value', scale: true, splitLine: {{ show: false }}, axisLabel: {{ show: false }}, axisTick: {{ show: false }}, axisLine: {{ show: false }} }},
                yAxis: {{ type: 'value', scale: true, splitLine: {{ show: false }}, axisLabel: {{ show: false }}, axisTick: {{ show: false }}, axisLine: {{ show: false }} }},
                series: series,
                dataZoom: [
                    {{ type: 'inside', xAxisIndex: [0], yAxisIndex: [0] }},
                    {{ type: 'slider', xAxisIndex: [0], show: false }},
                    {{ type: 'slider', yAxisIndex: [0], show: false }}
                ]
            }};

            myChart.setOption(option);
            
            window.addEventListener('resize', function() {{
                myChart.resize();
            }});
        }}

        // Initialize when window clears
        window.onload = initChart;
    </script>
    """

    html = build_html_template(
        content=body_content,
        title="Anlamsal Harita",
        extra_head=head_content
    )
    return save_html(html, "semantic_map")
