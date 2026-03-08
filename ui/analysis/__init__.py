"""
Analysis Actions sub-package for LexiScholar.
Assembled from modular functional mixins.
"""

from .search import SearchActionsMixin
from .stats import StatsActionsMixin
from .visuals import VisualsActionsMixin
from .mixed_methods import MixedMethodsActionsMixin
from .workspace import WorkspaceActionsMixin

class AnalysisActions(
    SearchActionsMixin, 
    StatsActionsMixin, 
    VisualsActionsMixin, 
    MixedMethodsActionsMixin, 
    WorkspaceActionsMixin
):
    """
    Mixin class providing a unified analysis interface for MainWindow.
    Decomposed from a monolithic class into functional components.
    """
    pass
