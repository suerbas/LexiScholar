"""
Table Management and Population for Coded Segments Dialog
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from .base import COLUMNS
from ..styles import COLORS

class CodedSegmentsTableMixin:
    """Handles QTableWidget setup and data population for segments."""

    def _build_table_panel(self):
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table_strip = QLabel("  📊  KODLANMIŞ BÖLÜMLER TABLOSU")
        self.table_strip.setStyleSheet(
            f"background-color:{COLORS['primary_50']}; color:{COLORS['text_secondary']}; "
            f"font-size:8pt; font-weight:700; padding:6px 12px; border-bottom:1px solid {COLORS['border']};"
        )
        layout.addWidget(self.table_strip)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in COLUMNS])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(True)

        hdr = self.table.horizontalHeader()
        for i, (_, width) in enumerate(COLUMNS):
            self.table.setColumnWidth(i, width)
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(34)

        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)

        layout.addWidget(self.table)
        return container

    def _on_row_selected(self):
        """Handle row selection to update preview."""
        items = self.table.selectedItems()
        if not items: return
        row = items[0].row()
        item = self.table.item(row, 0)
        if item:
            seg = item.data(Qt.ItemDataRole.UserRole)
            if hasattr(self, '_update_preview'):
                self._update_preview(seg)

    def _on_row_double_clicked(self, row, col):
        """Handle double click to navigate."""
        item = self.table.item(row, 0)
        if item:
            seg = item.data(Qt.ItemDataRole.UserRole)
            if seg:
                # Emit signal defined in base class
                self.segment_navigate_requested.emit(seg.get('document_id'), seg.get('id'))

    def _populate_table(self):
        segs = self._segments
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.table.setRowCount(len(segs))

        color = QColor(self._code_color)
        color.setAlpha(40)

        for row, seg in enumerate(segs):
            doc_title = seg.get("document_title", "") or "—"
            code_name = seg.get("code_name", "") or self._code_name
            start_pos = seg.get("start_pos", 0)
            end_pos   = seg.get("end_pos", 0)
            weight    = seg.get("weight", 0)
            seg_text  = (seg.get("segment_text", "") or "").strip()
            comment   = seg.get("comment", "") or ""
            paraphrase = seg.get("paraphrase", "") or ""
            folder_name = seg.get("folder_name", "")
            doc_group = folder_name if folder_name else "—"

            preview_short = (seg_text[:120] + "…") if len(seg_text) > 120 else seg_text
            para_short    = (paraphrase[:80] + "…") if len(paraphrase) > 80 else paraphrase

            cells = [comment, doc_group, doc_title, code_name, str(start_pos), str(end_pos), self._weight_stars(weight), para_short, preview_short]

            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                if col == self.COL_WEIGHT:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                elif col in (self.COL_START, self.COL_END):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)

            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, seg)
            doc_item = self.table.item(row, self.COL_DOC_NAME)
            if doc_item:
                doc_item.setBackground(color)

        self.table.setSortingEnabled(True)
        count = len(segs)
        self.lbl_count.setText(f"{count} segment" if count != 1 else "1 segment")
        self.table_strip.setText(f"  📊  KODLANMIŞ BÖLÜMLER TABLOSU — {count} kayıt")

    @staticmethod
    def _weight_stars(weight: int) -> str:
        try:
            w = max(1, min(5, int(weight)))
            return f"{w} ⭐"
        except (TypeError, ValueError):
            return "—"
