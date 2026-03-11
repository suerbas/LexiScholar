"""
Toolbar Mixin for BrowserWidget.
Handles dynamic toolbar creation and interactive controls for visualizations.
"""

import os
from PyQt6.QtWidgets import (
    QLabel, QPushButton, QSlider, QSpinBox, QToolButton,
    QWidget, QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class BrowserToolbarMixin:
    """Handles toolbar configuration and interaction for the BrowserWidget."""

    def set_toolbar_visible(self, visible: bool):
        """Show or hide the main toolbar."""
        self.toolbar.setVisible(visible)

    def _add_trailing_controls(self):
        """Add detach button to the end of the toolbar."""
        self.toolbar.addSeparator()
        
        # Fresh button with standard icon design
        btn = QPushButton("↗")
        btn.setToolTip("Pencereyi Ayır")
        btn.setFixedSize(28, 28)
        btn.setStyleSheet("""
            QPushButton { 
                border: 1px solid #E2E8F0; background: #F8FAFC; color: #64748B; 
                font-size: 14px; font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background: #F1F5F9; color: #1E293B; border-color: #CBD5E1; }
        """)
        btn.clicked.connect(self.detach_requested.emit)
        self.toolbar.addWidget(btn)
        btn.show()

    def add_word_cloud_controls(self):
        """Add controls for word clouds with +/- buttons and value labels."""
        self.toolbar.clear()
        
        # Left Spacer for Centering
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

        # Helper for slider with controls
        def add_controlled_slider(label_text, min_v, max_v, default_v, js_func, step=5, width=70, bold=True, tooltip=None):
            lbl = QLabel(label_text)
            weight = "bold" if bold else "normal"
            lbl.setStyleSheet(f"font-weight: {weight}; margin-right: 2px;")
            if tooltip:
                lbl.setToolTip(tooltip)
            self.toolbar.addWidget(lbl)
            
            # Value tag
            val_lbl = QLabel(str(default_v))
            val_lbl.setFixedWidth(25)
            val_lbl.setStyleSheet("color: #3B82F6; font-weight: bold; font-family: 'Consolas';")

            # Slider
            sld = QSlider(Qt.Orientation.Horizontal)
            sld.setRange(min_v, max_v)
            sld.setValue(default_v)
            sld.setFixedWidth(width)
            
            def on_change(v):
                val_lbl.setText(str(v))
                self.run_js(f"{js_func}({v})")
            sld.valueChanged.connect(on_change)

            # Plus/Minus buttons
            btn_style = "QToolButton { border: 1px solid #CBD5E1; border-radius: 3px; background: white; font-weight: bold; } QToolButton:hover { background: #F1F5F9; }"
            
            btn_min = QToolButton()
            btn_min.setText("-")
            btn_min.setToolTip(f"{label_text.rstrip(':')} miktarını azalt")
            btn_min.setFixedSize(20, 20)
            btn_min.setStyleSheet(btn_style)
            btn_min.clicked.connect(lambda: sld.setValue(sld.value() - step))
            
            btn_plus = QToolButton()
            btn_plus.setText("+")
            btn_plus.setToolTip(f"{label_text.rstrip(':')} miktarını artır")
            btn_plus.setFixedSize(20, 20)
            btn_plus.setStyleSheet(btn_style)
            btn_plus.clicked.connect(lambda: sld.setValue(sld.value() + step))

            self.toolbar.addWidget(btn_min)
            self.toolbar.addWidget(sld)
            self.toolbar.addWidget(btn_plus)
            self.toolbar.addWidget(val_lbl)
            return sld

        # 1. Word Count Control
        self.count_slider = add_controlled_slider("Sözcükler:", 10, 300, 50, "setWordCount", step=1)
        
        self.toolbar.addSeparator()

        # 2. Scale Control
        self.scale_slider = add_controlled_slider("Boyut:", 30, 200, 80, "setScale", step=5)

        self.toolbar.addSeparator()

        # 3. Min Frequency (Minimum Tekrar)
        freq_tip = "Bir kelimenin bulutta görünmesi için sahip olması gereken en az tekrar sayısı."
        self.freq_slider = add_controlled_slider("Min. Tekrar:", 1, 50, 1, "setMinFreq", step=1, width=60, bold=False, tooltip=freq_tip)

        # Style for action buttons
        btn_style = """
            QPushButton { 
                border: 1px solid #D1D5DB; border-radius: 4px; padding: 4px 10px; 
                font-size: 10px; font-weight: 600; color: #374151; background: #F9FAFB;
            }
            QPushButton:hover { background: #F3F4F6; border-color: #9CA3AF; }
        """

        # Action Buttons
        refresh_btn = QPushButton("🔄 Düzenle")
        refresh_btn.setToolTip("Bulutu rastgele yeniden oluşturur")
        refresh_btn.setStyleSheet(btn_style)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(lambda: self.run_js("reshuffle()"))
        self.toolbar.addWidget(refresh_btn)
        
        clear_btn = QPushButton("🧹 Temizle")
        clear_btn.setToolTip("Gizlenen kelimeleri geri getirir")
        clear_btn.setStyleSheet(btn_style)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self.run_js("clearExclusions()"))
        self.toolbar.addWidget(clear_btn)

    def add_crosstab_controls(self):
        """Add controls for crosstab visualizations."""
        self.toolbar.clear()

        # Left Spacer for centering
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

        # Central button style matching Code Matrix
        btn_style = """
            QPushButton { 
                border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 12px; 
                font-size: 11px; font-weight: 600; color: #1E293B; background: #F8FAFC;
            }
            QPushButton:hover { background: #F1F5F9; border-color: #CBD5E1; }
        """

        # Fit to screen
        fit_btn = QPushButton("📺 Ekrana Sığdır")
        fit_btn.setToolTip("Görselleştirmeyi ekrana sığdır")
        fit_btn.setStyleSheet(btn_style)
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.clicked.connect(lambda: self.run_js("fitToScreen()"))
        self.toolbar.addWidget(fit_btn)

        # Right Spacer for centering
        spacer_r = QWidget()
        spacer_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_r)

    def add_code_matrix_controls(self):
        """Restore and center secondary toolbar for Code Matrix; features reverted from header."""
        self.toolbar.clear()
        self.toolbar.show()

        # Left Spacer for Centering
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

        # Central Button Style matching Summary Table
        btn_style = """
            QPushButton { 
                border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 12px; 
                font-weight: 600; background: #F8FAFC; color: #1E293B; 
            }
            QPushButton:hover { background: #F1F5F9; }
        """

        # Mode Toggle Button
        mode_btn = QPushButton("🔥 Isı Haritası")
        mode_btn.setToolTip("Görünümü değiştir (Daireler / Isı Haritası)")
        mode_btn.setStyleSheet(btn_style)
        mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mode_btn._is_heatmap = False
        
        def toggle_mode():
            mode_btn._is_heatmap = not mode_btn._is_heatmap
            if mode_btn._is_heatmap:
                self.run_js("toggleHeatmap(true)")
                mode_btn.setText("🔘 Daireler")
            else:
                self.run_js("toggleHeatmap(false)")
                mode_btn.setText("🔥 Isı Haritası")
        
        mode_btn.clicked.connect(toggle_mode)
        self.toolbar.addWidget(mode_btn)

        # Zoom/Fit Button
        fit_btn = QPushButton("📺 Sığdır")
        fit_btn.setToolTip("Görselleştirmeyi ekrana sığdır")
        fit_btn.setStyleSheet(btn_style)
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.clicked.connect(lambda: self.run_js("zoomReset()"))
        self.toolbar.addWidget(fit_btn)

        # Right Spacer for Centering
        spacer_r = QWidget()
        spacer_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_r)

    def add_graph_controls(self, node_count=0, edge_count=0):
        """Add controls for relationship graphs."""
        self.toolbar.clear()
        
        # Left Spacer
        spacer_l = QWidget()
        spacer_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_l)

        # Stats Label
        stats = QLabel(f"📊 Kod: {node_count} | İlişki: {edge_count}")
        stats.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; padding-right: 15px;")
        self.toolbar.addWidget(stats)

        btn_style = """
            QPushButton { 
                border: 1px solid #D1D5DB; border-radius: 4px; padding: 4px 12px; 
                font-size: 11px; font-weight: 600; color: #374151; background: #F9FAFB;
            }
            QPushButton:hover { background: #F3F4F6; }
            QPushButton:checked { background: #E0E7FF; border-color: #3B82F6; color: #1E40AF; }
        """

        # Action Buttons
        restart_btn = QPushButton("🔄 Düzenle")
        restart_btn.setToolTip("Graf yerleşimini yeniden hesaplar")
        restart_btn.setStyleSheet(btn_style)
        restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restart_btn.clicked.connect(lambda: self.run_js("restartSimulation()"))
        self.toolbar.addWidget(restart_btn)

        label_btn = QPushButton("🏷️ Etiketler")
        label_btn.setToolTip("Düğüm isimlerini göster/gizle")
        label_btn.setCheckable(True)
        label_btn.setChecked(True)
        label_btn.setStyleSheet(btn_style)
        label_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        label_btn.toggled.connect(lambda chk: self.run_js(f"toggleLabels({str(chk).lower()})"))
        self.toolbar.addWidget(label_btn)

        fit_btn = QPushButton("📺 Odakla")
        fit_btn.setToolTip("Grafı merkeze odaklar")
        fit_btn.setStyleSheet(btn_style)
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.clicked.connect(lambda: self.run_js("fitToScreen()"))
        self.toolbar.addWidget(fit_btn)

        # Right Spacer
        spacer_r = QWidget()
        spacer_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer_r)

    def add_simple_controls(self, help_anchor=None, help_tooltip=None):
        """Clear toolbar for simple visualizations."""
        self.toolbar.clear()
        self.toolbar.setVisible(False)

    def _open_encyclopedia(self, anchor=""):
        page = os.path.join(self._base_for_docs, "docs", "encyclopedia", "analysis_tools.html")
        url = QUrl.fromLocalFile(page)
        if anchor:
            url.setFragment(anchor.lstrip('#'))
        QDesktopServices.openUrl(url)

    def add_help(self, anchor=""):
        """Add a help button to the toolbar."""
        help_btn = QToolButton()
        help_btn.setText("❓")
        help_btn.setToolTip("Yardım")
        help_btn.setFixedSize(26, 26)
        help_btn.setStyleSheet("""
            QToolButton { border: none; background: transparent; color: #64748B; font-size: 14px; }
            QToolButton:hover { color: #1E293B; background: #F1F5F9; border-radius: 4px; }
        """)
        help_btn.clicked.connect(lambda: self._open_encyclopedia(anchor))
        self.toolbar.addWidget(help_btn)

    def add_keyword_controls(self, current_settings: dict = None):
        """Add controls for Keyword Analysis (YAKE)."""
        self.toolbar.clear()
        
        settings = current_settings or {'ngram_size': 2, 'top_n': 30, 'dedup_lim': 0.9}

        # N-Gram Size
        self.toolbar.addWidget(QLabel("Kelime Grubu:"))
        self.ngram_combo = QComboBox()
        self.ngram_combo.setToolTip("Analiz edilecek kelime öbeği uzunluğu (N-gram)")
        self.ngram_combo.addItems(["1 (Tek)", "2 (İkili)", "3 (Üçlü)"])
        self.ngram_combo.setCurrentIndex(settings.get('ngram_size', 2) - 1)
        self.ngram_combo.setFixedWidth(80)
        self.toolbar.addWidget(self.ngram_combo)

        # Top N
        self.toolbar.addWidget(QLabel("Limit:"))
        self.top_spin = QSpinBox()
        self.top_spin.setToolTip("Gösterilecek en önemli anahtar kelime sayısı")
        self.top_spin.setRange(5, 100)
        self.top_spin.setValue(settings.get('top_n', 30))
        self.top_spin.setFixedWidth(60)
        self.toolbar.addWidget(self.top_spin)
        
        self.toolbar.addSeparator()
        
        refresh_btn = QPushButton("⚡ Yenile")
        refresh_btn.setToolTip("Yeni ayarlarla analizi tekrar çalıştır")
        refresh_btn.setStyleSheet("background: #3B82F6; color: white; font-weight: bold;")
        refresh_btn.clicked.connect(self._emit_keyword_settings)
        self.toolbar.addWidget(refresh_btn)

        self.toolbar.addSeparator()

    def _emit_keyword_settings(self):
        """Collect settings and emit signal."""
        ngram = self.ngram_combo.currentIndex() + 1
        top_n = self.top_spin.value()
        
        self.keyword_settings_changed.emit({
            'ngram_size': ngram,
            'top_n': top_n,
            'dedup_lim': 0.9
        })
