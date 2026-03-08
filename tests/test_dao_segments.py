"""
CodedSegmentDAO Testleri — kodlama, boolean sorgu ve coder filtresi.
"""
import pytest


class TestSegmentCreate:
    def test_create_returns_id(self, sample_document, sample_code, dao_segment):
        seg_id = dao_segment.create(
            document_id=sample_document,
            code_id=sample_code,
            start_pos=0,
            end_pos=10,
            segment_text="Bu bir örnek",
        )
        assert isinstance(seg_id, int)
        assert seg_id > 0

    def test_weight_clamped_to_range(self, sample_document, sample_code, dao_segment):
        seg_id = dao_segment.create(sample_document, sample_code, 0, 5, "test", weight=99)
        seg = dao_segment.get_by_id(seg_id)
        assert 1 <= seg["weight"] <= 5

    def test_weight_minimum_clamped(self, sample_document, sample_code, dao_segment):
        seg_id = dao_segment.create(sample_document, sample_code, 0, 5, "test", weight=0)
        seg = dao_segment.get_by_id(seg_id)
        assert seg["weight"] >= 1


class TestSegmentRead:
    def test_get_by_document(self, sample_document, sample_code, dao_segment):
        dao_segment.create(sample_document, sample_code, 0, 5, "test")
        results = dao_segment.get_by_document(sample_document)
        assert len(results) == 1
        assert results[0]["document_id"] == sample_document

    def test_get_by_document_coder_filter(self, sample_document, sample_code, dao_segment):
        # Sadece varsayılan coder_id=1 kullan (FK kısıtı var)
        dao_segment.create(sample_document, sample_code, 0, 5, "test", coder_id=1)
        dao_segment.create(sample_document, sample_code, 5, 10, "test2", coder_id=1)
        results = dao_segment.get_by_document(sample_document, coder_id=1)
        assert len(results) == 2
        assert all(s["coder_id"] == 1 for s in results)
        # Var olmayan coder için boş liste dönmeli
        assert dao_segment.get_by_document(sample_document, coder_id=99) == []


    def test_get_by_code(self, sample_document, sample_code, dao_segment):
        dao_segment.create(sample_document, sample_code, 0, 5, "test")
        results = dao_segment.get_by_code(sample_code)
        assert len(results) >= 1

    def test_get_by_id_returns_correct(self, sample_document, sample_code, dao_segment):
        seg_id = dao_segment.create(sample_document, sample_code, 3, 15, "merhaba dünya")
        seg = dao_segment.get_by_id(seg_id)
        assert seg["segment_text"] == "merhaba dünya"
        assert seg["start_pos"] == 3

    def test_get_by_id_not_found(self, dao_segment):
        assert dao_segment.get_by_id(99999) is None


class TestSegmentBulkFetch:
    def test_get_by_documents_bulk(self, sample_document, sample_code, dao_segment, dao_document, tmp_path):
        path2 = str(tmp_path / "doc2.txt")
        doc2 = dao_document.create("Belge 2", path2, "txt", "İçerik 2")
        dao_segment.create(sample_document, sample_code, 0, 5, "test1")
        dao_segment.create(doc2, sample_code, 0, 5, "test2")
        result = dao_segment.get_by_documents_bulk([sample_document, doc2])
        assert sample_document in result
        assert doc2 in result

    def test_bulk_empty_returns_empty_dict(self, dao_segment):
        assert dao_segment.get_by_documents_bulk([]) == {}


class TestSegmentActiveCriteria:
    def test_active_criteria_returns_intersection(
        self, sample_document, sample_code, dao_segment, dao_document, dao_code, tmp_path
    ):
        code2_id = dao_code.create("KodB", "#00FF00", "")
        dao_segment.create(sample_document, sample_code, 0, 5, "s1")
        results = dao_segment.get_by_active_criteria([sample_document], [sample_code])
        assert len(results) >= 1

    def test_empty_doc_ids_returns_empty(self, sample_code, dao_segment):
        assert dao_segment.get_by_active_criteria([], [sample_code]) == []

    def test_empty_code_ids_returns_empty(self, sample_document, dao_segment):
        assert dao_segment.get_by_active_criteria([sample_document], []) == []


class TestSegmentBooleanQuery:
    def test_and_query(self, sample_document, sample_code, dao_segment, dao_code):
        code2 = dao_code.create("KodC", "#AABBCC", "")
        dao_segment.create(sample_document, sample_code, 0, 5, "s1")
        dao_segment.create(sample_document, code2, 5, 10, "s2")
        results = dao_segment.get_by_boolean_query([sample_code, code2], [], [])
        assert len(results) > 0

    def test_not_query_excludes_correctly(self, sample_document, sample_code, dao_segment, dao_code, dao_document, tmp_path):
        code2 = dao_code.create("KodD", "#112233", "")
        path2 = str(tmp_path / "doc2b.txt")
        doc2 = dao_document.create("Belge 2B", path2, "txt", "İçerik")
        dao_segment.create(sample_document, sample_code, 0, 5, "s1")
        dao_segment.create(doc2, code2, 0, 5, "s2")
        results = dao_segment.get_by_boolean_query([], [sample_code], [code2])
        doc_ids = {r["document_id"] for r in results}
        assert doc2 not in doc_ids


class TestSegmentDelete:
    def test_delete(self, sample_document, sample_code, dao_segment):
        seg_id = dao_segment.create(sample_document, sample_code, 0, 5, "sil beni")
        assert dao_segment.delete(seg_id) is True
        assert dao_segment.get_by_id(seg_id) is None

    def test_delete_batch(self, sample_document, sample_code, dao_segment):
        ids = [dao_segment.create(sample_document, sample_code, i, i+3, f"s{i}") for i in range(3)]
        assert dao_segment.delete_batch(ids) is True
        for sid in ids:
            assert dao_segment.get_by_id(sid) is None

    def test_delete_batch_empty_is_noop(self, dao_segment):
        assert dao_segment.delete_batch([]) is True
