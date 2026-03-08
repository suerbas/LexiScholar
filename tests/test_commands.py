"""
Command Pattern Testleri — Undo/Redo doğruluğu.
"""
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.commands import (
    CommandStack,
    CreateSegmentCommand,
    DeleteSegmentCommand,
    BatchDeleteSegmentsCommand,
    CreateCodeCommand,
    DeleteCodeCommand,
    CreateMemoCommand,
    UpdateMemoCommand,
    DeleteMemoCommand,
    RenameCodeCommand,
    UpdateWeightCommand,
    InVivoCodingCommand,
)


# ─── CommandStack ─────────────────────────────────────────────
class TestCommandStack:
    def test_empty_stack_cannot_undo(self):
        stack = CommandStack()
        assert stack.can_undo() is False
        assert stack.undo() is False

    def test_empty_stack_cannot_redo(self):
        stack = CommandStack()
        assert stack.can_redo() is False
        assert stack.redo() is False

    def test_push_enables_undo(self, sample_document, sample_code, dao_segment):
        stack = CommandStack()
        cmd = CreateSegmentCommand(dao_segment, sample_document, sample_code, 0, 5, "t", 3, 1)
        stack.push(cmd)
        assert stack.can_undo() is True

    def test_undo_clears_redo_on_new_push(self, sample_document, sample_code, dao_segment):
        stack = CommandStack()
        cmd1 = CreateSegmentCommand(dao_segment, sample_document, sample_code, 0, 5, "t1", 3, 1)
        cmd2 = CreateSegmentCommand(dao_segment, sample_document, sample_code, 5, 10, "t2", 3, 1)
        stack.push(cmd1)
        stack.undo()
        stack.push(cmd2)
        assert stack.can_redo() is False  # Redo stack temizlenmeli

    def test_stack_respects_limit(self, sample_document, sample_code, dao_segment):
        stack = CommandStack(limit=3)
        for i in range(5):
            cmd = CreateSegmentCommand(dao_segment, sample_document, sample_code, i, i+1, f"t{i}", 3, 1)
            stack.push(cmd)
        assert len(stack.undo_stack) <= 3


# ─── Segment Commands ─────────────────────────────────────────
class TestCreateSegmentCommand:
    def test_execute_creates_segment(self, sample_document, sample_code, dao_segment):
        cmd = CreateSegmentCommand(dao_segment, sample_document, sample_code, 0, 5, "test", 3, 1)
        cmd.execute()
        assert cmd.segment_id is not None
        assert dao_segment.get_by_id(cmd.segment_id) is not None

    def test_undo_removes_segment(self, sample_document, sample_code, dao_segment):
        cmd = CreateSegmentCommand(dao_segment, sample_document, sample_code, 0, 5, "test", 3, 1)
        cmd.execute()
        seg_id = cmd.segment_id
        cmd.undo()
        assert dao_segment.get_by_id(seg_id) is None


class TestDeleteSegmentCommand:
    def test_execute_deletes_segment(self, sample_document, sample_code, dao_segment):
        seg_id = dao_segment.create(sample_document, sample_code, 0, 5, "sil")
        cmd = DeleteSegmentCommand(dao_segment, seg_id)
        cmd.execute()
        assert dao_segment.get_by_id(seg_id) is None

    def test_undo_restores_segment_content(self, sample_document, sample_code, dao_segment):
        seg_id = dao_segment.create(sample_document, sample_code, 0, 5, "geri gel")
        cmd = DeleteSegmentCommand(dao_segment, seg_id)
        cmd.execute()
        cmd.undo()
        # Segment geri gelmeli (yeni ID ile)
        segs = dao_segment.get_by_document(sample_document)
        texts = [s["segment_text"] for s in segs]
        assert "geri gel" in texts


class TestBatchDeleteCommand:
    def test_execute_deletes_all(self, sample_document, sample_code, dao_segment):
        ids = [dao_segment.create(sample_document, sample_code, i, i+2, f"s{i}") for i in range(3)]
        cmd = BatchDeleteSegmentsCommand(dao_segment, ids)
        cmd.execute()
        for sid in ids:
            assert dao_segment.get_by_id(sid) is None

    def test_undo_restores_all(self, sample_document, sample_code, dao_segment):
        ids = [dao_segment.create(sample_document, sample_code, i, i+2, f"r{i}") for i in range(2)]
        cmd = BatchDeleteSegmentsCommand(dao_segment, ids)
        cmd.execute()
        cmd.undo()
        segs = dao_segment.get_by_document(sample_document)
        texts = {s["segment_text"] for s in segs}
        assert "r0" in texts
        assert "r1" in texts


# ─── Code Commands ────────────────────────────────────────────
class TestCreateCodeCommand:
    def test_execute_creates_code(self, dao_code):
        cmd = CreateCodeCommand(dao_code, "YeniKod", "#AABBCC")
        cmd.execute()
        assert cmd.code_id is not None
        assert dao_code.get_by_id(cmd.code_id) is not None

    def test_undo_deletes_code(self, dao_code):
        cmd = CreateCodeCommand(dao_code, "SilBeni", "#FFFFFF")
        cmd.execute()
        code_id = cmd.code_id
        cmd.undo()
        assert dao_code.get_by_id(code_id) is None


class TestRenameCodeCommand:
    def test_execute_renames(self, sample_code, dao_code):
        cmd = RenameCodeCommand(dao_code, sample_code, "YeniAd")
        cmd.execute()
        assert dao_code.get_by_id(sample_code)["name"] == "YeniAd"

    def test_undo_restores_name(self, sample_code, dao_code):
        original = dao_code.get_by_id(sample_code)["name"]
        cmd = RenameCodeCommand(dao_code, sample_code, "Geçici")
        cmd.execute()
        cmd.undo()
        assert dao_code.get_by_id(sample_code)["name"] == original


# ─── Memo Commands ────────────────────────────────────────────
class TestMemoCommands:
    def test_create_memo_execute_and_undo(self, sample_document, dao_memo):
        memo_id = dao_memo.create("Not içeriği", document_id=sample_document)
        # Doğrudan oluştur, sonra sil ve geri al
        cmd = DeleteMemoCommand(dao_memo, memo_id)
        cmd.execute()
        assert dao_memo.get_by_id(memo_id) is None
        cmd.undo()
        # Geri dönünce içerik korunmuş olmalı
        memos = dao_memo.get_by_document(sample_document)
        assert any(m["content"] == "Not içeriği" for m in memos)

    def test_update_memo_undo_restores(self, sample_document, dao_memo):
        memo_id = dao_memo.create("İlk içerik", document_id=sample_document)
        cmd = UpdateMemoCommand(dao_memo, memo_id, "Güncel içerik")
        cmd.execute()
        assert dao_memo.get_by_id(memo_id)["content"] == "Güncel içerik"
        cmd.undo()
        assert dao_memo.get_by_id(memo_id)["content"] == "İlk içerik"

    def test_delete_memo_execute_and_undo(self, sample_document, dao_memo):
        memo_id = dao_memo.create("Silinecek not", document_id=sample_document)
        cmd = DeleteMemoCommand(dao_memo, memo_id)
        cmd.execute()
        assert dao_memo.get_by_id(memo_id) is None
        cmd.undo()
        # Geri döndükten sonra içerik korunmuş olmalı
        memos = dao_memo.get_by_document(sample_document)
        assert any(m["content"] == "Silinecek not" for m in memos)
