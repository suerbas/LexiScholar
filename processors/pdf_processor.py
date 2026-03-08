"""
PDF Processor for LexiScholar
Extracts text from PDF files while maintaining character positions for coding.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import os
import fitz  # PyMuPDF


@dataclass
class TextBlock:
    """Represents a block of text with its position information."""
    text: str
    start_pos: int
    end_pos: int
    page_num: int
    bbox: tuple  # (x0, y0, x1, y1) bounding box on page


@dataclass
class ExtractionResult:
    """Result of PDF text extraction."""
    full_text: str
    blocks: List[TextBlock]
    page_count: int
    success: bool
    error: Optional[str] = None


def extract_text_with_positions(pdf_path: str) -> ExtractionResult:
    """
    Extract text from PDF with character-level position tracking.
    
    This is critical for QDA software because:
    1. Coded segments need exact start/end positions in the extracted text
    2. These positions must map back to visual locations for coding stripes
    3. Paragraph structure should be preserved for readability
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        ExtractionResult with full text, blocks with positions, and metadata
    """
    try:
        # Memory Management: Check file size (limit 50MB)
        MAX_SIZE = 50 * 1024 * 1024
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > MAX_SIZE:
             return ExtractionResult(
                full_text="",
                blocks=[],
                page_count=0,
                success=False,
                error="Dosya çok büyük (Limit: 50MB). Lütfen daha küçük parçalara bölün."
            )

        doc = fitz.open(pdf_path)
        blocks: List[TextBlock] = []
        full_text_parts: List[str] = []
        char_offset = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_rect = page.rect
            page_height = page_rect.height
            
            # 1. Identify Tables
            tables = []
            try:
                tables = page.find_tables().tables
            except AttributeError:
                pass # older PyMuPDF version

            table_bboxes = [t.bbox for t in tables] # List of Rect or tuple
            
            # 2. Extract Tables as Text items
            page_items = []
            for tab in tables:
                tab_text = ""
                extracted = tab.extract()
                if extracted:
                    for row in extracted:
                        row_text = " | ".join([(cell or "").strip() for cell in row if cell is not None])
                        tab_text += f"| {row_text} |\n"
                if tab_text:
                    page_items.append({
                        "type": "table",
                        "bbox": tab.bbox,
                        "text": tab_text.strip()
                    })
                    
            # Get text as dictionary with detailed position info
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            
            # 3. Process Text Blocks
            for block in text_dict.get("blocks", []):
                # Skip image blocks
                if block.get("type") != 0:  # 0 = text, 1 = image
                    continue
                
                bbox = block.get("bbox", (0, 0, 0, 0))
                y0, y1 = bbox[1], bbox[3]
                
                # Filter headers/footers (approx top 8% and bottom 8%)
                if y0 < page_height * 0.08 or y1 > page_height * 0.92:
                    continue
                    
                # Skip if inside a table (to avoid duplicate messy text)
                inside_table = False
                for t_bbox in table_bboxes:
                    # Check overlap. t_bbox is (x0,y0,x1,y1)
                    tx0, ty0, tx1, ty1 = t_bbox
                    if ty0 - 5 <= y0 and ty1 + 5 >= y1 and tx0 - 5 <= bbox[0] and tx1 + 5 >= bbox[2]:
                        inside_table = True
                        break
                
                if inside_table:
                    continue
                
                block_text_parts = []
                for line in block.get("lines", []):
                    line_text_parts = []
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        if span_text:
                            line_text_parts.append(span_text)
                    
                    if line_text_parts:
                        line_text = "".join(line_text_parts).strip()
                        if line_text:
                            block_text_parts.append(line_text)
                
                if block_text_parts:
                    # Smart paragraph joining: join lines with space instead of newline
                    clean_lines = []
                    for i, l in enumerate(block_text_parts):
                        if i > 0 and clean_lines[-1].endswith("-"):
                            # Hyphenated word continuation
                            clean_lines[-1] = clean_lines[-1][:-1] + l
                        else:
                            clean_lines.append(l)
                            
                    block_text = " ".join(clean_lines)
                    
                    page_items.append({
                        "type": "text",
                        "bbox": bbox,
                        "text": block_text
                    })
            
            # 4. Sort all items (text + tables) top-to-bottom
            page_items.sort(key=lambda x: x["bbox"][1])
            
            # --- SMART BLOCK MERGER ---
            # Makalelerde veya formatı eksik PDF'lerde her fiziksel satır ayrı block (paragraf) olarak gelebiliyor.
            # Bu durum QDA programlarında analizi zorlaştırdığı için satırları boşluk toleransıyla birleştiriyoruz.
            merged_items = []
            for item in page_items:
                if not merged_items:
                    merged_items.append(item)
                    continue
                    
                prev = merged_items[-1]
                if prev["type"] == "text" and item["type"] == "text":
                    # İki blok arasındaki dikey boşluk (gap)
                    gap = item["bbox"][1] - prev["bbox"][3]
                    
                    # Başlık veya liste olma ihtimali
                    is_short = len(prev["text"]) < 40 and not prev["text"].endswith("-")
                    
                    # Eğer çok uzak değillerse ve önceki satır nokta/soru işareti gibi bir cümle bitiriciyle BİTMİYORSA:
                    if -20 <= gap <= 25 and not prev["text"].endswith((".", "?", "!", ":", ";", "\n")) and not is_short:
                        if prev["text"].endswith("-"):
                            # Tireyle bölünen kelimeyi bitiştir
                            prev["text"] = prev["text"][:-1] + item["text"]
                        else:
                            # Sadece bir boşluk bırakarak birleştir
                            prev["text"] += " " + item["text"]
                            
                        # Sınır kutusunu (bounding box) her ikisini kapsayacak şekilde genişlet
                        prev["bbox"] = (
                            min(prev["bbox"][0], item["bbox"][0]),
                            min(prev["bbox"][1], item["bbox"][1]),
                            max(prev["bbox"][2], item["bbox"][2]),
                            max(prev["bbox"][3], item["bbox"][3])
                        )
                        continue
                        
                merged_items.append(item)
            
            page_items = merged_items
            # --------------------------
            
            for item in page_items:
                block_text = item["text"]
                if full_text_parts:
                    char_offset += 2
                # Create TextBlock with position info
                text_block = TextBlock(
                    text=block_text,
                    start_pos=char_offset,
                    end_pos=char_offset + len(block_text),
                    page_num=page_num,
                    bbox=tuple(item["bbox"])
                )
                blocks.append(text_block)
                full_text_parts.append(block_text)
                char_offset += len(block_text)
        
        # Store page count before closing
        page_count = len(doc)
        doc.close()
        
        # Join with double newlines for paragraph separation
        full_text = "\n\n".join(full_text_parts)
        
        return ExtractionResult(
            full_text=full_text,
            blocks=blocks,
            page_count=page_count,
            success=True
        )
        
    except Exception as e:
        return ExtractionResult(
            full_text="",
            blocks=[],
            page_count=0,
            success=False,
            error=str(e)
        )


def get_page_for_position(blocks: List[TextBlock], char_pos: int) -> int:
    """
    Find which page a character position belongs to.
    Useful for jumping to the correct page when clicking a retrieved segment.
    """
    for block in blocks:
        if block.start_pos <= char_pos < block.end_pos:
            return block.page_num
    return 0


def get_bbox_for_range(blocks: List[TextBlock], start_pos: int, end_pos: int) -> List[tuple]:
    """
    Get bounding boxes for a text range.
    Useful for drawing coding stripes in the margin.
    
    Returns list of (page_num, bbox) tuples for the range.
    """
    result = []
    for block in blocks:
        # Check if this block overlaps with our range
        if block.end_pos > start_pos and block.start_pos < end_pos:
            result.append((block.page_num, block.bbox))
    return result


if __name__ == "__main__":
    # Test extraction
    import sys
    if len(sys.argv) > 1:
        result = extract_text_with_positions(sys.argv[1])
        if result.success:
            print(f"Extracted {len(result.full_text)} characters from {result.page_count} pages")
            print(f"Found {len(result.blocks)} text blocks")
            print("\n--- First 500 characters ---")
            print(result.full_text[:500])
        else:
            print(f"Error: {result.error}")
    else:
        print("Usage: python pdf_processor.py <pdf_file>")
