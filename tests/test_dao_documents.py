"""
DocumentDAO Testleri — CRUD operasyonları ve kenar durumlar.
"""
import pytest


class TestDocumentCreate:
    def test_create_returns_integer_id(self, dao_document, tmp_path):
        path = str(tmp_path / "doc1.txt")
        doc_id = dao_document.create("Belge 1", path, "txt", "İçerik", None)
        assert isinstance(doc_id, int)
        assert doc_id > 0

    def test_create_multiple_unique_paths(self, dao_document, tmp_path):
        for i in range(3):
            path = str(tmp_path / f"doc{i}.txt")
            doc_id = dao_document.create(f"Belge {i}", path, "txt", "İçerik")
            assert doc_id > 0

    def test_create_duplicate_path_raises(self, dao_document, tmp_path):
        path = str(tmp_path / "dup.txt")
        dao_document.create("İlk", path, "txt", "İçerik")
        with pytest.raises(Exception):
            dao_document.create("İkinci", path, "txt", "Farklı içerik")

    def test_create_with_folder(self, dao_document, dao_folder, tmp_path):
        folder_id = dao_folder.create("Klasör A")
        path = str(tmp_path / "klasorlu.txt")
        doc_id = dao_document.create("Klasörlü Belge", path, "txt", "İçerik", folder_id)
        doc = dao_document.get_by_id(doc_id)
        assert doc["folder_id"] == folder_id


class TestDocumentRead:
    def test_get_by_id_returns_dict(self, sample_document, dao_document):
        doc = dao_document.get_by_id(sample_document)
        assert isinstance(doc, dict)
        assert doc["id"] == sample_document

    def test_get_by_id_nonexistent_returns_none(self, dao_document):
        assert dao_document.get_by_id(99999) is None

    def test_get_all_returns_list(self, sample_document, dao_document):
        docs = dao_document.get_all()
        assert isinstance(docs, list)
        assert len(docs) >= 1

    def test_get_all_empty_db(self, dao_document):
        assert dao_document.get_all() == []

    def test_fields_present(self, sample_document, dao_document):
        doc = dao_document.get_by_id(sample_document)
        for field in ("id", "title", "file_path", "file_type", "extracted_text"):
            assert field in doc


class TestDocumentUpdate:
    def test_update_content(self, sample_document, dao_document):
        result = dao_document.update_content(sample_document, "Güncellenmiş içerik")
        assert result is True
        doc = dao_document.get_by_id(sample_document)
        assert doc["extracted_text"] == "Güncellenmiş içerik"

    def test_rename(self, sample_document, dao_document):
        result = dao_document.rename(sample_document, "Yeni Başlık")
        assert result is True
        doc = dao_document.get_by_id(sample_document)
        assert doc["title"] == "Yeni Başlık"


class TestDocumentActivation:
    def test_set_active_true(self, sample_document, dao_document):
        dao_document.set_active(sample_document, True)
        active_ids = dao_document.get_active_ids()
        assert sample_document in active_ids

    def test_set_active_false(self, sample_document, dao_document):
        dao_document.set_active(sample_document, True)
        dao_document.set_active(sample_document, False)
        active_ids = dao_document.get_active_ids()
        assert sample_document not in active_ids

    def test_reset_activation(self, sample_document, dao_document, tmp_path):
        path2 = str(tmp_path / "doc2.txt")
        doc2 = dao_document.create("Belge 2", path2, "txt", "İçerik 2")
        dao_document.set_active(sample_document, True)
        dao_document.set_active(doc2, True)
        dao_document.reset_activation()
        assert dao_document.get_active_ids() == []


class TestDocumentDelete:
    def test_delete_existing(self, sample_document, dao_document):
        result = dao_document.delete(sample_document)
        assert result is True
        assert dao_document.get_by_id(sample_document) is None

    def test_delete_nonexistent_returns_false(self, dao_document):
        result = dao_document.delete(99999)
        assert result is False
