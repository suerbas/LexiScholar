"""
NLP Analysis Actions module.
Aggregates various NLP actions to be used as a mixin for the MainWindow.
"""

from .base_actions import NLPBaseMixin, _get_available_ram_mb, _check_ram_before_nlp
from .keyword_actions import KeywordActionsMixin
from .sentiment_actions import SentimentActionsMixin
from .topic_actions import TopicActionsMixin
from .entity_actions import EntityActionsMixin
from .synthesis_actions import SynthesisActionsMixin
from .text_analysis import TextAnalysisMixin

class NLPActions(
    NLPBaseMixin,
    KeywordActionsMixin,
    SentimentActionsMixin,
    TopicActionsMixin,
    EntityActionsMixin,
    SynthesisActionsMixin,
    TextAnalysisMixin
):
    """
    Mixin class providing NLP analysis methods for MainWindow.
    This class combines various modular NLP actions into a single interface.
    """
    pass
