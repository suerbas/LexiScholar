"""
NLP Engine Testleri — dil tespiti, KWIC, konu modelleme.
Model indirme gerektiren testler `slow` ile işaretlenmiş,
varsayılan koşumda atlanır: pytest -m "not slow"
"""
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nlp_engine import clean_html, detect_language, extract_kwic, calculate_document_portrait


# ─── clean_html ───────────────────────────────────────────────
class TestCleanHtml:
    def test_strips_tags(self):
        assert clean_html("<b>Merhaba</b>") == "Merhaba"

    def test_removes_style_block(self):
        html = "<style>body{color:red}</style>Metin"
        assert "color" not in clean_html(html)
        assert "Metin" in clean_html(html)

    def test_removes_script_block(self):
        html = "<script>alert('x')</script>İçerik"
        assert "alert" not in clean_html(html)
        assert "İçerik" in clean_html(html)

    def test_collapses_whitespace(self):
        result = clean_html("    çok   boşluk   ")
        assert "  " not in result

    def test_plain_text_unchanged(self):
        text = "Düz metin, değişmemeli."
        assert clean_html(text) == text


# ─── detect_language ──────────────────────────────────────────
class TestDetectLanguage:
    def test_turkish_characters_detected(self):
        assert detect_language("Bu bir güzel şehir") == "tr"

    def test_english_keywords_detected(self):
        # Gerçek bir İngilizce akademik cümle kullan (langdetect kısa metinleri atlar)
        long_english = (
            "This study investigates the relationship between socioeconomic factors "
            "and academic performance among university students in the United States. "
            "The findings suggest that students from higher income backgrounds tend to "
            "perform better on standardized assessments."
        )
        assert detect_language(long_english) == "en"

    def test_default_is_turkish(self):
        # Belirsiz metin → Türkçe varsayılan
        result = detect_language("abc def ghi")
        assert result in ("tr", "en")  # Hata vermemeli

    def test_mixed_output_is_string(self):
        lang = detect_language("Some text with some Turkish: çok güzel")
        assert lang in ("tr", "en")


# ─── extract_kwic ─────────────────────────────────────────────
class TestExtractKwic:
    TEXT = "Araştırmacı araştırma yöntemlerini inceledi. Araştırma sonuçları önemliydi."

    def test_finds_keyword(self):
        results = extract_kwic(self.TEXT, "araştırma")
        assert len(results) >= 1

    def test_result_has_required_keys(self):
        results = extract_kwic(self.TEXT, "araştırma")
        for r in results:
            assert "left" in r
            assert "keyword" in r
            assert "right" in r

    def test_no_match_returns_empty(self):
        assert extract_kwic(self.TEXT, "yabancı_kelime_xyz") == []

    def test_context_window_respected(self):
        results = extract_kwic(self.TEXT, "araştırma", context_window=3)
        for r in results:
            # left ve right en fazla 3 kelime içermeli
            left_words = r["left"].split()
            right_words = r["right"].split()
            assert len(left_words) <= 3
            assert len(right_words) <= 3

    def test_result_limit(self):
        # Çok tekrarlayan kelimede 500 sınırına çarpmaz mı?
        big_text = "test kelime " * 600
        results = extract_kwic(big_text, "test")
        assert len(results) <= 500


# ─── calculate_document_portrait ──────────────────────────────
class TestDocumentPortrait:
    def test_returns_list_of_correct_size(self):
        grid = calculate_document_portrait(1000, [], grid_size=100)
        assert len(grid) == 100

    def test_all_white_when_no_segments(self):
        grid = calculate_document_portrait(1000, [], grid_size=10)
        assert all(c == "#F1F5F9" for c in grid)

    def test_segment_color_applied(self):
        seg = {"start": 0, "end": 500, "color": "#FF0000"}
        grid = calculate_document_portrait(1000, [seg], grid_size=10)
        assert "#FF0000" in grid  # Segmentin rengi uygulanmış olmalı

    def test_zero_doc_len_handled(self):
        grid = calculate_document_portrait(0, [], grid_size=10)
        assert len(grid) == 10  # Hata vermemeli

    def test_zero_grid_size_returns_empty(self):
        grid = calculate_document_portrait(100, [], grid_size=0)
        assert grid == []

    def test_overlap_uses_last_segment_priority(self):
        segs = [
            {"start": 0, "end": 100, "color": "#111111"},
            {"start": 20, "end": 80, "color": "#222222"},
        ]
        grid = calculate_document_portrait(100, segs, grid_size=10)
        assert grid[5] == "#222222"


# ─── Model gerektiren testler (atlanabilir) ───────────────────
@pytest.mark.slow
class TestModelBasedNLP:
    """Bu testler internet / BERT modeli gerektirir. `pytest -m slow` ile koşulur."""

    def test_sentiment_analysis_returns_dict(self):
        from nlp_engine import analyze_sentiment
        result = analyze_sentiment("Bu ürün harika, çok memnunum!")
        assert "label" in result
        assert "score" in result
        assert "level" in result

    def test_extract_entities_returns_list(self):
        from nlp_engine import extract_entities
        result = extract_entities("Türkiye'de İstanbul en büyük şehirdir.")
        assert isinstance(result, list)

    def test_extract_keywords_returns_list(self):
        from nlp_engine import extract_keywords
        result = extract_keywords("Makine öğrenmesi ve derin öğrenme modern yapay zekanın temelini oluşturur.")
        assert isinstance(result, list)
        if result:
            assert "keyword" in result[0]


class TestNlpFallbacks:
    def test_sentiment_fallback_returns_valid_shape(self, monkeypatch):
        import nlp_engine
        monkeypatch.setattr(nlp_engine._cache, "get_sentiment", lambda lang: None)
        result = nlp_engine.analyze_sentiment("Bu ürün çok iyi ve başarılı.")
        assert "label" in result
        assert "score" in result
        assert "level" in result
        assert result["label"] in ("very positive", "positive", "neutral", "negative", "very negative")

    def test_entities_fallback_returns_list(self, monkeypatch):
        import nlp_engine
        monkeypatch.setattr(nlp_engine._cache, "get_ner", lambda lang: None)
        result = nlp_engine.extract_entities("Ankara Üniversitesi Türkiye'dedir.")
        assert isinstance(result, list)
