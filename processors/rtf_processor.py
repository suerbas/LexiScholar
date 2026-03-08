"""
RTF Processor for LexiScholar
Extracts text from Rich Text Format documents.
"""

from dataclasses import dataclass
from typing import Optional

try:
    from striprtf.striprtf import rtf_to_text
except ImportError:
    rtf_to_text = None


@dataclass
class RtfExtractionResult:
    """Result of RTF text extraction."""
    full_text: str
    success: bool
    error: Optional[str] = None


def extract_text(rtf_path: str) -> RtfExtractionResult:
    """
    Extract text from an RTF file.
    
    Args:
        rtf_path: Path to the RTF file
        
    Returns:
        RtfExtractionResult with full text
    """
    if rtf_to_text is None:
        return RtfExtractionResult(
            full_text="",
            success=False,
            error="striprtf library not installed. Run: pip install striprtf"
        )
    
    try:
        # Try different encodings
        encodings = ['utf-8', 'cp1252', 'latin-1', 'cp1254']
        content = None
        
        for encoding in encodings:
            try:
                with open(rtf_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # Fallback: read as binary and decode with errors='replace'
            with open(rtf_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
        
        # Convert RTF to plain text
        full_text = rtf_to_text(content)
        
        return RtfExtractionResult(
            full_text=full_text.strip(),
            success=True
        )
        
    except FileNotFoundError:
        return RtfExtractionResult(
            full_text="",
            success=False,
            error="File not found"
        )
    except Exception as e:
        return RtfExtractionResult(
            full_text="",
            success=False,
            error=str(e)
        )


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = extract_text(sys.argv[1])
        if result.success:
            print(f"Total characters: {len(result.full_text)}")
            print("\n--- First 500 characters ---")
            print(result.full_text[:500])
        else:
            print(f"Error: {result.error}")
    else:
        print("Usage: python rtf_processor.py <rtf_file>")
