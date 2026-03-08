import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from processors import pdf_processor


class _FakeRect:
    def __init__(self, height=1000):
        self.height = height


class _FakeTableResult:
    def __init__(self):
        self.tables = []


class _FakePage:
    def __init__(self, text):
        self.rect = _FakeRect()
        self._text = text

    def find_tables(self):
        return _FakeTableResult()

    def get_text(self, mode, flags=None):
        return {
            "blocks": [
                {
                    "type": 0,
                    "bbox": (50, 100, 500, 120),
                    "lines": [{"spans": [{"text": self._text}]}],
                }
            ]
        }


class _FakeDoc:
    def __init__(self, pages):
        self._pages = pages

    def __len__(self):
        return len(self._pages)

    def __getitem__(self, idx):
        return self._pages[idx]

    def close(self):
        return None


def test_pdf_block_offsets_follow_full_text(monkeypatch):
    fake_doc = _FakeDoc([_FakePage("AAAA"), _FakePage("BBBB")])
    monkeypatch.setattr(pdf_processor.fitz, "open", lambda _: fake_doc)
    result = pdf_processor.extract_text_with_positions("x.pdf")
    assert result.success is True
    assert result.full_text == "AAAA\n\nBBBB"
    assert len(result.blocks) == 2
    assert result.blocks[0].start_pos == 0
    assert result.blocks[0].end_pos == 4
    assert result.blocks[1].start_pos == 6
    assert result.blocks[1].end_pos == 10
