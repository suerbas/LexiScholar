"""
LexiScholar Visualizations Package.
Exposes all visualization generators for backward compatibility.
"""

from .cooccurrence import generate_cooccurrence_graph
from .word_cloud import generate_word_cloud_html
from .code_matrix import generate_code_matrix_html
from .crosstab import generate_crosstab_html

__all__ = [
    'generate_cooccurrence_graph',
    'generate_word_cloud_html',
    'generate_code_matrix_html',
    'generate_crosstab_html',
    'generate_keywords_html',
    'generate_kwic_html',
    'generate_document_portrait_html',
    'generate_sankey_html'
]

from .simple_reports import (
    generate_keywords_html,
    generate_kwic_html,
    generate_document_portrait_html,
    generate_sankey_html,
)
