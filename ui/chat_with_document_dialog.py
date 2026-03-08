"""
Chat With Document Dialog — LexiScholar
MAXQDA-style "Chat with This Document" AI interface.
Loads the document text as context, then lets the user ask questions
about it in a chat-style interface using OpenRouter.
"""

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QTextEdit, QFrame, QSizePolicy,
    QApplication, QProgressDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor
from .styles import COLORS


# ─── Background worker ────────────────────────────────────────────────────────

class _AIWorker(QObject):
    """Runs the AI call in a background thread."""
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, messages: list, model: str):
        super().__init__()
        self._messages = messages
        self._model = model

    def run(self):
        try:
            from llm_engine import OpenRouterEngine
            engine = OpenRouterEngine()
            response = engine.chat_completion(self._messages, model=self._model)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))



# ─── Message Bubble ───────────────────────────────────────────────────────────

class _Bubble(QFrame):
    """A single chat message bubble."""

    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self._is_user = is_user
        self._setup(text)

    def _setup(self, text: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.TextFormat.MarkdownText)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        lbl.setText(text)
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl.setMaximumWidth(1000) # Increased for larger screens

        if self._is_user:
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #4F46E5;
                    color: #FFFFFF;
                    border-radius: 14px;
                    padding: 10px 14px;
                    font-size: 13px;
                    line-height: 1.5;
                }
            """)
            layout.addStretch()
            layout.addWidget(lbl)
        else:
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #F1F5F9;
                    color: #1E293B;
                    border-radius: 14px;
                    padding: 10px 14px;
                    font-size: 13px;
                    line-height: 1.5;
                }
            """)
            layout.addWidget(lbl)
            layout.addStretch()

        self.setStyleSheet("QFrame { background: transparent; }")


# ─── Main Dialog ──────────────────────────────────────────────────────────────

