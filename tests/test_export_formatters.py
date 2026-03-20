from export.exporters import _validate_hex_color

def test_valid_hex_accepted():
    assert _validate_hex_color("#4F46E5") == "#4F46E5"
    assert _validate_hex_color("#ABC") == "#ABC"

def test_invalid_color_returns_default():
    assert _validate_hex_color("red") == "#4f46e5"
    assert _validate_hex_color("javascript:alert(1)") == "#4f46e5"
    assert _validate_hex_color("") == "#4f46e5"

def test_memo_grouping_logic():
    memos = [
        {"id": 1, "document_id": 1},
        {"id": 2, "start_pos": 10},
        {"id": 3, "code_id": 5},
        {"id": 4, "code_id": 5, "start_pos": 10},
        {"id": 5, "document_id": 1, "code_id": 5}
    ]
    
    segment_memos = [m for m in memos if m.get('start_pos')]
    code_memos = [m for m in memos if m.get('code_id') and not m.get('start_pos')]
    doc_memos = [m for m in memos if m.get('document_id') and not m.get('start_pos') and not m.get('code_id')]
    
    assert len(segment_memos) == 2
    assert len(code_memos) == 2
    assert len(doc_memos) == 1
