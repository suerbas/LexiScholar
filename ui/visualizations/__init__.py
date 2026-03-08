"""
Visualization Engine Sub-package for LexiScholar
Aggregates all HTML visualization generators.
"""

from .text_analytics import (
    generate_keywords_html,
    generate_word_frequency_html,
    generate_kwic_html
)

from .semantic_analytics import (
    generate_sentiment_html,
    generate_topics_html,
    generate_entities_html
)

from .project_analytics import (
    generate_document_portrait_html,
    generate_coverage_heatmap_html,
    generate_code_timeline_html,
    generate_sankey_html,
    generate_search_results_html
)

# Re-export from root visualizations package
from visualizations import (
    generate_crosstab_html,
    generate_cooccurrence_graph,
    generate_word_cloud_html,
    generate_code_matrix_html
)

from .core_utils import _generate_empty_html
