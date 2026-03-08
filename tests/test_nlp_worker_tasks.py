import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.worker_threads import NLPWorker


def test_kwic_worker_emits_results(monkeypatch):
    import nlp_engine

    def fake_kwic(text, keyword, context_window=10):
        return [{"left": "a", "keyword": keyword, "right": "b"}]

    monkeypatch.setattr(nlp_engine, "extract_kwic", fake_kwic)
    worker = NLPWorker("kwic", [{"doc_id": 1, "title": "D1", "text": "x"}], options={"keyword": "anahtar"})
    captured = []
    worker.finished.connect(lambda payload: captured.append(payload))
    worker.run()
    assert captured
    assert captured[0][0]["keyword"] == "anahtar"
    assert len(captured[0][0]["results"]) == 1


def test_document_portrait_worker_emits_grid(monkeypatch):
    import nlp_engine

    monkeypatch.setattr(nlp_engine, "calculate_document_portrait", lambda doc_len, segments: ["#AAA"])
    worker = NLPWorker(
        "document_portrait",
        [],
        options={"doc_len": 123, "segments": [{"start": 1, "end": 2, "color": "#000"}], "title": "Belge"},
    )
    captured = []
    worker.finished.connect(lambda payload: captured.append(payload))
    worker.run()
    assert captured
    assert captured[0][0]["title"] == "Belge"
    assert captured[0][0]["grid_colors"] == ["#AAA"]
