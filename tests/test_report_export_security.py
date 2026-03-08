import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from export.report_exporter import ReportExporter
from export.exporters import _sanitize_spreadsheet_cell


def test_save_report_passes_color_for_csv_xlsx(monkeypatch, tmp_path):
    exporter = ReportExporter()
    exporter._last_code = {"name": "Kod1", "color": "#123ABC"}
    exporter._last_segments = [{"segment_text": "A"}]
    calls = {}

    def fake_csv(path, name, color, segments):
        calls["csv"] = (path, name, color, segments)
        return True

    def fake_xlsx(path, name, color, segments):
        calls["xlsx"] = (path, name, color, segments)
        return True

    monkeypatch.setattr("export.report_exporter.export_to_csv", fake_csv)
    monkeypatch.setattr("export.report_exporter.export_to_xlsx", fake_xlsx)

    assert exporter.save_report(str(tmp_path / "r.csv"), "CSV_CONTENT", "csv") is True
    assert exporter.save_report(str(tmp_path / "r.xlsx"), "XLSX_CONTENT", "xlsx") is True
    assert calls["csv"][2] == "#123ABC"
    assert calls["xlsx"][2] == "#123ABC"


def test_save_report_uses_exporters_for_json_and_markdown(monkeypatch, tmp_path):
    exporter = ReportExporter()
    exporter._last_code = {"name": "Kod2", "color": "#445566"}
    exporter._last_segments = [{"segment_text": "B"}]
    calls = {"json": 0, "md": 0}

    def fake_json(path, name, color, segments):
        calls["json"] += 1
        return True

    def fake_md(path, name, color, segments):
        calls["md"] += 1
        return True

    monkeypatch.setattr("export.report_exporter.export_to_json", fake_json)
    monkeypatch.setattr("export.report_exporter.export_to_markdown", fake_md)

    assert exporter.save_report(str(tmp_path / "r.json"), "JSON_CONTENT", "json") is True
    assert exporter.save_report(str(tmp_path / "r.md"), "MD_CONTENT", "md") is True
    assert calls["json"] == 1
    assert calls["md"] == 1


def test_html_report_escapes_untrusted_text():
    exporter = ReportExporter()
    html = exporter._generate_html_content(
        "<img src=x onerror=1>",
        "#4F46E5",
        [{"document_title": "<script>x</script>", "segment_text": "<b>text</b>", "start_pos": 0, "end_pos": 5}],
    )
    assert "<script>" not in html
    assert "<img src=x onerror=1>" not in html
    assert "&lt;script&gt;x&lt;/script&gt;" in html
    assert "&lt;b&gt;text&lt;/b&gt;" in html


def test_codebook_escapes_name_and_description():
    exporter = ReportExporter()
    html = exporter.generate_codebook(
        [{"name": "<svg onload=1>", "description": "<script>bad()</script>", "color": "#00AA00"}]
    )
    assert "<script>bad()</script>" not in html
    assert "&lt;script&gt;bad()&lt;/script&gt;" in html
    assert "<svg onload=1>" not in html


def test_spreadsheet_formula_injection_sanitized():
    assert _sanitize_spreadsheet_cell("=1+1") == "'=1+1"
    assert _sanitize_spreadsheet_cell("+cmd") == "'+cmd"
    assert _sanitize_spreadsheet_cell("-2+3") == "'-2+3"
    assert _sanitize_spreadsheet_cell("@A1") == "'@A1"
    assert _sanitize_spreadsheet_cell("normal") == "normal"
