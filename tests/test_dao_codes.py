"""
CodeDAO Testleri — hiyerarşi, cascade silme ve aktivasyon.
"""
import pytest


class TestCodeCreate:
    def test_create_root_code(self, dao_code):
        code_id = dao_code.create("KökKod", "#FF0000", "Açıklama")
        assert code_id > 0

    def test_create_child_code(self, dao_code):
        parent_id = dao_code.create("Üst", "#FF0000", "")
        child_id = dao_code.create("Alt", "#00FF00", "", parent_id=parent_id)
        code = dao_code.get_by_id(child_id)
        assert code["parent_id"] == parent_id


class TestCodeRead:
    def test_get_all_returns_list(self, sample_code, dao_code):
        codes = dao_code.get_all()
        assert isinstance(codes, list)
        assert any(c["id"] == sample_code for c in codes)

    def test_get_by_id(self, sample_code, dao_code):
        code = dao_code.get_by_id(sample_code)
        assert code is not None
        assert code["id"] == sample_code

    def test_get_by_id_not_found(self, dao_code):
        assert dao_code.get_by_id(99999) is None


class TestCodeUpdate:
    def test_update_name(self, sample_code, dao_code):
        dao_code.update(sample_code, name="YeniAd")
        code = dao_code.get_by_id(sample_code)
        assert code["name"] == "YeniAd"

    def test_update_color(self, sample_code, dao_code):
        dao_code.update(sample_code, color="#123456")
        code = dao_code.get_by_id(sample_code)
        assert code["color"] == "#123456"


class TestCodeActivation:
    def test_set_active(self, sample_code, dao_code):
        dao_code.set_active(sample_code, True)
        active = dao_code.get_active_ids()
        assert sample_code in active

    def test_deactivate(self, sample_code, dao_code):
        dao_code.set_active(sample_code, True)
        dao_code.set_active(sample_code, False)
        assert sample_code not in dao_code.get_active_ids()


class TestCodeDelete:
    def test_delete_removes_code(self, dao_code):
        code_id = dao_code.create("Geçici", "#FFFFFF", "")
        dao_code.delete(code_id)
        assert dao_code.get_by_id(code_id) is None

    def test_delete_cascades_to_children(self, dao_code):
        parent = dao_code.create("Ebeveyn", "#111111", "")
        child = dao_code.create("Çocuk", "#222222", "", parent_id=parent)
        dao_code.delete(parent)
        assert dao_code.get_by_id(child) is None  # CASCADE
