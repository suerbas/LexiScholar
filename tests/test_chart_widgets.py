import sys
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
import pytest
from ui.visualizations.charts.chart_widgets import LexiBarChart

# QWebEngineView is unstable in headless/offscreen mode on CI.
IS_OFFSCREEN = os.environ.get("QT_QPA_PLATFORM") == "offscreen"

@pytest.mark.skipif(IS_OFFSCREEN, reason="QWebEngineView crashes in offscreen mode on CI")
def test_bar_chart_respects_vertical_for_long_labels(qapp):
    chart = LexiBarChart(title="Kod Frekansı")
    labels = [
        "Bu oldukça uzun bir etiket ismidir ve dikeyde kesilmelidir",
        "İkinci uzun etiket örneği burada yer alıyor",
    ]
    values = [12, 7]
    colors = ["#4F46E5", "#60A5FA"]
    # Check it doesn't crash
    chart.update_data(labels, values, colors=colors, horizontal=False)
    assert chart.title == "Kod Frekansı"
    assert chart.browser is not None
    chart.deleteLater()


@pytest.mark.skipif(IS_OFFSCREEN, reason="QWebEngineView crashes in offscreen mode on CI")
def test_bar_chart_horizontal_does_not_force_truncation_legend(qapp):
    chart = LexiBarChart(title="Kod Frekansı")
    labels = [
        "Bu oldukça uzun bir etiket ismidir ve yatayda tam görünmelidir",
        "İkinci uzun etiket örneği burada yer alıyor",
    ]
    values = [9, 4]
    colors = ["#4F46E5", "#60A5FA"]
    # Check it doesn't crash with horizontal=True
    chart.update_data(labels, values, colors=colors, horizontal=True)
    assert chart.browser.url() is not None
    chart.deleteLater()


@pytest.mark.skipif(IS_OFFSCREEN, reason="QWebEngineView crashes in offscreen mode on CI")
def test_bar_chart_does_not_crash_on_update(qapp):
    chart = LexiBarChart(title="Kod Frekansı")
    labels = [f"Uzun etiket {i} için örnek metin" for i in range(10)]
    values = [10] * 10
    colors = ["#4F46E5"] * 10
    # Basic smoke test: update_data should run without throwing exceptions
    chart.update_data(labels, values, colors=colors, horizontal=False)
    chart.deleteLater()


@pytest.mark.skipif(IS_OFFSCREEN, reason="QWebEngineView crashes in offscreen mode on CI")
def test_bar_chart_full_label_mode_smoke_test(qapp):
    chart = LexiBarChart(title="Kod Frekansı")
    labels = [
        "Bu oldukça uzun bir etiket ismidir ve tam etiket modunda kırpılmamalıdır",
        "İkinci uzun etiket örneği burada yer alıyor",
    ]
    values = [8, 6]
    colors = ["#4F46E5", "#60A5FA"]
    # truncate_labels parameter was removed in favor of ApexCharts default behavior or show_labels
    chart.update_data(labels, values, colors=colors, horizontal=False, show_labels=True)
    assert chart.browser is not None
    chart.deleteLater()
