"""
Analysis Dialogs for LexiScholar - Statistics
UI for code statistics, word frequency, and co-occurrence analysis.

This file provides backward compatibility for older imports. 
The actual implementation has been modularized and moved to ui.statistics package.
"""

from .statistics import (
    StatisticsWidget, StatisticsDialog,
    WordFrequencyWidget, WordFrequencyDialog,
    CooccurrenceWidget, CooccurrenceDialog
)

__all__ = [
    'StatisticsWidget', 'StatisticsDialog',
    'WordFrequencyWidget', 'WordFrequencyDialog',
    'CooccurrenceWidget', 'CooccurrenceDialog'
]
