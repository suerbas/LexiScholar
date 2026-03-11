"""
Statistics UI views and logic for LexiScholar.
"""

from .code_stats import StatisticsWidget, StatisticsDialog
from .word_freq import WordFrequencyWidget, WordFrequencyDialog
from .cooccurrence import CooccurrenceWidget, CooccurrenceDialog

__all__ = [
    'StatisticsWidget', 'StatisticsDialog',
    'WordFrequencyWidget', 'WordFrequencyDialog',
    'CooccurrenceWidget', 'CooccurrenceDialog'
]
