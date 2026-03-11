import heapq
from typing import List, Dict

def calculate_document_portrait(doc_len: int, segments: List[Dict], grid_size: int = 1200) -> List[str]:
    if doc_len <= 0: return ["#FFFFFF"] * grid_size
    if grid_size <= 0: return []
    grid, cell_size = ["#F1F5F9"] * grid_size, doc_len / grid_size
    starts, ends, colors = [[] for _ in range(grid_size)], [[] for _ in range(grid_size)], {}
    for order, seg in enumerate(segments):
        start_pos, end_pos = max(0, float(seg.get("start", 0))), min(float(doc_len), float(seg.get("end", 0)))
        if end_pos < start_pos: continue
        start_idx, end_idx = int(start_pos / cell_size), int(end_pos / cell_size)
        if start_idx >= grid_size or end_idx < 0: continue
        start_idx, end_idx = max(0, min(grid_size - 1, start_idx)), max(0, min(grid_size - 1, end_idx))
        starts[start_idx].append(order); ends[end_idx].append(order); colors[order] = seg.get("color", "#CCCCCC")
    active, heap = set(), []
    for i in range(grid_size):
        if starts[i]:
            for order in starts[i]: active.add(order); heapq.heappush(heap, -order)
        while heap and (-heap[0]) not in active: heapq.heappop(heap)
        if heap: grid[i] = colors[-heap[0]]
        if ends[i]:
            for order in ends[i]: active.discard(order)
    return grid
