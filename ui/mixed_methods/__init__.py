"""
Mixed Methods sub-package for LexiScholar.
"""

from .quotes_by_variables import QuotesByVariablesDialog, QuotesByVariablesResultWidget
from .activation import ActivateByVariablesDialog
from .quote_matrix import QuoteMatrixDialog, QuoteMatrixResultWidget
from .side_by_side import SideBySideWidget
from .variance_analysis import VarianceAnalysisDialog, VarianceResultWidget

__all__ = [
    'QuotesByVariablesDialog',
    'QuotesByVariablesResultWidget',
    'ActivateByVariablesDialog',
    'QuoteMatrixDialog',
    'QuoteMatrixResultWidget',
    'SideBySideWidget',
    'VarianceAnalysisDialog',
    'VarianceResultWidget'
]
