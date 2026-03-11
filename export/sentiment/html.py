"""
Export Sentiment Analysis to HTML.
"""

from datetime import datetime
from typing import List, Dict

from .utils import (
    _compute_sentiment_stats,
    _get_label_hex,
    _score_color,
    _translate_label,
    _build_html_shell,
    _compare_sentiment_labels,
    _comparison_color,
    _ratio_text
)

def export_sentiment_to_html(
    file_path: str,
    results: List[Dict],
    model_type: str = "BERT"
) -> bool:
    """
    Export sentiment analysis results to detailed HTML format.
    """
    try:
        labels = [r.get('label', 'neutral') for r in results]
        scores = [r.get('score', 0.5) for r in results]
        stats = _compute_sentiment_stats(labels, scores)
        generated_at = datetime.now().strftime('%d.%m.%Y %H:%M')
        report_title = 'Duygu Analizi Raporu'
        meta_text = f"{generated_at} | Toplam: {len(results)} belge"

        rows_html = ""
        for i, r in enumerate(results, 1):
            label = r.get('label', 'neutral')
            score = r.get('score', 0.5)
            badge_color = _get_label_hex(label)
            progress_color = _score_color(score)
            rows_html += f"""
                <tr>
                    <td class="idx">#{i}</td>
                    <td class="doc">{r.get('title', 'Bilinmeyen')}</td>
                    <td><span class="badge" style="background:{badge_color}18;color:{badge_color};border-color:{badge_color}33">{_translate_label(label)}</span></td>
                    <td>
                        <div class="score">{score:.0%}</div>
                        <div class="bar"><div class="fill" style="width:{score:.0%};background:{progress_color}"></div></div>
                    </td>
                    <td class="summary">{r.get('summary', 'Analiz özeti mevcut değil.')}</td>
                </tr>
            """

        html_content = _build_html_shell(
            page_title=report_title,
            header_title=report_title,
            meta_text=meta_text,
            stat_cards=[
                ("Pozitif", str(stats['pos_total']), stats['pos_pct'], "positive"),
                ("Nötr", str(stats['neu_total']), stats['neu_pct'], "neutral"),
                ("Negatif", str(stats['neg_total']), stats['neg_pct'], "negative"),
                ("Ortalama Skor", stats['avg_percentage'], stats['overall_sentiment'], "accent"),
            ],
            section_title="Belge Bazlı Sonuçlar",
            section_body=f"""
            <table class="result-table single-mode">
                <thead>
                    <tr>
                        <th>Sıra</th>
                        <th>Belge</th>
                        <th>Duygu</th>
                        <th>Skor</th>
                        <th>Özet / Analiz</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """,
            footer_text=f"LexiScholar Akademik Analiz Yazılımı | {datetime.now().strftime('%d.%m.%Y')}"
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return True

    except Exception as e:
        print(f"HTML export error: {e}")
        return False

def export_hybrid_sentiment_to_html(file_path: str, results: List[Dict], model_type: str = "AI") -> bool:
    """
    Export hybrid sentiment comparison to detailed HTML format.
    Shows both BERT and AI model results with summaries.
    """
    try:
        generated_at = datetime.now().strftime('%d.%m.%Y %H:%M')
        local_scores = [r.get('local', {}).get('score', 0.5) for r in results]
        online_scores = [r.get('online', {}).get('score', 0.5) for r in results]

        exact_count = 0
        close_count = 0
        different_count = 0
        rows_html = ""

        for i, r in enumerate(results, 1):
            local = r.get('local', {})
            online = r.get('online', {})
            comparison = _compare_sentiment_labels(local.get('label', 'neutral'), online.get('label', 'neutral'))

            if comparison['state'] == 'exact':
                exact_count += 1
            elif comparison['state'] == 'close':
                close_count += 1
            else:
                different_count += 1

            l_label = local.get('label', 'neutral')
            o_label = online.get('label', 'neutral')
            l_score = local.get('score', 0.5)
            o_score = online.get('score', 0.5)
            o_conf = online.get('confidence', 0.5)
            l_color = _get_label_hex(l_label)
            o_color = _get_label_hex(o_label)
            compare_color = _comparison_color(comparison['state'])

            rows_html += f"""
                <tr>
                    <td class="idx">#{i}</td>
                    <td class="doc">{r.get('title', 'Bilinmeyen')}</td>
                    <td class="model-cell">
                        <span class="badge" style="background:{l_color}18;color:{l_color};border-color:{l_color}33">{_translate_label(l_label)}</span>
                        <div class="score">{l_score:.0%}</div>
                        <div class="bar"><div class="fill" style="width:{l_score:.0%};background:{_score_color(l_score)}"></div></div>
                        <div class="summary">{local.get('summary', 'Özet yok')}</div>
                    </td>
                    <td class="model-cell">
                        <span class="badge" style="background:{o_color}18;color:{o_color};border-color:{o_color}33">{_translate_label(o_label)}</span>
                        <div class="score">{o_score:.0%}</div>
                        <div class="bar"><div class="fill" style="width:{o_score:.0%};background:{_score_color(o_score)}"></div></div>
                        <div class="meta-inline">Güven: {o_conf:.0%}</div>
                        <div class="summary">{online.get('summary', 'Özet yok')}</div>
                    </td>
                    <td><span class="badge compare" style="background:{compare_color}18;color:{compare_color};border-color:{compare_color}33">{comparison['label']}</span></td>
                </tr>
            """

        avg_local = sum(local_scores) / len(local_scores) if local_scores else 0.5
        avg_online = sum(online_scores) / len(online_scores) if online_scores else 0.5
        html_content = _build_html_shell(
            page_title='Hibrit Duygu Analizi Raporu',
            header_title='Hibrit Duygu Analizi Raporu',
            meta_text=f"{generated_at} | Toplam: {len(results)} belge",
            stat_cards=[
                ("Uyumlu", str(exact_count), _ratio_text(exact_count, len(results)), "positive"),
                ("Yakın", str(close_count), _ratio_text(close_count, len(results)), "warning"),
                ("Farklı", str(different_count), _ratio_text(different_count, len(results)), "negative"),
                ("Ort. Skorlar", f"{avg_local:.0%} / {avg_online:.0%}", "BERT / Online", "accent"),
            ],
            section_title='Belge Bazlı Karşılaştırma',
            section_body=f"""
            <table class="result-table hybrid-mode">
                <thead>
                    <tr>
                        <th>Sıra</th>
                        <th>Belge</th>
                        <th>Lokal</th>
                        <th>Online</th>
                        <th>Karşılaştırma</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """,
            footer_text=f"LexiScholar Akademik Analiz Yazılımı | {datetime.now().strftime('%d.%m.%Y')}"
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return True

    except Exception as e:
        print(f"Hybrid HTML export error: {e}")
        return False
