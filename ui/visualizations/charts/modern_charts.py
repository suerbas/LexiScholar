"""
Modern HTML Chart Generator for LexiScholar.
Uses ApexCharts to replicate the React/Recharts aesthetic.
"""

import json
from visualizations.common import save_html

def generate_modern_chart_html(data, chart_type="bar", options=None):
    """
    Generate an interactive HTML chart using ApexCharts.
    data: List of dicts with {'name', 'value', 'color'}
    chart_type: 'bar', 'pie', 'donut'
    options: dict for additional settings (horizontal, show_labels, etc.)
    """
    if options is None:
        options = {}
    
    # Extract data for ApexCharts
    labels = [item['name'] for item in data]
    values = [item['value'] for item in data]
    # Use provided colors or the Recharts palette from the example
    recharts_palette = ['#1D4ED8', '#047857', '#B45309', '#6D28D9', '#BE123C']
    colors = [item.get('color') or recharts_palette[i % len(recharts_palette)] for i, item in enumerate(data)]
    
    is_horizontal = options.get('horizontal', False)
    show_labels = options.get('show_labels', True)
    show_legend = options.get('show_legend', True)
    title = options.get('title', "")
    
    # ApexCharts Configuration
    chart_config = {
        "chart": {
            "type": "bar" if chart_type == "bar" else "pie",
            "toolbar": {"show": False},
            "height": '100%',
            "width": '100%',
            "sparkline": {"enabled": False},
            "animations": {
                "enabled": True,
                "easing": 'easeinout',
                "speed": 800
            },
            "fontFamily": 'Inter, Segoe UI, sans-serif',
            "background": 'transparent'
        },
        "colors": colors,
        "series": [],
        "labels": labels,
        "title": {
            "text": title,
            "align": 'center',
            "style": {"fontSize": '16px', "fontWeight": '700', "color": '#1E293B'}
        },
        "tooltip": {
            "theme": 'light',
            "style": {"fontSize": '12px'}
        },
        "legend": {
            "show": show_legend,
            "position": 'bottom',
            "fontSize": '12px',
            "offsetY": 8
        }
    }
    
    if chart_type == "bar":
        chart_config["series"] = [{"name": "Frekans", "data": values}]
        chart_config["plotOptions"] = {
            "bar": {
                "horizontal": is_horizontal,
                "borderRadius": 4,
                "distributed": True, # Each bar gets its own color from the palette
                "dataLabels": {"position": 'top' if not is_horizontal else 'right'}
            }
        }
        chart_config["dataLabels"] = {
            "enabled": show_labels,
            "style": {"fontSize": '11px', "colors": ['#475569']},
            "offsetY": -20 if not is_horizontal else 0,
            "offsetX": 0 if not is_horizontal else 5
        }
        chart_config["xaxis"] = {
            "categories": labels,
            "labels": {"style": {"fontSize": '12px', "colors": '#64748B'}}
        }
        chart_config["yaxis"] = {
            "labels": {"style": {"fontSize": '12px', "colors": '#64748B'}}
        }
        chart_config["grid"] = {
            "borderColor": '#E2E8F0',
            "strokeDashArray": 4
        }
    else:
        # Pie / Donut
        chart_config["series"] = values
        chart_config["chart"]["type"] = "donut" if chart_type == "donut" else "pie"
        chart_config["plotOptions"] = {
            "pie": {
                "donut": {
                    "size": '65%',
                    "labels": {
                        "show": chart_type == "donut",
                        "total": {
                            "show": True,
                            "label": 'Toplam',
                            "formatter": "function(w) { return w.globals.seriesTotals.reduce((a, b) => a + b, 0) }"
                        }
                    }
                }
            }
        }
        chart_config["dataLabels"] = {
            "enabled": show_labels,
            "formatter": "function(val, opts) { return opts.w.globals.labels[opts.seriesIndex] + ': ' + val.toFixed(1) + '%' }"
        }

    # Read local ApexCharts
    from visualizations.common import _get_js_content
    apex_js = _get_js_content("apexcharts.min.js")
    if apex_js:
        script_tag = f"<script>{apex_js}</script>"
    else:
        script_tag = '<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>'

    # HTML Template
    html = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        {script_tag}
    <style>
        body, html {{ 
            margin: 0; padding: 0; width: 100%; height: 100%; 
            overflow: hidden; background-color: white; 
            font-family: 'Inter', 'Segoe UI', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        #chart {{ 
            width: 100%; 
            height: 100%; 
            max-width: 100%;
            max-height: 100%;
        }}
        /* Hide ApexCharts scrollbars */
        .apexcharts-canvas {{
            overflow: hidden;
        }}
    </style>
    </head>
    <body>
        <div id="chart"></div>
        <script>
            var options = {json.dumps(chart_config)};
            
            // Fix function string for total label formatter in donut
            if (options.plotOptions && options.plotOptions.pie && options.plotOptions.pie.donut) {{
                options.plotOptions.pie.donut.labels.total.formatter = function(w) {{
                    return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                }};
            }}
            // Fix dataLabels formatter
            if (options.dataLabels && options.dataLabels.formatter === "function(val, opts) {{ return opts.w.globals.labels[opts.seriesIndex] + ': ' + val.toFixed(1) + '%' }}") {{
                options.dataLabels.formatter = function(val, opts) {{
                    return opts.w.globals.labels[opts.seriesIndex] + ': ' + val.toFixed(1) + '%';
                }};
            }}

            var chart = new ApexCharts(document.querySelector("#chart"), options);
            chart.render();
            
            // Export helper for PyQt
            window.exportImage = function() {{
                chart.dataURI().then(({{ imgURI }}) => {{
                    console.log("CHART_EXPORT_READY:" + imgURI);
                }});
            }};
        </script>
    </body>
    </html>
    """
    
    return save_html(html, "modern_chart")
