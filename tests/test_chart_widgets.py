import sys
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.visualizations.charts.chart_widgets import LexiBarChart


def test_bar_chart_respects_vertical_for_long_labels(qapp):
    chart = LexiBarChart(title="Kod Frekansı")
    labels = [
        "Bu oldukça uzun bir etiket ismidir ve dikeyde kesilmelidir",
        "İkinci uzun etiket örneği burada yer alıyor",
    ]
    values = [12, 7]
    colors = ["#4F46E5", "#60A5FA"]
    chart.update_data(labels, values, colors=colors, horizontal=False)
    ax = chart.fig.axes[0]
    assert ax.get_ylabel() == "Frekans"
    assert ax.get_xlabel() == ""
    assert ax.get_legend() is not None
    chart.deleteLater()


def test_bar_chart_horizontal_does_not_force_truncation_legend(qapp):
    chart = LexiBarChart(title="Kod Frekansı")
    labels = [
        "Bu oldukça uzun bir etiket ismidir ve yatayda tam görünmelidir",
        "İkinci uzun etiket örneği burada yer alıyor",
    ]
    values = [9, 4]
    colors = ["#4F46E5", "#60A5FA"]
    chart.update_data(labels, values, colors=colors, horizontal=True)
    ax = chart.fig.axes[0]
    assert ax.get_xlabel() == "Frekans"
    assert ax.get_legend() is None
    chart.deleteLater()


def test_bar_chart_does_not_emit_tight_layout_warning(qapp):
    chart = LexiBarChart(title="Kod Frekansı")
    labels = [f"Uzun etiket {i} için örnek metin" for i in range(10)]
    values = [10] * 10
    colors = ["#4F46E5"] * 10
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        chart.update_data(labels, values, colors=colors, horizontal=False)
    assert not any("Tight layout not applied" in str(w.message) for w in caught)
    chart.deleteLater()


def test_bar_chart_full_label_mode_disables_truncation_legend(qapp):
    chart = LexiBarChart(title="Kod Frekansı")
    labels = [
        "Bu oldukça uzun bir etiket ismidir ve tam etiket modunda kırpılmamalıdır",
        "İkinci uzun etiket örneği burada yer alıyor",
    ]
    values = [8, 6]
    colors = ["#4F46E5", "#60A5FA"]
    chart.update_data(labels, values, colors=colors, horizontal=False, truncate_labels=False)
    ax = chart.fig.axes[0]
    xtick_texts = [tick.get_text() for tick in ax.get_xticklabels()]
    assert labels[0] in xtick_texts
    assert ax.get_legend() is None
    chart.deleteLater()
