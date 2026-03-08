"""Document processors module for LexiScholar."""
from pathlib import Path
from .pdf_processor import extract_text_with_positions as extract_pdf
from .docx_processor import extract_text as extract_docx
from .doc_processor import extract_text as extract_doc
from .txt_processor import extract_text as extract_txt
from .rtf_processor import extract_text as extract_rtf
from .excel_processor import extract_text as extract_excel
from .odt_processor import extract_text as extract_odt
from .spss_processor import extract_text as extract_spss


def extract_text(file_path: str) -> str:
    """
    Extract text from a document file. Detects file type and uses the appropriate extractor.
    Raises Exception on failure with a clear error message.
    """
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        result = extract_pdf(file_path)
    elif ext == '.docx':
        result = extract_docx(file_path)
    elif ext == '.doc':
        result = extract_doc(file_path)
    elif ext == '.txt':
        result = extract_txt(file_path)
    elif ext == '.rtf':
        result = extract_rtf(file_path)
    elif ext in ['.xls', '.xlsx']:
        result = extract_excel(file_path)
    elif ext == '.odt':
        result = extract_odt(file_path)
    elif ext == '.sav':
        result = extract_spss(file_path)
    else:
        raise ValueError(f"Desteklenmeyen dosya formatı: {ext}")
        
    if not result.success:
        error_msg = result.error or "Bilinmeyen bir hata oluştu."
        raise Exception(f"Metin çıkarma başarısız oldu: {error_msg}")
        
    return result.full_text


__all__ = ['extract_pdf', 'extract_docx', 'extract_doc', 'extract_txt', 'extract_rtf', 'extract_excel', 'extract_text']

