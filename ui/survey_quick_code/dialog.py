"""
Survey Quick Code Dialog — LexiScholar
MAXQDA-style "Anket Verisini Kategorilere Ayır" window.
Shows all answers to a coded survey question in a 3-column layout and allows
quick sub-code assignment by selecting text within any answer.
"""

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLabel, QToolBar, QPushButton, QTextEdit, QFrame, QMenu,
    QScrollArea, QMessageBox, QSizePolicy, QToolButton, QInputDialog, QColorDialog,
    QApplication, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QTextCursor, QTextCharFormat, QAction, QDesktopServices

# --- Imports adjusted for new location (ui/survey_quick_code/dialog.py) ---
from ..styles import COLORS, CONTEXT_MENU_STYLE, get_color
from ..common.modern_dialog import ModernBaseDialog
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class AnswerBlock(QFrame):
    """
    A single answer block — shows the participant ID / document name as a header
    and the full answer text as an editable (read-only) QTextEdit so the user
    can select text to assign a sub-code.
    """
    text_selected = pyqtSignal(str, int, dict)   # selected_text, block_index, segment_info

    def __init__(self, segment: dict, block_index: int, parent=None):
        super().__init__(parent)
        self._segment = segment
        self._block_index = block_index
        self._code_color = get_color('primary')
        self._badges_layout = None   # set during _setup_ui
        self._setup_ui()

    # ── UI Setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)

        self.setStyleSheet(f"""
            AnswerBlock {{
                border: 1px solid {get_color('border')};
                border-radius: 8px;
                background-color: {get_color('bg_panel')};
                margin-bottom: 8px;
            }}
        """)

        # — Header row (document name + position) ————————————
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {get_color('primary_50')};
            border-bottom: 1px solid {get_color('border')};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 6, 10, 6)
        h_layout.setSpacing(12)

        doc_label = QLabel(f"📄 {self._segment.get('document_title', '—')}")
        doc_label.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {get_color('text_primary')};")
        h_layout.addWidget(doc_label)

        folder_label = QLabel(self._segment.get('folder_name', '') or '')
        folder_label.setStyleSheet(f"font-size: 11px; color: {get_color('text_secondary')};")
        h_layout.addWidget(folder_label)

        h_layout.addStretch()

        pos_lbl = QLabel(
            f"Konum {self._segment.get('start_pos', '')}–{self._segment.get('end_pos', '')}"
        )
        pos_lbl.setStyleSheet(f"font-size: 11px; color: {get_color('text_muted')};")
        h_layout.addWidget(pos_lbl)

        layout.addWidget(header)

        # — Text Area ———————————————————————————————————————————
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        raw_text = (self._segment.get("segment_text") or "").strip()
        self.text_edit.setPlainText(raw_text)

        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                background-color: {get_color('bg_panel')};
                padding: 10px 14px;
                font-size: 13px;
                color: {get_color('text_primary')};
                line-height: 1.7;
            }}
        """)

        # Dynamic height (min 60, capped at 220)
        doc_height = min(220, max(60, raw_text.count('\n') * 22 + 80))
        self.text_edit.setFixedHeight(doc_height)

        self.text_edit.selectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.text_edit)

        # — Code Badges Footer ———————————————————————
        self._badges_footer = QWidget()
        self._badges_footer.setStyleSheet(
            f"background-color: {get_color('bg_panel')};"
            f"border-top: 1px solid {get_color('border')};"
            "border-bottom-left-radius: 8px;"
            "border-bottom-right-radius: 8px;"
        )
        badges_row = QHBoxLayout(self._badges_footer)
        badges_row.setContentsMargins(10, 5, 10, 5)
        badges_row.setSpacing(6)

        lbl_kodlar = QLabel("🏷 Kodlar:")
        lbl_kodlar.setStyleSheet(f"font-size: 10px; color: {get_color('text_muted')}; font-weight: 600;")
        badges_row.addWidget(lbl_kodlar)

        # Inner badges area (wrappable)
        self._badges_inner = QWidget()
        self._badges_layout = QHBoxLayout(self._badges_inner)
        self._badges_layout.setContentsMargins(0, 0, 0, 0)
        self._badges_layout.setSpacing(4)
        self._badges_layout.addStretch()
        badges_row.addWidget(self._badges_inner)
        badges_row.addStretch()

        self._badges_footer.setFixedHeight(32)
        layout.addWidget(self._badges_footer)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _on_selection_changed(self):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText().strip()
            if selected:
                self.text_selected.emit(selected, self._block_index, self._segment)

    def add_code_badge(self, code_name: str, code_color: str):
        """Append a colored pill badge for a code that was just assigned to this block."""
        if self._badges_layout is None:
            return
        pill = QLabel(f"  {code_name}  ")
        pill.setStyleSheet(f"""
            QLabel {{
                background-color: {code_color}22;
                color: {code_color};
                border: 1px solid {code_color}66;
                border-radius: 9px;
                font-size: 10px;
                font-weight: 700;
                padding: 1px 6px;
            }}
        """)
        # Insert before the trailing stretch
        count = self._badges_layout.count()
        self._badges_layout.insertWidget(count - 1, pill)

    def highlight_coded_text(self, color: str):
        """Highlight the entire text block with the given code color."""
        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        bg = QColor(color)
        bg.setAlpha(40)
        fmt.setBackground(bg)
        cursor.mergeCharFormat(fmt)

    def get_selected_text(self) -> str:
        return self.text_edit.textCursor().selectedText().strip()


# ─────────────────────────────────────────────────────────────────────────────
# Main Dialog
# ─────────────────────────────────────────────────────────────────────────────

class SurveyQuickCodeDialog(ModernBaseDialog):
    """
    MAXQDA-style 'Anket Verisini Kategorilere Ayır' (Survey Quick Coding) dialog.

    Layout (3 panels):
      LEFT  │ CENTRE (answers scroll)  │ RIGHT (code list + actions)
    """
    # Emitted when user assigns a new sub-code inside this dialog
    sub_code_assigned = pyqtSignal(int, int, str, int)   # doc_id, seg_idx, text, code_id
    sub_code_created = pyqtSignal(str, str, int, str)    # name, color, parent_id, desc

    def __init__(
        self,
        segments: list,
        code_name: str,
        code_id: int,
        code_color: str = None,
        all_codes: list = None,
        segment_dao=None,
        parent=None,
    ):
        if code_color is None:
            code_color = get_color('primary')
        super().__init__(parent, min_width=1100, min_height=750)
        self._segments = segments
        self._code_name = code_name
        self._code_id = code_id
        self._code_color = code_color
        self._all_codes = all_codes or []
        self._segment_dao = segment_dao
        self._selected_text = ""
        self._selected_segment = None
        self._answer_blocks: list[AnswerBlock] = []

        self.setModal(False) 
        self._setup_ui()
        self._populate_answers()

    # ── UI Setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self._setup_base_ui()
        
        # Header Area
        header_layout = QHBoxLayout()
        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)

        title = QLabel(f"Anket Verisini Kategorilere Ayır — {self._code_name}")
        title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {get_color('text_primary')};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Red X Close Button
        close_btn_top = QPushButton("✕")
        close_btn_top.setFixedSize(32, 32)
        close_btn_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_top.clicked.connect(self.close)
        close_btn_top.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {get_color('text_secondary')}; font-size: 18px; font-weight: bold; border: none; border-radius: 16px; }}
            QPushButton:hover {{ background: {get_color('error_bg')}; color: {get_color('error')}; }}
        """)
        header_layout.addWidget(close_btn_top)
        self.layout.addLayout(header_layout)

        # ── Top Toolbar ───────────────────────────────────────────────────────
        toolbar = self._build_toolbar()
        self.layout.addWidget(toolbar)

        # ── Main Splitter ─────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {get_color('border')}; }}")

        # LEFT: Info panel (code info + stats)
        left = self._build_info_panel()
        splitter.addWidget(left)

        # CENTRE: Answers
        centre = self._build_answers_panel()
        splitter.addWidget(centre)

        # RIGHT: Quick-code panel
        right = self._build_code_panel()
        splitter.addWidget(right)

        splitter.setSizes([220, 520, 360])
        self.layout.addWidget(splitter)
        # ── Status Bar ────────────────────────────────────────────────────────
        footer_layout = QHBoxLayout()
        self._status_bar = QLabel(f"  ✂️ Metinden seçim yapın → Sağ panelden kod atayın   |   Toplam: {len(self._segments)} yanıt")
        self._status_bar.setStyleSheet(f"""
            color: {get_color('text_secondary')};
            font-size: 11px;
            font-weight: 600;
        """)
        footer_layout.addWidget(self._status_bar)
        footer_layout.addStretch()
        self.layout.addLayout(footer_layout)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"""
            background-color: {get_color('bg_panel')};
            border-bottom: 1px solid {get_color('border')};
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Title
        title_lbl = QLabel(f"<b>📊 {self._code_name}</b>")
        title_lbl.setStyleSheet(f"font-size: 14px; color: {self._code_color};")
        layout.addWidget(title_lbl)

        count_lbl = QLabel(f"  {len(self._segments)} yanıt")
        count_lbl.setStyleSheet(f"font-size: 12px; color: {get_color('text_muted')}; border: 1px solid {get_color('border')}; border-radius: 10px; padding: 1px 8px;")
        layout.addWidget(count_lbl)

        layout.addStretch()

        # Word Cloud button
        btn_wc = QPushButton("☁️ Kelime Bulutu")
        btn_wc.setStyleSheet(self._tool_btn_style())
        btn_wc.clicked.connect(self._show_word_cloud)
        layout.addWidget(btn_wc)

        # AI Summarize
        btn_ai = QPushButton("🤖 AI Özet")
        btn_ai.setStyleSheet(self._tool_btn_style(get_color('info_bg'), get_color('info')))
        btn_ai.clicked.connect(self._ai_summarize)
        layout.addWidget(btn_ai)

        return bar

    def _build_info_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(180)
        panel.setMaximumWidth(240)
        panel.setStyleSheet(f"background-color: {get_color('bg_panel')}; border-right: 1px solid {get_color('border')};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Code color swatch
        swatch = QLabel()
        swatch.setFixedSize(36, 36)
        swatch.setStyleSheet(f"background-color: {self._code_color}; border-radius: 18px;")
        layout.addWidget(swatch, alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(self._code_name)
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {get_color('text_primary')};")
        layout.addWidget(title)

        # stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"background-color: {get_color('bg_panel')}; border: 1px solid {get_color('border')}; border-radius: 8px; padding: 8px;")
        sf_layout = QVBoxLayout(stats_frame)
        sf_layout.setSpacing(4)
        sf_layout.setContentsMargins(8, 8, 8, 8)

        total_chars = sum(len((s.get("segment_text") or "")) for s in self._segments)
        for label, value in [
            ("Yanıt Sayısı", str(len(self._segments))),
            ("Toplam Karakter", f"{total_chars:,}"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 11px; color: {get_color('text_secondary')};")
            val = QLabel(value)
            val.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {self._code_color};")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            sf_layout.addLayout(row)

        layout.addWidget(stats_frame)
        layout.addStretch()

        # Hint
        hint = QLabel("💡 Cevap metninden bir bölüm seçin, ardından sağdaki kodlardan birini tıklayın.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"font-size: 10px; color: {get_color('text_muted')}; line-height: 1.4;")
        layout.addWidget(hint)

        return panel

    def _build_answers_panel(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header strip
        strip = QLabel("   📝  KATILIMCI CEVAPLARI")
        strip.setFixedHeight(30)
        strip.setStyleSheet(f"""
            background-color: {get_color('primary_50')};
            color: {get_color('text_secondary')};
            font-size: 8pt; font-weight: 700; letter-spacing: 0.5px;
            padding: 6px 12px;
            border-bottom: 1px solid {get_color('border')};
        """)
        layout.addWidget(strip)

        # Scrollable answer blocks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._answers_container = QWidget()
        self._answers_layout = QVBoxLayout(self._answers_container)
        self._answers_layout.setContentsMargins(12, 12, 12, 12)
        self._answers_layout.setSpacing(12)
        self._answers_layout.addStretch()

        scroll.setWidget(self._answers_container)
        layout.addWidget(scroll)

        return wrapper

    def _build_code_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(200)
        panel.setMaximumWidth(600)
        panel.setStyleSheet(f"background-color: {get_color('bg_panel')}; border-left: 1px solid {get_color('border')};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        strip = QLabel("   🏷  KODLAR")
        strip.setFixedHeight(30)
        strip.setStyleSheet(f"""
            background-color: {get_color('primary_50')};
            color: {get_color('text_secondary')};
            font-size: 8pt; font-weight: 700; letter-spacing: 0.5px;
            padding: 6px 12px;
            border-bottom: 1px solid {get_color('border')};
        """)
        layout.addWidget(strip)

        # "Selected Text" preview
        self._sel_preview = QLabel("(Metin seçimi yok)")
        self._sel_preview.setWordWrap(True)
        self._sel_preview.setStyleSheet(f"""
            font-size: 11px; font-style: italic; color: {get_color('text_muted')};
            padding: 8px 12px;
            border-bottom: 1px solid {get_color('bg_hover')};
        """)
        self._sel_preview.setFixedHeight(60)
        layout.addWidget(self._sel_preview)

        # Code buttons (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._code_list_widget = QWidget()
        self._code_list_layout = QVBoxLayout(self._code_list_widget)
        self._code_list_layout.setContentsMargins(8, 8, 8, 8)
        self._code_list_layout.setSpacing(4)
        self._code_list_layout.addStretch()

        scroll.setWidget(self._code_list_widget)
        layout.addWidget(scroll)

        # "New sub-code" button at bottom
        btn_new = QPushButton("＋ Yeni Alt Kod Oluştur")
        btn_new.setStyleSheet(f"""
            QPushButton {{
                margin: 8px;
                background-color: {self._code_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {get_color('primary_dark')}; }}
        """)
        btn_new.clicked.connect(self._create_subcode)
        layout.addWidget(btn_new)

        return panel

    # ── Populate ──────────────────────────────────────────────────────────────

    def _populate_answers(self):
        """Build AnswerBlock widgets and populate the code list."""
        # Clear old blocks
        while self._answers_layout.count() > 1:
            item = self._answers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, seg in enumerate(self._segments):
            block = AnswerBlock(seg, idx, self._answers_container)
            block.text_selected.connect(self._on_text_selected)
            self._answer_blocks.append(block)
            self._answers_layout.insertWidget(idx, block)

        # Populate code list
        self._refresh_code_list()

    def _refresh_code_list(self):
        """Rebuild the quick-code button panel from all_codes."""
        while self._code_list_layout.count() > 1:
            item = self._code_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for code in self._all_codes:
            btn = QPushButton(f"● {code['name']}")
            c = code.get('color', get_color('primary'))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {get_color('bg_panel')};
                    color: {c};
                    border: 1.5px solid {c};
                    border-radius: 6px;
                    padding: 7px 10px;
                    font-size: 12px;
                    font-weight: 600;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {c}18;
                }}
            """)
            btn.setToolTip(f"Seçili metni '{code['name']}' olarak kodla")
            btn.clicked.connect(lambda checked, co=code: self._assign_code(co))
            self._code_list_layout.insertWidget(self._code_list_layout.count() - 1, btn)

    # ── Event Handlers ────────────────────────────────────────────────────────

    def _on_text_selected(self, text: str, block_idx: int, segment: dict):
        self._selected_text = text
        self._selected_segment = segment
        preview = text[:80] + ("…" if len(text) > 80 else "")
        self._sel_preview.setText(f'"{preview}"')
        self._sel_preview.setStyleSheet(f"""
            font-size: 11px; font-style: italic; color: {get_color('text_primary')};
            background-color: {get_color('warning_bg')};
            padding: 8px 12px;
            border-bottom: 1px solid {get_color('warning')};
        """)
        self._status_bar.setText(f"  ✂️ Seçili: {len(text)} karakter  |  Sağdaki kodlardan birini tıklayın →")

    def _assign_code(self, code: dict):
        if not self._selected_text:
            show_info(self, "Seçim Yok",
                "Lütfen önce bir cevap metninden bir bölüm seçin.")
            return

        seg = self._selected_segment
        if not seg:
            return

        doc_id = seg.get("document_id")
        code_id = code.get("id")

        if self._segment_dao and doc_id and code_id:
            try:
                # Find the approximate start/end within the document by searching the text
                doc_text = seg.get("segment_text", "")
                rel_start = doc_text.find(self._selected_text)
                if rel_start < 0:
                    rel_start = 0
                abs_start = seg.get("start_pos", 0) + rel_start
                abs_end = abs_start + len(self._selected_text)

                self._segment_dao.add(
                    doc_id,
                    code_id,
                    abs_start,
                    abs_end,
                    self._selected_text,
                )
                self.sub_code_assigned.emit(doc_id, 0, self._selected_text, code_id)

                # Add badge to the answer block that was selected
                target_block = next(
                    (b for b in self._answer_blocks if b._segment is seg),
                    None
                )
                if target_block:
                    target_block.add_code_badge(code['name'], code.get('color', get_color('primary')))

                self._status_bar.setText(
                    f"  ✅ '{self._selected_text[:40]}…' → '{code['name']}' olarak kodlandı"
                )

                # Flash the status bar green momentarily
                self._status_bar.setStyleSheet(f"""
                    background-color: {get_color('success_bg')};
                    border-top: 1px solid {get_color('success')};
                    color: {get_color('success')};
                    font-size: 11px;
                    padding: 5px 16px;
                """)
                QTimer.singleShot(2000, self._reset_status_style)

                # Clear selection + reset
                self._selected_text = ""
                self._selected_segment = None
                self._sel_preview.setText("(Metin seçimi yok)")
                self._sel_preview.setStyleSheet(f"""
                    font-size: 11px; font-style: italic; color: {get_color('text_muted')};
                    padding: 8px 12px;
                    border-bottom: 1px solid {get_color('bg_hover')};
                """)

            except Exception as e:
                show_error(self, "Kodlama Hatası", str(e))
        else:
            show_warning(self, "Uyarı", "Segment DAO bağlı değil veya segment bilgisi eksik.")

    def _reset_status_style(self):
        self._status_bar.setStyleSheet(f"""
            background-color: {get_color('bg_panel')};
            border-top: 1px solid {get_color('border')};
            color: {get_color('text_secondary')};
            font-size: 11px;
            padding: 5px 16px;
        """)
        self._status_bar.setText(f"  ✂️ Metinden seçim yapın → Sağ panelden kod atayın   |   Toplam: {len(self._segments)} yanıt")

    def _create_subcode(self):
        from ..modern_dialogs import ModernInputDialog
        name, ok = ModernInputDialog.get_input(self, "Yeni Alt Kod", f"'{self._code_name}' altında yeni alt kod adı:")
        if ok and name.strip():
            color = QColorDialog.getColor(QColor(self._code_color), self, "Alt Kod Rengi")
            chosen_color = color.name() if color.isValid() else self._code_color
            self.sub_code_created.emit(name.strip(), chosen_color, self._code_id, "")
            # Optimistcally add to our list
            self._all_codes.append({"id": None, "name": name.strip(), "color": chosen_color})
            self._refresh_code_list()

    # ── Word Cloud / AI ───────────────────────────────────────────────────────

    def _show_word_cloud(self):
        from collections import Counter
        import re
        try:
            from visualizations.word_cloud import generate_word_cloud_html
        except ImportError:
            show_warning(self, "Hata", "Kelime bulutu modülü bulunamadı.")
            return

        try:
            from analysis.analysis_tools import STOP_WORDS
        except ImportError:
            STOP_WORDS = set()

        counter = Counter()
        # Fix regex to support Turkish characters properly and find words
        pattern = re.compile(r'\b[\wçğıöşüÇĞİÖŞÜ]{3,}\b')

        for seg in self._segments:
            text = (seg.get("segment_text") or "").lower()
            text = re.sub(r'<[^>]+>', ' ', text)
            words = pattern.findall(text)
            counter.update([w for w in words if w not in STOP_WORDS])

        word_freq = counter.most_common(150)
        if not word_freq:
            show_info(self, "Bilgi", "Yeterli metin bulunamadı.")
            return

        try:
            file_path = generate_word_cloud_html(word_freq)
            self._open_wc_dialog(file_path)
        except Exception as e:
            show_error(self, "Hata", str(e))

    def _open_wc_dialog(self, html_path: str):
        try:
            from ..common.browser_dialog import BrowserDialog
            dlg = BrowserDialog(f"☁️ Kelime Bulutu — {self._code_name}", html_path, self)
            dlg.add_word_cloud_controls()
            dlg.exec()
        except ImportError:
            import webbrowser
            webbrowser.open(f"file://{html_path}")

    def _ai_summarize(self):
        try:
            from llm_engine import OpenRouterEngine
        except ImportError:
            show_warning(self, "Hata", "LLM Engine bulunamadı.")
            return

        texts = [s.get("segment_text", "").strip() for s in self._segments if s.get("segment_text", "").strip()]
        if not texts:
            show_info(self, "Bilgi", "Özetlenecek yanıt bulunamadı.")
            return

        combined = "\\n".join(f"- {t}" for t in texts)[:12000]

        prog = QProgressDialog("AI analiz ediyor…", None, 0, 0, self)
        prog.setWindowTitle("AI Özet")
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.show()
        QApplication.processEvents()

        try:
            engine = OpenRouterEngine()
            sys_prompt = "You are a Senior QDA expert specializing in transforming raw survey responses into analytically meaningful qualitative codes and summaries. Summarize the following participant responses comprehensively, in the SAME LANGUAGE as the responses."
            prompt = f"Responses for code '{self._code_name}':\\n\\n{combined}"
            response = engine.generate_completion(prompt, system_prompt=sys_prompt, model="google/gemini-2.5-flash")
            prog.close()
            from ..common_ui import show_scrollable_info
            show_scrollable_info(self, f"AI Özet: {self._code_name}", response)
        except Exception as e:
            prog.close()
            show_error(self, "Hata", str(e))

    # ── Static Factory ────────────────────────────────────────────────────────

    @staticmethod
    def open_for_code(segment_dao, code_dao, code_id: int, code_name: str,
                      code_color: str = None, parent=None) -> "SurveyQuickCodeDialog":
        if code_color is None:
            code_color = get_color('primary')
        segments = segment_dao.get_by_code(code_id)
        all_codes = code_dao.get_all() if code_dao else []
        dlg = SurveyQuickCodeDialog(
            segments=segments,
            code_name=code_name,
            code_id=code_id,
            code_color=code_color,
            all_codes=all_codes,
            segment_dao=segment_dao,
            parent=parent,
        )
        return dlg

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _tool_btn_style(bg=None, color=None) -> str:
        bg = bg or get_color('bg_panel')
        color = color or get_color('text_secondary')
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: 1px solid {get_color('border')};
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {bg}AA;
            }}
        """
