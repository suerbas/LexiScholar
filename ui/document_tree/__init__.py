"""
Document Tree Sub-package for LexiScholar
Decomposed into base, actions_mixin, model_populator, and menu_builder.
"""

from .base import DocumentTreeBase
from .actions_mixin import DocumentTreeActionsMixin
from .model_populator import DocumentTreeModelPopulatorMixin
from .menu_builder import DocumentTreeMenuMixin

class DocumentTree(DocumentTreeBase, DocumentTreeActionsMixin, DocumentTreeModelPopulatorMixin, DocumentTreeMenuMixin):
    """
    Tree view showing imported documents organized in folders.
    Assembled from multiple mixins for better maintainability.
    """
    def __init__(self, parent=None, doc_dao=None, folder_dao=None):
        # Initializing the base class
        super().__init__(parent, doc_dao, folder_dao)

    def set_daos(self, doc_dao, folder_dao):
        """Update DAOs and refresh tree."""
        self.doc_dao = doc_dao
        self.folder_dao = folder_dao
        # Optional logging can go here or be moved to a logger utility
        self._refresh_data()
