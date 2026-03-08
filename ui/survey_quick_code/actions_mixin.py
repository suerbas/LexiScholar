"""
Actions (AI, WordCloud, Coding) for Survey Quick Code.
"""

import sys
import os
import re
import tempfile
import atexit
from collections import Counter
from PyQt6.QtWidgets import QMessageBox, QApplication, QProgressDialog, QDialog, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QUrl
from ..styles import get_color
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class SurveyQuickCodeActionsMixin:
    """Business logic for the Survey Quick Code tool."""

    def _assign_code(self, code: dict):
        if not self._selected_text:
            show_info(self, "Seçim Yok", "Lütfen önce bir cevap metninden bir bölüm seçin.")
            return

        seg = self._selected_segment
        if not seg: return

        doc_id = seg.get("document_id")
        code_id = code.get("id")

        if self._segment_dao and doc_id and code_id:
            try:
                # Calculate relative position
                doc_text = seg.get("segment_text", "")
                rel_start = doc_text.find(self._selected_text)
                if rel_start < 0: rel_start = 0
                abs_start = seg.get("start_pos", 0) + rel_start
                abs_end = abs_start + len(self._selected_text)

                self._segment_dao.add(doc_id, code_id, abs_start, abs_end, self._selected_text)
                self.sub_code_assigned.emit(doc_id, 0, self._selected_text, code_id)

                target_block = next((b for b in self._answer_blocks if b._segment is seg), None)
                if target_block: target_block.add_code_badge(code['name'], code.get('color', get_color('primary')))

                self._status_bar.setText(f"  ✅ Kodlandı: '{self._selected_text[:40]}…' → '{code['name']}'")
                self._status_bar.setStyleSheet(f"background-color: {get_color('success_bg')}; border-top: 1px solid {get_color('success')}; color: {get_color('success')}; font-size: 11px; padding: 5px 16px;")
                QTimer.singleShot(2000, self._reset_status_style)

                self._selected_text = ""
                self._selected_segment = None
                self._sel_preview.setText("(Metin seçimi yok)")
                self._sel_preview.setStyleSheet(f"font-size: 11px; font-style: italic; color: {get_color('text_muted')}; padding: 8px 12px; border-bottom: 1px solid {get_color('bg_hover')};")

            except Exception as e:
                show_error(self, "Kodlama Hatası", str(e))

    def _show_word_cloud(self):
        try:
            from ..visualizations import generate_word_cloud_html
        except ImportError:
            show_warning(self, "Hata", "Kelime bulutu modülü bulunamadı.")
            return

        try:
            from analysis.analysis_tools import STOP_WORDS
        except ImportError:
            STOP_WORDS = set()

        counter = Counter()
        pattern = re.compile(r'\b[a-zçğıöşü]{3,}\b')
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
            self._open_wc_browser(file_path)
        except Exception as e:
            show_error(self, "Hata", str(e))

    def _open_wc_browser(self, html_path: str):
        # Implementation of the browser dialog
        dlg = QDialog(self)
        dlg.setWindowTitle(f"☁️ Kelime Bulutu — {self._code_name}")
        dlg.setMinimumSize(900, 580)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(0, 0, 0, 0)
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            browser = QWebEngineView()
            browser.setUrl(QUrl.fromLocalFile(html_path) if os.path.exists(html_path) else QUrl())
            lay.addWidget(browser)
        except ImportError:
            import webbrowser
            webbrowser.open(f"file://{html_path}")
            return
        dlg.exec()

    def _ai_summarize(self):
        try:
            from llm_engine import OpenRouterEngine
        except ImportError:
            show_warning(self, "Hata", "LLM Engine bulunamadı.")
            return

        texts = [s.get("segment_text", "").strip() for s in self._segments if s.get("segment_text", "").strip()]
        if not texts: return

        combined = "\n".join(f"- {t}" for t in texts)[:12000]
        prog = QProgressDialog("AI analiz ediyor…", None, 0, 0, self)
        prog.show()
        QApplication.processEvents()

        try:
            engine = OpenRouterEngine()
            prompt = f"Responses for code '{self._code_name}':\n\n{combined}"
            response = engine.generate_completion(prompt, model="google/gemini-2.5-flash")
            prog.close()
            from ..common_ui import show_scrollable_info
            show_scrollable_info(self, f"AI Özet: {self._code_name}", response)
        except Exception as e:
            prog.close()
            show_error(self, "Hata", str(e))
