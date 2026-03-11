"""
AIAssistantMixin — LexiScholar Document Browser
Seçili metin üzerinde AI özetleme ve kod önerisi işlevlerini sağlar.
DocumentBrowser tarafından mixin olarak kullanılır.
"""

import re
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QPushButton, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextOption

from .llm_worker import LLMWorker
from .styles import AI_DIALOG_BROWSER_STYLE, AI_DIALOG_BTN_SECONDARY, AI_DIALOG_BTN_PRIMARY, AI_DIALOG_BTN_SUCCESS, AI_DIALOG_BTN_CLOSE
from nlp_engine import detect_language
from .common_ui import show_info, show_warning, show_error, ask_confirmation


class AIAssistantMixin:
    """
    Mixin: AI destekli özetleme ve kod önerisi işlevleri.

    DocumentBrowser'ın ihtiyaç duyduğu attribute'lar (parent sınıfta bulunmalı):
        self.text_edit  — CodableTextEdit
        self.header     — PanelHeader  (setText metodu olan)
    """

    # ─── Özetleme ────────────────────────────────────────────────

    def _ai_summarize_selection(self):
        """Seçili metni AI ile özetler."""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        text = cursor.selectedText()
        if len(text) < 10:
            show_warning(self, "Uyarı", "Özetlenecek metin çok kısa.")
            return

        self._update_header_status("[AI Özetliyor... ⏳]")

        lang = detect_language(text)
        target_lang_str = "İNGİLİZCE (English)" if lang == "en" else "TÜRKÇE (Turkish)"

        system_prompt = (
            "You are a Senior Academic Research Assistant specializing in descriptive and analytical summarization for qualitative studies. "
            f"YOUR TASK: Summarize the provided text STRICTLY in {target_lang_str}. "
            "Output in Markdown format using exactly this structure:\n\n"
            "**📌 Main Idea (veya Ana Fikir):**\n(1-2 sentence core summary)\n\n"
            "**🎯 Key Points (veya Önemli Noktalar):**\n- (Point 1)\n- (Point 2)\n\n"
            "**💡 Tone/Context (veya Genel Ton/Bağlam):**\n(Author's approach or context)\n\n"
            "Do NOT add any conversational introductory sentences."
        )
        user_prompt = (
            f"READ the text below carefully. "
            f"You MUST write the summary STRICTLY in {target_lang_str}:\n\nText:\n{text}"
        )

        self._run_llm_worker(user_prompt, system_prompt, self._on_ai_summary_success)

    def _on_ai_summary_success(self, summary: str):
        self._clear_header_status()
        self._show_copyable_ai_dialog("🤖 AI Özeti", summary)

    # ─── Kod Önerisi ─────────────────────────────────────────────

    def _ai_suggest_codes(self):
        """Seçili metinden AI ile kod önerileri alır."""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        text = cursor.selectedText()
        if len(text) < 10:
            show_warning(self, "Uyarı", "Kod önerisi için metin çok kısa.")
            return

        self._update_header_status("[AI Kod Öneriyor... ⏳]")

        user_prompt = (
            "Aşağıdaki metni analiz et ve metindeki temel temaları temsil eden "
            "en fazla 3 adet kısa KOD öner. "
            "Lütfen SADECE virgülle ayrılmış kısa kelimeler döndür. "
            "Kesinlikle giriş cümlesi, açıklama, numara veya ek metin YAZMA.\n\n"
            f"Metin:\n{text}\n\nÖneriler:"
        )
        system_prompt = (
            "You are an Expert QDA Methodology Consultant providing thematic coding suggestions based on Grounded Theory principles for LexiScholar. "
            "Your task is qualitative data coding/labeling. Cevabın SADECE virgülle "
            "ayrılmış kelimelerden oluşmalıdır. Asla sohbet etme, asla açıklama yapma."
        )

        self._run_llm_worker(user_prompt, system_prompt, self._on_ai_codes_success)

    def _on_ai_codes_success(self, codes_text: str):
        self._clear_header_status()
        content = (
            f"Önerilen Kodlar:\n\n{codes_text}\n\n"
            "Not: Beğendiğiniz kodu Tepsiden yeni kod olarak ekleyebilirsiniz."
        )
        self._show_copyable_ai_dialog("💡 AI Kod Önerileri", content)

    # ─── Hata Yönetimi ───────────────────────────────────────────

    def _on_ai_error(self, err_msg: str):
        self._clear_header_status()
        if "environ" in err_msg or "API anahtarı" in err_msg:
            err_msg = (
                "OpenRouter API Anahtarı bulunamadı.\n"
                "Lütfen program dizinindeki .env dosyasını yapılandırıp programı yeniden başlatın."
            )
        show_error(self, "AI Asistanı Hatası", err_msg)

    # ─── Yardımcılar ─────────────────────────────────────────────

    def _run_llm_worker(self, prompt: str, system_prompt: str, success_slot):
        """LLMWorker başlatır ve sinyal bağlantılarını kurar."""
        self._worker = LLMWorker(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1
        )
        self._worker.finished_success.connect(success_slot)
        self._worker.finished_error.connect(self._on_ai_error)
        self._worker.start()

    def _update_header_status(self, status_text: str):
        """Header'a geçici durum mesajı ekler."""
        # Header removed in UI redesign. Trying to use statusbar if available.
        if hasattr(self, 'window') and hasattr(self.window(), 'statusbar'):
            self.window().statusbar.showMessage(status_text)
        # Fallback: print to console
        print(f"AI Status: {status_text}")

    def _clear_header_status(self):
        """Header'daki AI durum mesajlarını temizler."""
        if hasattr(self, 'window') and hasattr(self.window(), 'statusbar'):
            self.window().statusbar.clearMessage()

    def _show_copyable_ai_dialog(self, title: str, content: str):
        """Kopyalanabilir, markdown destekli AI sonuç diyaloğu gösterir."""
        # LLM bazen cevabı ```markdown ... ``` içine alır — temizle
        content = re.sub(r"^```(?:markdown|md)?\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content)

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(550, 450)
        dialog.resize(700, 550)

        layout = QVBoxLayout(dialog)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        browser.setMarkdown(content)
        browser.setStyleSheet(AI_DIALOG_BROWSER_STYLE)
        layout.addWidget(browser)

        btn_layout = QHBoxLayout()
        current_md = [content]

        # Çeviri butonları
        btn_tr = QPushButton("🇹🇷 Türkçeye Çevir")
        btn_en = QPushButton("🇬🇧 Translate to English")
        for btn in (btn_tr, btn_en):
            btn.setStyleSheet(AI_DIALOG_BTN_SECONDARY)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        def do_translate(target_lang: str):
            is_tr = target_lang == "TR"
            btn = btn_tr if is_tr else btn_en
            btn.setText("⏳ Çevriliyor...")
            btn_tr.setEnabled(False)
            btn_en.setEnabled(False)

            prompt_lang = (
                "tamamen akademik ve kusursuz bir Türkçeye"
                if is_tr else
                "tamamen akademik ve kusursuz bir İngilizceye (English)"
            )
            sys_lang = (
                "You are an expert in cross-cultural academic terminology and qualitative research vocabulary, serving as a professional academic translator. "
                "Sadece çeviriyi Markdown formatını bozmadan ver. Kendi yorumunu ekleme."
            )

            worker = LLMWorker(
                prompt=(
                    f"Aşağıdaki metni {prompt_lang} çevir. "
                    f"Orijinal Markdown formatını kesinlikle koru:\n\n{current_md[0]}"
                ),
                system_prompt=sys_lang,
                temperature=0.3,
                parent=dialog,
            )

            def on_success(translated: str):
                translated = re.sub(r"^```(?:markdown|md)?\s*", "", translated.strip())
                translated = re.sub(r"\s*```$", "", translated)
                current_md[0] = translated
                browser.setMarkdown(translated)
                btn_tr.setText("🇹🇷 Türkçeye Çevir")
                btn_en.setText("🇬🇧 Translate to English")
                btn_tr.setEnabled(True)
                btn_en.setEnabled(True)

            def on_error(err: str):
                btn_tr.setText("🇹🇷 Türkçeye Çevir")
                btn_en.setText("🇬🇧 Translate to English")
                btn_tr.setEnabled(True)
                btn_en.setEnabled(True)
                show_warning(dialog, "Çeviri Hatası", f"Çeviri sırasında hata:\n{err}")

            worker.finished_success.connect(on_success)
            worker.finished_error.connect(on_error)
            worker.start()
            dialog._current_translation_worker = worker  # GC'den koruma

        btn_tr.clicked.connect(lambda: do_translate("TR"))
        btn_en.clicked.connect(lambda: do_translate("EN"))

        btn_copy = QPushButton("📋 Kopyala")

        def copy_text():
            QApplication.clipboard().setText(current_md[0])
            btn_copy.setText("✅ Kopyalandı!")
            btn_copy.setStyleSheet(
                "padding: 10px 24px; font-weight: bold; "
                "background-color: #22c55e; color: white; "
                "border: none; border-radius: 6px;"
            )

        btn_copy.clicked.connect(copy_text)
        btn_copy.setStyleSheet(AI_DIALOG_BTN_PRIMARY)
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(dialog.accept)
        btn_close.setStyleSheet(AI_DIALOG_BTN_CLOSE)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_layout.addWidget(btn_tr)
        btn_layout.addWidget(btn_en)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_copy)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        dialog.exec()
