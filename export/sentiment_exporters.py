"""
Sentiment Analysis Export Module
Provides Excel, Word, and HTML export for sentiment analysis results.

Note: This module is maintained for backward compatibility.
Implementation logic has been moved to the `export.sentiment` package.
"""

from typing import List, Dict

from .sentiment.excel import export_sentiment_to_excel, export_hybrid_sentiment_to_excel
from .sentiment.word import export_sentiment_to_word, export_hybrid_sentiment_to_word
from .sentiment.html import export_sentiment_to_html, export_hybrid_sentiment_to_html

def get_sentiment_export_formats() -> List[Dict]:
    """Return available export formats for sentiment analysis."""
    formats = [
        {
            'name': 'Excel Belgesi',
            'extension': 'xlsx',
            'filter': 'Excel Dosyaları (*.xlsx)',
            'description': 'Yapılandırılmış tablo formatında export'
        },
        {
            'name': 'Word Belgesi',
            'extension': 'docx',
            'filter': 'Word Belgeleri (*.docx)',
            'description': 'Akademik rapor formatında export'
        },
        {
            'name': 'HTML Rapor',
            'extension': 'html',
            'filter': 'HTML Dosyaları (*.html)',
            'description': 'Web tarayıcısında görüntülenebilir rapor'
        },
        {
            'name': 'JSON Verisi',
            'extension': 'json',
            'filter': 'JSON Dosyaları (*.json)',
            'description': 'Programatik analiz için ham veri'
        }
    ]
    return formats
