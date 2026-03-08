"""
Report Exporter class for LexiScholar.
Class-based interface used by menu_actions.py for code report generation.
"""

from datetime import datetime
import html as html_lib
import re
from .exporters import export_to_docx, export_to_csv, export_to_json, export_to_markdown, export_memos_to_docx, export_to_xlsx


class ReportExporter:
    """
    Class-based interface for report exporting.
    Used by menu_actions.py for code report generation.
    """
    
    def __init__(self):
        self._last_code = {}
        self._last_segments = []

    def _safe_hex_color(self, value: str, fallback: str = "#4F46E5") -> str:
        color = str(value or "").strip()
        if re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", color):
            return color
        return fallback
    
    def generate_code_report(self, code: dict, segments: list, format_type: str = 'txt') -> str:
        """
        Generate report content for a code.
        
        Args:
            code: Code dictionary with 'name' and 'color'
            segments: List of segment dictionaries
            format_type: 'txt', 'html', or 'word'
            
        Returns:
            Generated report content as string (for txt/html) or None (docx handled separately)
        """
        # Store for later use in save_report (needed for Word export)
        self._last_code = code
        self._last_segments = segments
        
        code_name = code.get('name', 'Bilinmeyen')
        code_color = code.get('color', '#4F46E5')
        
        if format_type == 'txt':
            lines = []
            lines.append(f"╔{'═' * 58}╗")
            lines.append(f"║  KOD RAPORU: {code_name.upper():<44}║")
            lines.append(f"╠{'═' * 58}╣")
            lines.append(f"║  Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M'):<48}║")
            lines.append(f"║  Toplam Segment: {len(segments):<40}║")
            lines.append(f"╚{'═' * 58}╝\n")
            
            current_doc = None
            for i, seg in enumerate(segments, 1):
                if seg.get('document_title') != current_doc:
                    current_doc = seg.get('document_title', 'Bilinmeyen')
                    lines.append(f"\n{'─' * 60}")
                    lines.append(f"📄 {current_doc}")
                    lines.append(f"{'─' * 60}\n")
                
                lines.append(f'[{i}] "{seg.get("segment_text", "")}"')
                lines.append(f"    └─ Konum: karakter {seg.get('start_pos', 0)}-{seg.get('end_pos', 0)}\n")
            
            return '\n'.join(lines)
        
        elif format_type == 'html':
            # Return HTML content
            return self._generate_html_content(code_name, code_color, segments)
        
        elif format_type == 'word':
            # For Word, we return a marker - actual generation happens in save_report
            return 'DOCX_CONTENT'
        
        elif format_type == 'csv':
            return 'CSV_CONTENT'
            
        elif format_type == 'xlsx':
            return 'XLSX_CONTENT'
            
        elif format_type == 'json':
            return 'JSON_CONTENT'
            
        elif format_type == 'md':
            return 'MD_CONTENT'
        
        return ''
    
    def _generate_html_content(self, code_name: str, code_color: str, segments: list) -> str:
        """Generate HTML report content."""
        safe_color = self._safe_hex_color(code_color)
        safe_code_name = html_lib.escape(str(code_name))
        parts = [f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Kod Raporu: {safe_code_name}</title>
    <style>
        body {{ font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 40px; background: #f8fafc; }}
        .header {{ text-align: center; padding: 30px; background: white; border-radius: 12px; border-left: 6px solid {safe_color}; margin-bottom: 30px; }}
        h1 {{ color: {safe_color}; }}
        .segment {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid {safe_color}; }}
        .doc-title {{ color: #4f46e5; font-size: 18px; border-bottom: 2px solid #e2e8f0; padding: 10px 0; margin: 30px 0 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏷️ {safe_code_name}</h1>
        <p>Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Toplam: {len(segments)} segment</p>
    </div>
"""]
        current_doc = None
        for i, seg in enumerate(segments, 1):
            doc_title = html_lib.escape(str(seg.get('document_title', 'Bilinmeyen')))
            if doc_title != current_doc:
                current_doc = doc_title
                parts.append(f'    <h2 class="doc-title">📄 {doc_title}</h2>\n')
            
            text = html_lib.escape(str(seg.get('segment_text', '')))
            parts.append(
                f'    <div class="segment"><b>[{i}]</b> "{text}"<br><small>Konum: {seg.get("start_pos", 0)}-{seg.get("end_pos", 0)}</small></div>\n'
            )
        
        parts.append("</body></html>")
        return "".join(parts)
    
    def generate_codebook(self, codes: list) -> str:
        """
        Generate a Codebook (Kod Kitabı) report.
        Lists all codes with their descriptions, colors, and hierarchy.
        Essential for academic validity (audit trail).
        """
        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>LexiScholar - Kod Kitabı (Codebook)</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; background: #f8fafc; color: #334155; }}
        .header {{ text-align: center; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 30px; border-top: 6px solid #4F46E5; }}
        h1 {{ color: #1e293b; margin-bottom: 5px; }}
        .meta {{ color: #64748b; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th {{ background: #f1f5f9; color: #475569; font-weight: 600; text-align: left; padding: 12px 16px; border-bottom: 2px solid #e2e8f0; }}
        td {{ padding: 12px 16px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
        tr:last-child td {{ border-bottom: none; }}
        .color-dot {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        .code-name {{ font-weight: 600; color: #0f172a; }}
        .desc {{ color: #334155; line-height: 1.5; }}
        .no-desc {{ color: #94a3b8; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📘 Proje Kod Kitabı</h1>
        <p class="meta">Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Toplam Kod: {len(codes)}</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th style="width: 30%">Kod Adı</th>
                <th style="width: 15%">Renk</th>
                <th style="width: 55%">Tanım / Açıklama</th>
            </tr>
        </thead>
        <tbody>
"""
        # Sort codes by name or hierarchy? Flat list for now.
        # Ideally we should show hierarchy indentation.
        # Assuming codes list is basic dicts.
        
        for code in codes:
            color = self._safe_hex_color(code.get('color', '#CCCCCC'), "#CCCCCC")
            name = html_lib.escape(str(code.get('name', 'Adsız')))
            desc = html_lib.escape(str(code.get('description', '')))
            
            desc_html = f'<div class="desc">{desc}</div>' if desc else '<span class="no-desc">Tanım girilmemiş.</span>'
            
            html += f"""
            <tr>
                <td><span class="code-name">{name}</span></td>
                <td><span class="color-dot" style="background-color: {color};"></span>{color}</td>
                <td>{desc_html}</td>
            </tr>
            """
            
        html += """
        </tbody>
    </table>
    <p style="margin-top: 30px; text-align: center; color: #94a3b8; font-size: 0.8em;">LexiScholar ile oluşturulmuştur.</p>
</body>
</html>
"""
        return html

    def generate_project_summary(self, project_name: str, stats: dict) -> str:
        """
        Generate a project summary dashboard report HTML.
        """
        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Proje Özeti: {html_lib.escape(str(project_name))}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; background: #f0fdf4; }}
        .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        h1 {{ color: #166534; text-align: center; margin-bottom: 40px; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
        .stat-box {{ background: #dcfce7; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-num {{ font-size: 3em; font-weight: bold; color: #15803d; display: block; }}
        .stat-label {{ color: #166534; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>📊 {html_lib.escape(str(project_name))} - Proje Özeti</h1>
    
    <div class="grid">
        <div class="stat-box">
            <span class="stat-num">{stats.get('doc_count', 0)}</span>
            <span class="stat-label">Belge</span>
        </div>
        <div class="stat-box">
            <span class="stat-num">{stats.get('code_count', 0)}</span>
            <span class="stat-label">Kod</span>
        </div>
        <div class="stat-box">
            <span class="stat-num">{stats.get('segment_count', 0)}</span>
            <span class="stat-label">Kodlu Segment</span>
        </div>
        <div class="stat-box">
            <span class="stat-num">{stats.get('memo_count', 0)}</span>
            <span class="stat-label">Memo (Not)</span>
        </div>
    </div>
    
    <div class="card" style="margin-top: 30px; text-align: center;">
        <p>Rapor Tarihi: <b>{datetime.now().strftime('%d.%m.%Y %H:%M')}</b></p>
        <p>LexiScholar Akademik Analiz Yazılımı</p>
    </div>
</body>
</html>
"""
        return html

    def save_report(self, file_path: str, content: str, format_type: str) -> bool:
        """
        Save the report to a file.
        """
        try:
            if format_type == 'word':
                # Use stored code and segments data
                code = self._last_code
                segments = self._last_segments
                
                # Check if we have data, otherwise maybe it's a generic word report request?
                # For now assume Code Report flow.
                return export_to_docx(
                    file_path,
                    code.get('name', 'Kod Raporu'),
                    code.get('color', '#4F46E5'),
                    segments
                )
            elif format_type == 'csv':
                code = self._last_code
                segments = self._last_segments
                return export_to_csv(
                    file_path,
                    code.get('name', 'Kod Raporu'),
                    code.get('color', '#4F46E5'),
                    segments
                )
            elif format_type == 'xlsx':
                code = self._last_code
                segments = self._last_segments
                return export_to_xlsx(
                    file_path,
                    code.get('name', 'Kod Raporu'),
                    code.get('color', '#4F46E5'),
                    segments
                )
            elif format_type == 'json':
                code = self._last_code
                segments = self._last_segments
                return export_to_json(
                    file_path,
                    code.get('name', 'Kod Raporu'),
                    code.get('color', '#4F46E5'),
                    segments
                )
            elif format_type == 'md':
                code = self._last_code
                segments = self._last_segments
                return export_to_markdown(
                    file_path,
                    code.get('name', 'Kod Raporu'),
                    code.get('color', '#4F46E5'),
                    segments
                )
            
            # Default text/html/md
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def save_memo_report(self, file_path: str, memos: list, format_type: str) -> bool:
        """Export all project memos."""
        try:
            if format_type == 'word':
                return export_memos_to_docx(file_path, memos)
            else:
                # Basic text export for memos
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"PROJE MEMO RAPORU\n{'='*20}\n\n")
                    for m in memos:
                        f.write(f"[{m.get('doc_title', 'Genel')}] {m.get('title', 'Not')}\n")
                        f.write(f"{m.get('content')}\n")
                        f.write(f"{'-'*40}\n\n")
                return True
        except Exception as e:
            print(f"Memo save error: {e}")
            return False

