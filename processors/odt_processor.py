"""
ODT Processor for LexiScholar
Extracts text from OpenOffice/LibreOffice documents (.odt).
"""

from dataclasses import dataclass
from typing import Optional

try:
    from odf import text, teletype
    from odf.opendocument import load
    ODFPY_AVAILABLE = True
except ImportError:
    ODFPY_AVAILABLE = False


@dataclass
class ODTExtractionResult:
    """Result of ODT text extraction."""
    full_text: str
    success: bool
    error: Optional[str] = None


def extract_text(odt_path: str) -> ODTExtractionResult:
    """
    Extract text from an ODT file.
    
    Args:
        odt_path: Path to the .odt file
        
    Returns:
        ODTExtractionResult with full text
    """
    if not ODFPY_AVAILABLE:
        return ODTExtractionResult(
            full_text="",
            success=False,
            error="odfpy kütüphanesi yüklü değil. Lütfen yükleyin: pip install odfpy"
        )
    
    try:
        doc = load(odt_path)
        all_paragraphs = doc.getElementsByType(text.P)
        full_text = []
        
        for p in all_paragraphs:
            content = teletype.extractText(p)
            if content:
                full_text.append(content)
        
        return ODTExtractionResult(
            full_text="\n\n".join(full_text),
            success=True
        )
        
    except FileNotFoundError:
        return ODTExtractionResult(
            full_text="",
            success=False,
            error="Dosya bulunamadı."
        )
    except Exception as e:
        return ODTExtractionResult(
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
            print("\n--- First 1000 characters ---")
            print(result.full_text[:1000])
        else:
            print(f"Error: {result.error}")
    else:
        print("Usage: python odt_processor.py <odt_file>")
