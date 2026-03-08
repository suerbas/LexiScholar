"""
ProjectManager Testleri — proje oluşturma, yükleme, yedekleme.
"""
import pytest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from project_manager import ProjectManager
from __version__ import PROJECT_SCHEMA_VERSION


@pytest.fixture
def pm(tmp_db_path) -> ProjectManager:
    """Geçici DB'ye bağlı ProjectManager."""
    from database.connection import init_db
    init_db(tmp_db_path)
    return ProjectManager(tmp_db_path)


class TestCreateProject:
    def test_create_returns_success(self, pm, tmp_path):
        ok, result = pm.create_project("TestProjesi", save_dir=str(tmp_path))
        assert ok is True
        assert Path(result).exists()

    def test_create_generates_project_json(self, pm, tmp_path):
        ok, db_path = pm.create_project("MetadataTesti", save_dir=str(tmp_path))
        project_dir = Path(db_path).parent
        meta_file = project_dir / "project.json"
        assert meta_file.exists()
        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
        assert meta["name"] == "MetadataTesti"
        assert "version" in meta

    def test_create_schema_version_is_current(self, pm, tmp_path):
        ok, db_path = pm.create_project("VersionTest", save_dir=str(tmp_path))
        meta_file = Path(db_path).parent / "project.json"
        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
        assert meta["version"] == PROJECT_SCHEMA_VERSION

    def test_create_duplicate_name_fails(self, pm, tmp_path):
        pm.create_project("Tekrar", save_dir=str(tmp_path))
        ok, msg = pm.create_project("Tekrar", save_dir=str(tmp_path))
        assert ok is False

    def test_invalid_name_fails(self, pm, tmp_path):
        ok, msg = pm.create_project("", save_dir=str(tmp_path))
        assert ok is False

    def test_path_traversal_blocked(self, pm, tmp_path):
        ok, msg = pm.create_project("../../kötü", save_dir=str(tmp_path))
        # Ya başarısız olmalı ya da güvenli yola yazılmalı
        if ok:
            # Eğer başarılı olduysa, path traversal gerçekleşmemiş olmalı
            result_path = Path(msg)
            assert str(tmp_path) in str(result_path.resolve())


class TestLoadProject:
    def test_load_existing_project(self, pm, tmp_path):
        _, db_path = pm.create_project("YüklemeTesti", save_dir=str(tmp_path))
        project_dir = Path(db_path).parent
        ok, loaded_db = pm.load_project(str(project_dir))
        assert ok is True
        assert Path(loaded_db).exists()

    def test_load_nonexistent_fails(self, pm, tmp_path):
        ok, msg = pm.load_project(str(tmp_path / "hiç_yok"))
        assert ok is False

    def test_load_via_lxs_marker(self, pm, tmp_path):
        _, db_path = pm.create_project("MarkerTest", save_dir=str(tmp_path))
        project_dir = Path(db_path).parent
        lxs_files = list(project_dir.glob("*.lxs"))
        assert len(lxs_files) == 1
        ok, loaded_db = pm.load_project(str(lxs_files[0]))
        assert ok is True


class TestSnapshot:
    def test_snapshot_creates_file(self, pm, tmp_path):
        _, db_path = pm.create_project("SnapshotTest", save_dir=str(tmp_path))
        pm2 = ProjectManager(db_path)
        ok, snap_path = pm2.create_snapshot()
        assert ok is True
        assert Path(snap_path).exists()

    def test_snapshot_keeps_max_5(self, pm, tmp_path):
        _, db_path = pm.create_project("Snapshots", save_dir=str(tmp_path))
        pm2 = ProjectManager(db_path)
        for _ in range(7):
            pm2.create_snapshot()
        backup_dir = Path(db_path).parent / "backups"
        snaps = list(backup_dir.glob("auto_snapshot_*.db"))
        assert len(snaps) <= 5


class TestGetRecentProjects:
    def test_returns_list(self, pm, tmp_path):
        pm.create_project("Proje1", save_dir=str(tmp_path))
        pm.create_project("Proje2", save_dir=str(tmp_path))
        projects = pm.get_recent_projects(str(tmp_path))
        assert isinstance(projects, list)
        assert len(projects) == 2

    def test_empty_dir_returns_empty(self, pm, tmp_path):
        assert pm.get_recent_projects(str(tmp_path)) == []
