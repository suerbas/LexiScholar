"""
SPSS Processor for LexiScholar
Extracts and formats data from SPSS files (.sav).
"""

from dataclasses import dataclass
from typing import Optional, List

try:
    import pyreadstat
    PYREADSTAT_AVAILABLE = True
except ImportError:
    PYREADSTAT_AVAILABLE = False


@dataclass
class SPSSExtractionResult:
    """Result of SPSS data extraction."""
    full_text: str
    row_count: int
    column_count: int
    success: bool
    error: Optional[str] = None


def extract_text(sav_path: str) -> SPSSExtractionResult:
    """
    Extract data from an SPSS (.sav) file and format it as text.
    
    Args:
        sav_path: Path to the .sav file
        
    Returns:
        SPSSExtractionResult with formatted text representation
    """
    if not PYREADSTAT_AVAILABLE:
        return SPSSExtractionResult(
            full_text="",
            row_count=0,
            column_count=0,
            success=False,
            error="pyreadstat kütüphanesi yüklü değil. Lütfen yükleyin: pip install pyreadstat"
        )
    
    try:
        import pandas as pd
        # Load SPSS file
        df, meta = pyreadstat.read_sav(sav_path)
        
        all_text = []
        all_text.append(f"📊 SPSS VERİ SETİ: {sav_path}")
        all_text.append(f"Sütun Sayısı: {len(df.columns)}")
        all_text.append(f"Satır Sayısı: {len(df)}")
        all_text.append(f"{'='*60}\n")
        
        # Add Variable Labels as a header section
        all_text.append("📋 DEĞİŞKEN TANIMLARI")
        for col_name in df.columns:
            label = meta.column_names_to_labels.get(col_name, "Etiket yok")
            all_text.append(f"- {col_name}: {label}")
        all_text.append(f"\n{'='*60}\n")
        
        # Add Data rows (Formatted as text)
        all_text.append("📝 VERİ KAYITLARI")
        # Header row
        header = " | ".join(df.columns)
        all_text.append(header)
        all_text.append("-" * len(header))
        
        # Data rows (limit to 1000 rows to prevent extreme file sizes in UI)
        max_rows = 1000
        for i, (idx, row) in enumerate(df.iterrows()):
            if i >= max_rows:
                all_text.append(f"\n[... {len(df) - max_rows} satır daha mevcut, performans için sınırlandırıldı ...]")
                break
            
            row_values = []
            for col in df.columns:
                val = row[col]
                # Try to map value labels if they exist
                if col in meta.variable_to_label:
                    # pyreadstat handles labels differently, usually metadata contains variable_value_labels
                    pass # Values are already processed in df usually or needs manual mapping
                
                row_values.append(str(val))
            
            all_text.append(" | ".join(row_values))
            
        return SPSSExtractionResult(
            full_text="\n".join(all_text),
            row_count=len(df),
            column_count=len(df.columns),
            success=True
        )
        
    except FileNotFoundError:
        return SPSSExtractionResult(
            full_text="",
            row_count=0,
            column_count=0,
            success=False,
            error="Dosya bulunamadı."
        )
    except Exception as e:
        return SPSSExtractionResult(
            full_text="",
            row_count=0,
            column_count=0,
            success=False,
            error=str(e)
        )


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = extract_text(sys.argv[1])
        if result.success:
            print(f"Rows: {result.row_count}, Cols: {result.column_count}")
            print("\n--- First 1000 characters ---")
            print(result.full_text[:1000])
        else:
            print(f"Error: {result.error}")
    else:
        print("Usage: python spss_processor.py <sav_file>")
