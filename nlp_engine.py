"""
Facade for the refactored nlp package.
This file is kept for backward compatibility so existing imports don't break.
"""

from nlp import *
from nlp.tasks.ner import _aggregate_entity_documents
import logging

logger = logging.getLogger(__name__)

# Backward compatibility alias
_hf_pipelines_enabled = hf_pipelines_enabled

