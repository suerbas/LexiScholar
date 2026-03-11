"""
NLP Analysis Actions Mixin for LexiScholar Main Window.
Keyword extraction, sentiment analysis, topic modeling, NER, KWIC, and document portrait.

This file provides backward compatibility for older imports. 
The actual implementation has been modularized and moved to ui.nlp package.
"""

from .nlp import NLPActions

__all__ = ['NLPActions']