class ChatWidget(QWidget):
    """
    Widget version of the AI Chat for tabbed interface.
    """

    def __init__(
        self,
        doc_id: int,
        doc_title: str,
        doc_text: str,
        chat_dao=None,
        parent=None,
        on_close_callback=None
    ):
        super().__init__(parent)
        self._doc_id = doc_id
        self._doc_title = doc_title
        self._doc_text = doc_text[:20000]          # cap context at ~20k chars
        self._chat_dao = chat_dao
        self._history: list[dict] = []             # OpenAI-style message list
        self._thread: QThread | None = None
        self._worker: _AIWorker | None = None
        self._on_close_callback = on_close_callback

        self._build_system_prompt()
        self._setup_ui()

    # ── System Prompt ─────────────────────────────────────────────────────────

    def _build_system_prompt(self):
        self._system_prompt = (
            "You are an expert Qualitative Data Analysis (QDA) and qualitative research assistant "
            "working within the LexiScholar application. You are helping a researcher analyze "
            "a document by identifying themes, assigning codes, writing memos, and finding patterns. "
            "The document text is provided below. Answer questions about the "
            "document accurately and concisely. "
            "CRITICAL INSTRUCTION: You MUST use the EXACT SAME LANGUAGE as the user's question. "
            "If the user asks in Turkish, your ENTIRE response MUST be in fluent and natural Turkish. "
            "Do NOT mix words from German, English, or other languages into your response. "
            "If the answer is not found in the document, say so clearly.\n\n"
            f"--- DOCUMENT: {self._doc_title} ---\n"
            f"{self._doc_text}\n"
            "--- END OF DOCUMENT ---"
        )

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = QWidget()
        toolbar.setFixedHeight(44)
        toolbar.setStyleSheet(f"""
            background-color: #FFFFFF;
            border-bottom: 1px solid {COLORS.get('border', '#E2E8F0')};
        """)
        h_lay = QHBoxLayout(toolbar)
        h_lay.setContentsMargins(12, 0, 12, 0)
        h_lay.setSpacing(8)
        h_lay.addStretch()

        btn_clear = QPushButton("🗑 Sohbeti Temizle")
        btn_clear.setStyleSheet(self._tool_btn_style())
        btn_clear.clicked.connect(self._clear_chat)
        h_lay.addWidget(btn_clear)

        doc_chars_lbl = QLabel(f"{len(self._doc_text):,} karakter yüklendi")
        doc_chars_lbl.setStyleSheet("font-size: 11px; color: #94A3B8; padding-left: 6px;")
        h_lay.addWidget(doc_chars_lbl)

        root.addWidget(toolbar)

        # Chat history
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: #FFFFFF; }")

        self._chat_container = QWidget()
        self._chat_container.setStyleSheet("background: #FFFFFF;")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(24, 24, 24, 24)
        self._chat_layout.setSpacing(12)
        self._chat_layout.addStretch(1) # Pushes messages to bottom

        self._scroll.setWidget(self._chat_container)
        root.addWidget(self._scroll, 1) # Set stretch factor to 1

        # Typing indicator (hidden by default)
        self._typing_lbl = QLabel("🤖  AI yazıyor…")
        self._typing_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-style: italic; padding: 4px 16px;")
        self._typing_lbl.setVisible(False)
        root.addWidget(self._typing_lbl)

        # Input area
        input_area = QWidget()
        input_area.setStyleSheet(f"""
            background-color: #FAFAFA;
            border-top: 1px solid {COLORS.get('border', '#E2E8F0')};
        """)
        in_lay = QHBoxLayout(input_area)
        in_lay.setContentsMargins(12, 8, 12, 8)
        in_lay.setSpacing(8)

        self._input = QTextEdit()
        self._input.setPlaceholderText("Belge hakkında bir soru sorun… (Ctrl+Enter ile gönderin)")
        self._input.setFixedHeight(72)
        self._input.setStyleSheet("""
            QTextEdit {
                border: 1.5px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1E293B;
                background: #FFFFFF;
            }
            QTextEdit:focus { border-color: #4F46E5; }
        """)
        self._input.installEventFilter(self)
        in_lay.addWidget(self._input)

        self._send_btn = QPushButton("Gönder ➤")
        self._send_btn.setFixedSize(90, 72)
        self._send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover { background-color: #4338CA; }
            QPushButton:disabled { background-color: #A5B4FC; }
        """)
        self._send_btn.clicked.connect(self._send)
        in_lay.addWidget(self._send_btn)

        root.addWidget(input_area)

        # Load history or welcome
        self._load_history_or_welcome()

    def _load_history_or_welcome(self):
        if self._chat_dao:
            saved_history = self._chat_dao.get_by_document(self._doc_id)
            if saved_history:
                for msg in saved_history:
                    self._history.append({"role": msg["role"], "content": msg["content"]})
                    if msg["role"] == "user":
                        self._add_user_bubble(msg["content"])
                    else:
                        self._add_ai_bubble(msg["content"])
                
                QTimer.singleShot(100, self._scroll_to_bottom)
                return

        self._add_welcome_message()

    def _add_welcome_message(self):
        self._add_ai_bubble(
            f"Merhaba! **'{self._doc_title}'** belgesindeki içerik hakkında sorularınızı yanıtlamaya hazırım. "
            "Belgenin herhangi bir bölümü, tema, dil, bağlam ya da kodlama hakkında dilediğiniz soruyu sorabilirsiniz."
        )

    # ── Event Filter (Ctrl+Enter) ─────────────────────────────────────────────

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        if obj is self._input and event.type() == QEvent.Type.KeyPress:
            ke: QKeyEvent = event
            if ke.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and ke.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self._send()
                return True
        return super().eventFilter(obj, event)

    # ── Chat Logic ────────────────────────────────────────────────────────────

    def _send(self):
        text = self._input.toPlainText().strip()
        if not text or self._thread is not None:
            return

        self._input.clear()
        self._add_user_bubble(text)

        # Append to history
        self._history.append({"role": "user", "content": text})
        if self._chat_dao:
            self._chat_dao.add_message(self._doc_id, "user", text)

        # Build messages list for API
        messages = [{"role": "system", "content": self._system_prompt}] + self._history

        self._set_waiting(True)

        # Run in background thread
        self._thread = QThread()
        # Passing model=None to _AIWorker ensures OpenRouterEngine uses the user-selected model
        self._worker = _AIWorker(messages, model=None)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_ai_response)
        self._worker.error.connect(self._on_ai_error)
        self._thread.start()

    def _on_ai_response(self, response: str):
        self._cleanup_thread()
        self._history.append({"role": "assistant", "content": response})
        if self._chat_dao:
            self._chat_dao.add_message(self._doc_id, "assistant", response)
        self._add_ai_bubble(response)
        self._set_waiting(False)

    def _on_ai_error(self, error: str):
        self._cleanup_thread()
        self._add_ai_bubble(f"⚠️ Hata: {error}")
        self._set_waiting(False)

    def _cleanup_thread(self):
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None

    def _set_waiting(self, waiting: bool):
        self._send_btn.setEnabled(not waiting)
        self._typing_lbl.setVisible(waiting)
        self._input.setReadOnly(waiting)
        if waiting:
            self._scroll_to_bottom()

    def _clear_chat(self):
        self._history.clear()
        if self._chat_dao:
            self._chat_dao.clear_document_chat(self._doc_id)
        # Keep the stretch (index 0)
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        self._add_ai_bubble(
            "Sohbet temizlendi. Yeni sorularınızı bekliyorum!"
        )

    # ── Bubble Helpers ────────────────────────────────────────────────────────

    def _add_user_bubble(self, text: str):
        bubble = _Bubble(text, is_user=True, parent=self._chat_container)
        self._chat_layout.addWidget(bubble) # Append to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _add_ai_bubble(self, text: str):
        bubble = _Bubble(text, is_user=False, parent=self._chat_container)
        self._chat_layout.addWidget(bubble) # Append to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _tool_btn_style() -> str:
        return """
            QPushButton {
                background-color: #F8FAFC;
                color: #475569;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #F1F5F9; }
        """

    def closeEvent(self, event):
        self._cleanup_thread()
        if self._on_close_callback:
            self._on_close_callback()
        super().closeEvent(event)


class ChatWithDocumentDialog(QDialog):
    """
    Standalone dialog wrapper for ChatWidget.
    """
    def __init__(
        self,
        doc_id: int,
        doc_title: str,
        doc_text: str,
        chat_dao=None,
        parent=None,
        on_close_callback=None
    ):
        super().__init__(parent)
        self.setWindowTitle(f"💬 AI Sohbet — {doc_title}")
        self.setMinimumSize(700, 600)
        self.setModal(False)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.widget = ChatWidget(doc_id, doc_title, doc_text, chat_dao, self, on_close_callback)
        layout.addWidget(self.widget)

    def closeEvent(self, event):
        self.widget.closeEvent(event)
        super().closeEvent(event)
