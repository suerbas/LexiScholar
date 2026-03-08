"""
DOC Processor for LexiScholar
Extracts text from older Microsoft Word (.doc) documents.
Uses pywin32 to interface with Word application on Windows.
"""

from dataclasses import dataclass
from typing import Optional
import os
import platform

import subprocess

@dataclass
class DocExtractionResult:
    """Result of DOC text extraction."""
    full_text: str
    success: bool
    error: Optional[str] = None


def _extract_with_antiword(doc_path: str) -> Optional[str]:
    """Try extracting text using antiword if it's available in PATH."""
    try:
        # antiword -m UTF-8.txt <file.doc>
        result = subprocess.run(
            ['antiword', '-m', 'UTF-8.txt', doc_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None

def _extract_fallback_strings(doc_path: str) -> str:
    """
    A very basic fallback mechanism that attempts to extract readable strings 
    directly from the binary .doc file if no other options are available.
    This won't be perfect, but it's better than nothing for raw text.
    """
    try:
        with open(doc_path, 'rb') as f:
            data = f.read()
            
        # Extract ASCII and UTF-16LE printable strings heuristically
        
        # 1. Try to find UTF-16-LE strings (Windows standard for modern Word)
        # We look for sequences of (printable byte, 0x00)
        utf16_text = ""
        import string
        printable = set(string.printable.encode('ascii'))
        
        # VERY basic heuristic. In production, tools like `textract` or `antiword` are preferred.
        def get_strings(b_data, encoding='utf-16-le'):
             try:
                  text = b_data.decode(encoding, errors='ignore')
                  # Filter out mostly garbage 
                  clean = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
                  # Return if it looks like there's actually some text
                  if len(clean) > 50:
                       return clean
             except:
                  pass
             return ""

        extracted = get_strings(data, 'utf-16-le')
        if not extracted:
            extracted = get_strings(data, 'utf-8')
            
        # Clean up excessive newlines or whitespace
        lines = [line.strip() for line in extracted.splitlines()]
        lines = [line for line in lines if line]
        
        return "\n\n".join(lines)
    except Exception:
        return ""

def extract_text(doc_path: str) -> DocExtractionResult:
    """
    Extract text from a .doc file.
    
    Tries strategies in this order:
    1. COM Interface (Requires Microsoft Word on Windows) - 100% accurate
    2. Antiword (If installed in PATH) - Good accuracy
    3. Heuristic Binary Extraction - Partial/Messy accuracy (Fallback)
    
    Args:
        doc_path: Path to the .doc file
        
    Returns:
        DocExtractionResult with full text
    """
    # Memory Management: Check file size (limit 50MB)
    MAX_SIZE = 50 * 1024 * 1024
    if os.path.exists(doc_path) and os.path.getsize(doc_path) > MAX_SIZE:
        return DocExtractionResult(
            full_text="",
            success=False,
            error="Dosya çok büyük (Limit: 50MB). Lütfen daha küçük parçalara bölün."
        )

    # Strategy 1: Windows COM (MS Word)
    error_msg = ""
    if platform.system() == 'Windows':
        try:
            import win32com.client
            abs_path = os.path.abspath(doc_path)
            
            # DispatchEx creates a new instance so we don't interfere with user's open Word docs
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
            
            try:
                doc = word.Documents.Open(abs_path, ReadOnly=True, Visible=False)
                text = doc.Content.Text
                doc.Close(False)
                
                # Word uses carriage returns (\r) instead of standard newlines (\n)
                # or sometimes \r\n, so let's normalize
                text = text.replace('\r\n', '\n').replace('\r', '\n')
                
                return DocExtractionResult(
                    full_text=text.strip(),
                    success=True
                )
            finally:
                # Safely quit the dedicated instance
                try:
                    word.Quit(False)
                except:
                    pass
        except ImportError:
            error_msg = "'pywin32' yüklü değil. "
        except Exception as e:
            error_msg = f"Word COM Hatası: {str(e)}. "

    # Strategy 2: Antiword (Cross-platform CLI tool if installed)
    antiword_text = _extract_with_antiword(doc_path)
    if antiword_text:
         return DocExtractionResult(
             full_text=antiword_text,
             success=True
         )
         
    # Strategy 3: Binary string extraction fallback
    fallback_text = _extract_fallback_strings(doc_path)
    if fallback_text and len(fallback_text) > 20: # Ensure we got *something*
         return DocExtractionResult(
             full_text=fallback_text,
             success=True,
             # Attach a warning that formatting might be lost
             error="Uyarı: Sistemde Microsoft Word bulunamadı. Metin temel düzeyde kurtarıldı, bazı bozulmalar olabilir."
         )
         
    # If all fails
    final_error = error_msg + "Sistemde Microsoft Word (Windows) veya 'antiword' aracı bulunamadığı için .doc dosyası okunamadı. Lütfen dosyayı .docx olarak kaydedip tekrar deneyin."
    return DocExtractionResult(
        full_text="",
        success=False,
        error=final_error
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
        print("Usage: python doc_processor.py <doc_file>")
