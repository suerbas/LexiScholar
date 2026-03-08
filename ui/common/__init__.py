"""
Common UI components for LexiScholar.
"""

from .memos import MemoDialog
from .coding_helpers import QuickCodeDialog, WeightDialog
from .message_boxes import ScrollableMessageBox
from .segment_card import ModernSegmentCard
from .browser_dialog import BrowserDialog

__all__ = [
    'MemoDialog',
    'QuickCodeDialog',
    'WeightDialog',
    'ScrollableMessageBox',
    'ModernSegmentCard',
    'BrowserDialog'
]
