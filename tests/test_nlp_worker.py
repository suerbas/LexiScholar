from ui.worker_threads import NLPWorker

def test_ner_worker_cancel_emits_no_signal(monkeypatch, qapp):
    """NERWorker iptal edildiğinde finished sinyali yayılmamalı."""
    worker = NLPWorker("ner", [{"doc_id": 1, "title": "T", "text": "test"}])
    worker._is_canceled = True
    
    # Mock extract functions to avoid real execution
    monkeypatch.setattr("nlp_engine.extract_entities", lambda x: [])
    monkeypatch.setattr("nlp_engine.compare_entity_results", lambda x, y: {})
    monkeypatch.setattr("nlp_engine._aggregate_entity_documents", lambda x, mode: {})
    
    emitted = []
    worker.finished.connect(emitted.append)
    worker._run_ner()
    
    assert emitted == []
