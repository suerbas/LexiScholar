"""
Coded Segments (Retrieved Segments) Analysis Dialog for LexiScholar
Modularized sub-package.
"""

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QWidget
from PyQt6.QtCore import Qt
from ..styles import COLORS
from .base import CodedSegmentsDialogBase
from .table_manager import CodedSegmentsTableMixin
from .actions_mixin import CodedSegmentsActionsMixin

class CodedSegmentsDialog(CodedSegmentsDialogBase, CodedSegmentsTableMixin, CodedSegmentsActionsMixin):
    """
    MAXQDA-style retrieved segments analysis window.
    Assembled from Base UI, Table Manager, and Actions Mixins.
    """

    def __init__(self, segments: list, code_name: str = "",
                 code_color: str = "#4F46E5", segment_dao=None,
                 command_stack=None, parent=None):
        super().__init__(segments, code_name, code_color, parent)
        self._segment_dao = segment_dao
        self._command_stack = command_stack

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        self._setup_base_ui()

    def _build_header(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("headerBar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Code color indicator
        circle = QLabel()
        circle.setFixedSize(14, 14)
        circle.setStyleSheet(f"background-color:{self._code_color}; border-radius:7px;")
        layout.addWidget(circle)

        title = QLabel(
            f"<b style='font-size:12pt;color:{COLORS['text_primary']};'>Kodlanmış Bölümler</b>"
            f"&nbsp;&nbsp;<span style='color:{COLORS['text_muted']};font-size:10pt;'>— {self._code_name}</span>"
        )
        title.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(title)
        layout.addStretch()

        self.lbl_count = QLabel("0 segment")
        self.lbl_count.setObjectName("countBadge")
        layout.addWidget(self.lbl_count)

        btn_wordcloud = QPushButton("☁️ Kelime Bulutu")
        btn_wordcloud.setObjectName("toolBtn")
        btn_wordcloud.clicked.connect(self._show_word_cloud)
        layout.addWidget(btn_wordcloud)

        btn_export = QPushButton("📥 Excel'e Aktar")
        btn_export.setObjectName("primaryBtn")
        btn_export.clicked.connect(self._export_to_excel)
        layout.addWidget(btn_export)

        return bar

    def _update_preview(self, seg: dict):
        """Seçili segmentin tam metnini önizleme alanında göster."""
        full_text = (seg.get("segment_text", "") or "").strip()
        doc_title  = seg.get("document_title", "") or "Belge"
        code_name  = seg.get("code_name", "") or self._code_name
        weight     = seg.get("weight", 0)
        start_pos  = seg.get("start_pos", 0)
        end_pos    = seg.get("end_pos", 0)
        color      = self._code_color
        paraphrase = (seg.get("paraphrase") or "").strip()

        para_html = ""
        if paraphrase:
            para_html = (
                f"<div style='margin:10px 0 8px 0; padding:8px 14px;"
                f" background:#FFFBEB; border-left:4px solid #F59E0B;"
                f" border-radius:5px;'>"
                f"<span style='font-size:8pt; font-weight:700; color:#92400E; "
                f"letter-spacing:0.5px;'>✍️ PARAFRAZE</span><br>"
                f"<span style='font-size:10pt; color:#1E293B;'>{paraphrase}</span>"
                f"</div>"
            )

        html = (
            f"<div style='margin-bottom:10px;'>"
            f"<span style='display:inline-block; background:{color}22; "
            f"border-left:4px solid {color}; padding:3px 8px; border-radius:3px;"
            f"font-size:9pt; font-weight:700; color:{color};'>"
            f"🏷️ {code_name}</span>"
            f"&nbsp;&nbsp;"
            f"<span style='color:{COLORS['text_muted']};font-size:9pt;'>"
            f"📄 {doc_title} &nbsp;|&nbsp; "
            f"Pos {start_pos}–{end_pos} &nbsp;|&nbsp; "
            f"{weight} ⭐"
            f"</span>"
            f"</div>"
            f"{para_html}"
            f"<div style='font-size:11pt; line-height:1.4; color:{COLORS['text_primary']}; white-space:pre-wrap;'>"
            f"{full_text}"
            f"</div>"
        )
        self.preview_edit.setHtml(html)
        self.lbl_status.setText(f"📄 {doc_title}  ·  Karakter: {start_pos}–{end_pos}  ·  Ağırlık: {weight} ⭐")

    @staticmethod
    def open_for_code(segment_dao, code_id: int, code_name: str,
                       code_color: str = "#4F46E5", parent=None) -> "CodedSegmentsDialog":
        segments = segment_dao.get_by_code(code_id)
        dlg = CodedSegmentsDialog(segments, code_name, code_color, segment_dao=segment_dao, parent=parent)
        return dlg
