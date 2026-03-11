"""
Retrieved Segments Widget for LexiScholar
Panel showing all text segments associated with a specific code.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QFrame, QMenu, QScrollArea, QPushButton, QComboBox
)
import math
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from .styles import PANEL_HEADER_STYLE, SCROLL_AREA_STYLE
from .panel_header import PanelHeader
from .icons import IconProvider
from .common import ModernSegmentCard
from .common_ui import show_info, show_warning, show_error, ask_confirmation

# Internal SegmentCard replaced by ui.common.ModernSegmentCard


class RetrievedSegments(QWidget):
    """Panel showing all segments for active codes in active documents."""
    
    # Signals
    segment_clicked = pyqtSignal(int, int)  # document_id, segment_id
    segment_delete_requested = pyqtSignal(int)  # segment_id
    minimize_requested = pyqtSignal()
    detach_requested = pyqtSignal()
    query_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_code_id = None # Deprecated, but keeping for compatibility if needed
        self._active_card = None
        self._all_segments = []
        self._current_page = 1
        self._items_per_page = 50
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the retrieved segments UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header (Not closable as it's a main panel)
        self.header = PanelHeader("GERİ ÇAĞIRILAN BÖLÜMLER", has_close=False)
        self.header.minimize_requested.connect(self.minimize_requested.emit)
        self.header.detach_requested.connect(self.detach_requested.emit)
        
        # Add Layout Toggle Button to Header
        self.btn_layout = QPushButton()
        self.btn_layout.setToolTip("Görünümü Değiştir (Dikey/Yatay)")
        self.btn_layout.setAccessibleName("Görünüm Düzeni")
        self.btn_layout.setAccessibleDescription("Sağ paneli yatay ve dikey düzen arasında değiştirir.")
        self.btn_layout.setIcon(IconProvider.get_layout_icon("vertical", "#64748B"))
        self.btn_layout.setFixedSize(24, 24)
        self.btn_layout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_layout.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_layout.setStyleSheet("QPushButton { border: none; background: transparent; font-size: 14px; color: #64748B; } QPushButton:hover { color: #1E293B; background: #F1F5F9; border-radius: 4px; }")
        self.btn_layout.clicked.connect(self._toggle_layout_mode)
        
        # Insert before minimize/detach buttons
        # PanelHeader layout is usually HBox with title, stretch, buttons.
        # We need to access its layout to insert properly or just add to toolbar.
        # Let's add it to the toolbar instead as it's safer than hacking PanelHeader.
        
        layout.addWidget(self.header)
        
        # ── Toolbar ───────────────────────────────────────────────────
        from PyQt6.QtWidgets import QToolBar
        self.toolbar = QToolBar("Segment Araçları")
        self.toolbar.setAccessibleName("Segment Araç Çubuğu")
        self.toolbar.setAccessibleDescription("Sorgu ve dışa aktarma komutlarını içerir.")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar { 
                background: white; border-bottom: 1px solid #E2E8F0; 
                padding: 4px 8px; spacing: 10px;
            }
            QPushButton { 
                border: 1px solid #E2E8F0; border-radius: 4px; padding: 3px 10px; 
                font-size: 11px; font-weight: 700; color: #475569; background: #F8FAFC;
            }
            QPushButton:hover { background: #F1F5F9; border-color: #CBD5E1; }
        """)
        layout.addWidget(self.toolbar)

        # Query button
        self.btn_query = QPushButton("Sorgu")
        self.btn_query.setToolTip("Gelişmiş Boolean Sorgu Oluşturucu (Ctrl+Q)")
        self.btn_query.setAccessibleName("Gelişmiş Sorgu")
        self.btn_query.setAccessibleDescription("Boolean operatörleri ile segment sorgusu açar.")
        self.btn_query.setIcon(IconProvider.get_action_icon("search", "#475569"))
        self.btn_query.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_query.clicked.connect(self.query_requested.emit)
        self.toolbar.addWidget(self.btn_query)

        self.btn_export = QPushButton("Aktar")
        self.btn_export.setToolTip("Kodlu bölümleri rapor veya veri olarak dışa aktarın.")
        self.btn_export.setAccessibleName("Segment Aktar")
        self.btn_export.setAccessibleDescription("Kodlu bölümleri CSV dosyasına aktarır.")
        self.btn_export.setIcon(IconProvider.get_action_icon("export", "#475569"))
        self.btn_export.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_export.clicked.connect(self._export_segments)
        self.toolbar.addWidget(self.btn_export)

        self.btn_export.clicked.connect(self._export_segments)
        self.toolbar.addWidget(self.btn_export)

        self.toolbar.addSeparator()

        # Semantic Mode Toggle
        self.btn_semantic_mode = QPushButton("Anlamsal Mod")
        self.btn_semantic_mode.setCheckable(True)
        self.btn_semantic_mode.setToolTip("Yapay Zeka destekli Anlamsal Arama (Semantic Search) modunu aç/kapat")
        self.btn_semantic_mode.setAccessibleName("Anlamsal Mod Geçişi")
        self.btn_semantic_mode.setIcon(IconProvider.get_action_icon("analytics", "#475569"))
        self.btn_semantic_mode.toggled.connect(self._toggle_semantic_mode)
        self.toolbar.addWidget(self.btn_semantic_mode)

        # Semantic Search Bar (Hidden by default)
        from PyQt6.QtWidgets import QLineEdit
        self.semantic_bar = QWidget()
        self.semantic_bar.setStyleSheet("background: #F8FAFC; border-bottom: 1px solid #E2E8F0;")
        sem_layout = QHBoxLayout(self.semantic_bar)
        sem_layout.setContentsMargins(8, 6, 8, 6)
        
        self.semantic_input = QLineEdit()
        self.semantic_input.setPlaceholderText("Anlamsal arama için bir kavram veya cümle girin (Örn: Ekonomik kaygı)...")
        self.semantic_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CBD5E1; border-radius: 4px; padding: 4px 8px;
                background: white; font-size: 13px;
            }
            QLineEdit:focus { border-color: #3B82F6; }
        """)
        self.semantic_input.returnPressed.connect(self._trigger_semantic_search)
        
        self.btn_do_semantic_search = QPushButton("Ara ✨")
        self.btn_do_semantic_search.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6; color: white; border-radius: 4px; padding: 4px 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.btn_do_semantic_search.clicked.connect(self._trigger_semantic_search)
        
        sem_layout.addWidget(self.semantic_input)
        sem_layout.addWidget(self.btn_do_semantic_search)
        self.semantic_bar.hide()
        layout.addWidget(self.semantic_bar)
        
        # Segments list container
        self.segments_container = QWidget()
        self.segments_container.setStyleSheet("background-color: #FFFFFF;")
        self.segments_layout = QVBoxLayout(self.segments_container)
        self.segments_layout.setContentsMargins(8, 12, 8, 12)
        self.segments_layout.setSpacing(8)
        self.segments_layout.addStretch()
        
        # Scroll area for segments
        scroll = QScrollArea()
        scroll.setWidget(self.segments_container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(SCROLL_AREA_STYLE)
        layout.addWidget(scroll)
        
        # Pagination Controls
        self.pagination_widget = QWidget()
        self.pagination_widget.setStyleSheet("background-color: #F8FAFC; border-top: 1px solid #E2E8F0; padding: 4px;")
        pag_layout = QHBoxLayout(self.pagination_widget)
        pag_layout.setContentsMargins(8, 4, 8, 4)
        
        self.btn_prev_page = QPushButton("◀ Önceki")
        self.btn_prev_page.setAccessibleName("Önceki Sayfa")
        self.btn_prev_page.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_prev_page.clicked.connect(self._prev_page)
        
        self.page_label = QLabel("Sayfa 1 / 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_next_page = QPushButton("Sonraki ▶")
        self.btn_next_page.setAccessibleName("Sonraki Sayfa")
        self.btn_next_page.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_next_page.clicked.connect(self._next_page)
        
        for btn in (self.btn_prev_page, self.btn_next_page):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #475569;
                }
                QPushButton:hover { background-color: #F1F5F9; }
                QPushButton:disabled { color: #94A3B8; background-color: #F8FAFC; border-color: #E2E8F0; }
            """)
            
        pag_layout.addWidget(self.btn_prev_page)
        pag_layout.addStretch()
        pag_layout.addWidget(self.page_label)
        pag_layout.addStretch()
        pag_layout.addWidget(self.btn_next_page)
        self.pagination_widget.hide()
        layout.addWidget(self.pagination_widget)
        
        # Empty state (Centered in the layout)
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Use a large icon or emoji for the empty state
        empty_icon = QLabel("🔍") # Or 🕸️, 📂
        empty_icon.setStyleSheet("font-size: 48px; color: #CBD5E1; margin-bottom: 10px;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_text = QLabel("Henüz gösterilecek bir kodlama yok\n\nKodlu bölümleri listelemek için\nbelge(ler) ve kod(lar) etkinleştirin")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text.setStyleSheet("color: #94A3B8; font-size: 13px; line-height: 1.5;")
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        
        # Add empty widget to segments layout (it will be shown/hidden)
        # Actually, it's better to put it in the main layout stack or just toggle visibility
        # But since we use a scroll area, let's just add it to the container and hide it when has data
        self.segments_layout.insertWidget(0, self.empty_widget)
        self.empty_widget.show()
    
    def _toggle_layout_mode(self):
        """Toggle between Horizontal and Vertical splitter in main window."""
        # Find MainWindow by walking up parent chain or checking QApplication
        from PyQt6.QtWidgets import QApplication
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "MainWindow" or widget.__class__.__name__ == "MainWindow":
                main_window = widget
                break
        
        if not main_window and self.window():
            main_window = self.window()

        if hasattr(main_window, 'right_splitter'):
            splitter = main_window.right_splitter
            if splitter.orientation() == Qt.Orientation.Vertical:
                splitter.setOrientation(Qt.Orientation.Horizontal)
                splitter.setSizes([800, 300]) 
                self.btn_layout.setIcon(IconProvider.get_layout_icon("vertical", "#64748B"))
            else:
                splitter.setOrientation(Qt.Orientation.Vertical)
                splitter.setSizes([500, 300])
                self.btn_layout.setIcon(IconProvider.get_layout_icon("horizontal", "#64748B"))

    def set_segments(self, segments: list):
        """
        Display a list of segments.
        
        Args:
            segments: List of segment dicts from the database
        """
        self._all_segments = segments
        self._current_page = 1
        self._render_current_page()
        
    def _render_current_page(self):
        self._active_card = None
        self._clear_segments()
        
        total_segments = len(self._all_segments)
        
        if total_segments == 0:
            self.header.set_title("GERİ ÇAĞIRILAN BÖLÜMLER (0)")
            self.empty_widget.show()
            self.pagination_widget.hide()
            return
            
        self.empty_widget.hide()
        self.header.set_title(f"GERİ ÇAĞIRILAN BÖLÜMLER ({total_segments})")
        
        total_pages = math.ceil(total_segments / self._items_per_page)
        self._current_page = max(1, min(self._current_page, total_pages))
        
        if total_pages > 1:
            self.pagination_widget.show()
            self.page_label.setText(f"Sayfa {self._current_page} / {total_pages}")
            self.btn_prev_page.setEnabled(self._current_page > 1)
            self.btn_next_page.setEnabled(self._current_page < total_pages)
        else:
            self.pagination_widget.hide()
            
        start_idx = (self._current_page - 1) * self._items_per_page
        end_idx = min(start_idx + self._items_per_page, total_segments)
        
        page_segments = self._all_segments[start_idx:end_idx]
        
        for seg in page_segments:
            card = ModernSegmentCard(seg)
            card.clicked.connect(lambda d, s, c=card: self._handle_card_click(c, d, s))
            
            # Add context menu (ModernSegmentCard doesn't have it yet, or we add here)
            card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card.customContextMenuRequested.connect(lambda pos, sid=seg.get('id'): self._show_card_context_menu(pos, sid))
            
            self.segments_layout.insertWidget(self.segments_layout.count() - 1, card)
            card.adjust_height_to_content()
            
    def _show_card_context_menu(self, pos, segment_id):
        menu = QMenu(self)
        delete_action = menu.addAction("🗑️ Segmenti Sil")
        action = menu.exec(self.sender().mapToGlobal(pos))
        if action == delete_action:
            self.segment_delete_requested.emit(segment_id)
            
    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._render_current_page()
            
    def _next_page(self):
        total_pages = math.ceil(len(self._all_segments) / self._items_per_page)
        if self._current_page < total_pages:
            self._current_page += 1
            self._render_current_page()
            
    def _handle_card_click(self, card, doc_id, segment_id):
        """Handle card click to update active state."""
        if self._active_card:
            try:
                self._active_card.set_active(False)
            except RuntimeError: # Widget might have been deleted during refresh
                pass
        
        self._active_card = card
        card.set_active(True)
        
        # Emit signal to parent
        self.segment_clicked.emit(doc_id, segment_id)
    
    def _clear_segments(self):
        """Remove all segment cards."""
        # Iterate backwards to safely remove
        for i in range(self.segments_layout.count() - 1, -1, -1): 
            item = self.segments_layout.itemAt(i)
            widget = item.widget()
            if widget:
                # Don't delete the empty_widget
                if widget == self.empty_widget:
                    continue
                widget.deleteLater()
            
    def set_current_code_id(self, code_id: int):
        """Set the current code ID for export/context purposes."""
        self._current_code_id = code_id

    def set_code(self, code_id, name, segments):
        """
        Update the panel for a specific code.
        Used by handlers.py and analysis_actions.py
        """
        self._current_code_id = code_id
        self.header.set_title(f"KOD: {name} ({len(segments)})")
        self.set_segments(segments)

    def populate_segments(self, segments):
        """Alias for set_segments for compatibility with query_builder."""
        self.set_segments(segments)

    def clear(self):
        """Clear the panel."""
        self._current_code_id = None
        self._all_segments = []
        self._current_page = 1
        self.header.set_title("GERİ ÇAĞIRILAN BÖLÜMLER")
        self._clear_segments()
        self.empty_widget.show()
        self.pagination_widget.hide()
    
    def clear_segments(self):
        """Alias for clear() - used by handlers.py"""
        self.clear()
    def _export_segments(self):
        """Export current retrieved segments to CSV."""
        if not self._all_segments:
            from PyQt6.QtWidgets import QMessageBox
            show_info(self, "Bilgi", "Dışa aktarılacak segment bulunmuyor.\nLütfen önce belge ve kodları etkinleştirin.")
            return

        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import csv
        
        def _sanitize_cell(value):
            text = str(value or "")
            if text and text[0] in ("=", "+", "-", "@"):
                return f"'{text}"
            return text
        
        path, _ = QFileDialog.getSaveFileName(self, "Segmentleri Aktar (Excel uyumlu)", "geri_cagrilan_bolumler.csv", "CSV Dosyaları (*.csv)")
        if not path: return
        
        try:
            # utf-8-sig ensures Excel opens it correctly with UTF-8
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, delimiter=';')
                header = ["Belge", "Klasör", "Kod", "Segment Metni", "Ağırlık"]
                writer.writerow(header)
                
                for s in self._all_segments:
                    # Robust handling of potentially null values
                    doc_title = _sanitize_cell(s.get('document_title') or 'Adsız Belge')
                    folder = _sanitize_cell(s.get('folder_name') or '-')
                    code = _sanitize_cell(s.get('code_name') or '-')
                    text = _sanitize_cell((s.get('segment_text') or '').replace('\n', ' ').strip())
                    weight = s.get('weight', 0)
                    
                    writer.writerow([doc_title, folder, code, text, weight])
            
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            
            from .common_ui import ask_confirmation
            if ask_confirmation(self, "Başarılı", f"Segmentler başarıyla aktarıldı:\n{os.path.basename(path)}\n\nKlasörü açmak ister misiniz?"):
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
                
        except Exception as e:
            show_error(self, "Hata", f"Dışa aktarma başarısız oldu:\n{str(e)}")

    def _toggle_semantic_mode(self, checked: bool):
        """Show or hide the semantic search bar."""
        self.semantic_bar.setVisible(checked)
        if checked:
            self.semantic_input.setFocus()
            
            # Show info message if no segments loaded
            if not self._all_segments:
                self.statusbar_msg("Anlamsal arama için önce sonuçları listeleyen bir kod veya düğüme tıklayın.")
        else:
            self.semantic_input.clear()

    def _trigger_semantic_search(self):
        """Execute semantic search on currently loaded segments."""
        query = self.semantic_input.text().strip()
        if not query:
            return
            
        if not self._all_segments:
            show_info(self, "Bilgi", "Anlamsal arama yapılacak segment bulunamadı. Lütfen önce belgelerden bölümler listeleyin.")
            return
            
        try:
            from nlp.tasks.semantic import semantic_search
            from ui.common_ui import ModernProgressDialog
            
            progress = ModernProgressDialog(
                title="Yapay Zeka Anlamsal Çözümleme",
                message=f"'{query}' kavramı mevcut {len(self._all_segments)} segment içinde aranıyor...\nBu işlem ilk çalıştırmada model indirileceğinden uzun sürebilir.",
                max_val=0,
                parent=self
            )
            progress.show()
            
            # Using QTimer to allow UI update before blocking NLP task
            # In a real heavy app, this should be a QThread
            from PyQt6.QtCore import QTimer
            
            def do_search():
                try:
                    # Perform search (this will download model if missing and block, or use cache)
                    results = semantic_search(query, self._all_segments, top_k=50)
                    
                    if progress.isVisible():
                        progress.close()
                        
                    if results:
                        self.set_segments(results)
                        self.header.set_title(f"Arama Sonuçları: '{query}' ({len(results)} eşleşme)")
                    else:
                        show_info(self, "Bilgi", "Anlam eşleşmesi bulunamadı.")
                        
                except Exception as e:
                    if progress.isVisible():
                        progress.close()
                    error_msg = str(e)
                    if "Kütüphane_Eksik" in error_msg:
                        show_error(self, "Gerekli Kütüphaneler Eksik", "Anlamsal arama için gerekli Python kütüphaneleri eksik:\n\npip install sentence-transformers")
                    elif "Model_Missing" in error_msg:
                        show_info(self, "Dil Modeli Gerekli", "Bu özellik dünyaca ünlü BAAI/bge-m3 dil modelini (2.2 GB) gerektirir.\n\nLütfen üst menüden 'Dil Modellerini Kontrol Et' seçeneğine tıklayarak modeli indirin.")
                    else:
                        show_error(self, "Arama Hatası", f"Anlamsal arama sırasında bir hata oluştu:\n{error_msg}")
                        
            QTimer.singleShot(100, do_search)
            
        except ImportError:
            show_error(self, "Sistem Hatası", "Anlamsal arama modülü yüklenemedi.")

    def statusbar_msg(self, msg: str):
        """Helper to show a message if main window statusbar exists."""
        from PyQt6.QtWidgets import QApplication
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "MainWindow":
                if hasattr(widget, "statusbar"):
                    widget.statusbar.showMessage(msg, 5000)
                break

