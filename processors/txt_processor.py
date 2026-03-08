"""
TXT Processor for LexiScholar
Handles plain text file import with encoding detection.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import chardet
except ImportError:
    chardet = None


@dataclass
class TxtExtractionResult:
    """Result of TXT text extraction."""
    full_text: str
    encoding: str
    success: bool
    error: Optional[str] = None


def detect_encoding(file_path: str) -> str:
    """Detect file encoding using chardet or fallback to UTF-8."""
    if chardet is None:
        return "utf-8"
    
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
            result = chardet.detect(raw_data)
            return result.get("encoding", "utf-8") or "utf-8"
    except Exception:
        return "utf-8"


def extract_text(txt_path: str) -> TxtExtractionResult:
    """
    Extract text from a plain text file.
    
    Automatically detects encoding to handle various file sources
    (UTF-8, Latin-1, Windows-1252, etc.).
    
    Args:
        txt_path: Path to the text file
        
    Returns:
        TxtExtractionResult with full text and detected encoding
    """
    try:
        encoding = detect_encoding(txt_path)
        
        try:
            with open(txt_path, "r", encoding=encoding) as f:
                full_text = f.read()
        except UnicodeDecodeError:
            # Fallback to UTF-8 with error handling
            with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
                full_text = f.read()
            encoding = "utf-8 (fallback)"
        
        return TxtExtractionResult(
            full_text=full_text,
            encoding=encoding,
            success=True
        )
        
    except FileNotFoundError:
        return TxtExtractionResult(
            full_text="",
            encoding="",
            success=False,
            error="File not found"
        )
    except Exception as e:
        return TxtExtractionResult(
            full_text="",
            encoding="",
            success=False,
            error=str(e)
        )


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = extract_text(sys.argv[1])
        if result.success:
            print(f"Encoding: {result.encoding}")
            print(f"Total characters: {len(result.full_text)}")
            print("\n--- First 500 characters ---")
            print(result.full_text[:500])
        else:
            print(f"Error: {result.error}")
    else:
        print("Usage: python txt_processor.py <txt_file>")
