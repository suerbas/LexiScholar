"""
Analysis Dialogs for LexiScholar
Backwards-compatible re-exports for analysis dialogs.
All dialogs have been split into domain-specific modules.
"""

from .statistics_dialogs import (
    StatisticsDialog, 
    WordFrequencyDialog, 
    CooccurrenceDialog
)
from .code_management_dialogs import (
    CodeMergeDialog, 
    DocumentSearchDialog, 
    CrosstabDialog
)
from .variable_dialogs_ext import (
    VariableStatisticsDialog, 
    VariableStatisticsResultDialog
)
from .mixed_methods import (
    QuotesByVariablesDialog, 
    QuotesByVariablesResultWidget,
    ActivateByVariablesDialog, 
    QuoteMatrixDialog, 
    QuoteMatrixResultWidget,
    SideBySideWidget
)

__all__ = [
    'StatisticsDialog',
    'WordFrequencyDialog',
    'CooccurrenceDialog',
    'CodeMergeDialog',
    'DocumentSearchDialog',
    'CrosstabDialog',
    'VariableStatisticsDialog',
    'VariableStatisticsResultDialog',
    'QuotesByVariablesDialog',
    'QuotesByVariablesResultWidget',
    'ActivateByVariablesDialog',
    'QuoteMatrixDialog',
    'QuoteMatrixResultWidget',
    'SideBySideWidget'
]
