"""
Ribbon UI Setup for LexiScholar MainWindow.
Extracted to a mixin to keep MainWindow.py clean.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, 
    QLabel, QPushButton, QToolButton, QFrame, 
    QSizePolicy, QMenu, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QActionGroup
from .icons import IconProvider
from .search import SearchDialog
from .styles import (
    RIBBON_GROUP_STYLE, RIBBON_BUTTON_STYLE, RIBBON_LABEL_STYLE, 
    RIBBON_GROUP_NO_BORDER_STYLE, COLORS, CONTEXT_MENU_STYLE, TAB_WIDGET_STYLE,
    SPACING
)

class RibbonMixin:
    """Mixin for setting up the ribbon tabs and persistent global controls."""
    
    def create_ribbon_btn(self, text, tooltip, callback, emoji, color, overlay=None):
        """Standardized ribbon button with icon and label underneath."""
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setStatusTip(tooltip)  # Show description in status bar
        btn.setAccessibleName(text.replace("\n", " ").strip())
        btn.setAccessibleDescription(tooltip)
        btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if callback:
            btn.clicked.connect(callback)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        icon = IconProvider.get_icon(emoji, color, overlay_emoji=overlay)
        btn.setIcon(icon)
        btn.setIconSize(QSize(24, 24))
        btn.setStyleSheet(RIBBON_BUTTON_STYLE)
        btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        btn.setAutoRaise(True)
        if not hasattr(self, "_ribbon_buttons"):
            self._ribbon_buttons = []
        self._ribbon_buttons.append(btn)
        return btn

    def create_group(self, layout_type=QHBoxLayout, has_divider=True):
        """Standardized group container frame."""
        frame = QFrame()
        style = RIBBON_GROUP_STYLE if has_divider else RIBBON_GROUP_NO_BORDER_STYLE
        frame.setStyleSheet(style)
        layout = layout_type(frame)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        return frame, layout

    def create_v_separator(self):
        """Creates a standardized vertical separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setFixedWidth(1)
        line.setStyleSheet(f"background-color: {COLORS['border_hover']}; margin: 10px 0px;")
        return line



    def _setup_ribbon_tabs(self):
        """Create tabs and content for the ribbon."""
        
        def wrap_tab(content, label):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(content)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setStyleSheet("background: transparent; border: none;")
            self.ribbon.addTab(scroll, label)

        # --- Tab 1: Giriş ---
        home_tab = QWidget()
        home_layout = QHBoxLayout(home_tab)
        home_layout.setContentsMargins(4, 2, 4, 2)
        home_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        home_layout.setSpacing(0)
        
        proj_frame, proj_layout = self.create_group()
        proj_layout.addWidget(self.create_ribbon_btn("Yeni\nProje", "Yeni bir nitel araştırma projesi başlatın.", self._new_project, "📁", COLORS['action_new'], overlay="➕"))
        proj_layout.addWidget(self.create_ribbon_btn("Projeyi\nAç", "Mevcut LexiScholar projenizi bilgisayardan yükleyin.", self._load_project, "📂", COLORS['action_new']))
        proj_layout.addWidget(self.create_ribbon_btn("Projeyi\nKaydet", "Tüm kodlamaları ve proje verilerini veritabanına kaydedin.", self._save_project, "💾", COLORS['action_save']))
        proj_layout.addWidget(self.create_ribbon_btn("Farklı\nKaydet", "Projenin bir yedeğini farklı bir dosya ismiyle oluşturun.", self._save_project_as, "💾", "#6366F1", overlay="✏️"))
        home_layout.addWidget(proj_frame)

        # Added Missing buttons: Journal & Coders
        mgmt_frame, mgmt_layout = self.create_group()
        mgmt_layout.addWidget(self.create_ribbon_btn("Proje\nGünlüğü", "Araştırma sürecine dair notlar ve reflektif düşüncelerinizi günlüğe kaydedin.", self._show_journal_dialog, "📔", COLORS['action_view']))
        mgmt_layout.addWidget(self.create_ribbon_btn("Kodlayıcı\nYönetimi", "Projedeki farklı kodlayıcıları yönetin ve aktif kodlayıcıyı seçin.", self._manage_coders, "👤", COLORS['primary_600']))
        home_layout.addWidget(mgmt_frame)

        exp_frame, exp_layout = self.create_group(has_divider=False)
        btn_export = self.create_ribbon_btn("Dışa\nAktar", "Analiz raporlarını, kod kitaplarını veya proje özetlerini farklı formatlarda kaydedin.", None, "📤", COLORS['action_export'])
        export_menu = QMenu(btn_export)
        export_menu.setStyleSheet(CONTEXT_MENU_STYLE)
        export_menu.addAction("📝 Kod Raporu (TXT)", lambda: self._export_code_report('txt'))
        export_menu.addAction("📄 Kod Raporu (Word)", lambda: self._export_code_report('word'))
        export_menu.addAction("📊 Kod Raporu (Excel)", lambda: self._export_code_report('xlsx'))
        export_menu.addAction("📓 Kod Raporu (Markdown)", lambda: self._export_code_report('md'))
        export_menu.addAction("📁 Kod Verisi (JSON)", lambda: self._export_code_report('json'))
        export_menu.addSeparator()
        export_menu.addAction("📘 Kod Kitabı (Codebook)", self._export_codebook)
        export_menu.addAction("📊 Proje Özeti (Dashboard)", self._show_project_summary_report)
        export_menu.addSeparator()
        export_menu.addAction("📝 Memo Raporu (Word)", lambda: self._export_memo_report('word'))
        export_menu.addAction("📄 Memo Raporu (Metin)", lambda: self._export_memo_report('txt'))
        btn_export.setMenu(export_menu)
        btn_export.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        exp_layout.addWidget(btn_export)
        home_layout.addWidget(exp_frame)
        
        wrap_tab(home_tab, "Giriş")

        # --- Tab 2: İçe Aktar ---
        import_tab = QWidget()
        import_layout = QHBoxLayout(import_tab)
        import_layout.setContentsMargins(4, 4, 4, 4)
        import_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        imp_frame, imp_layout = self.create_group(has_divider=False)
        imp_layout.addWidget(self.create_ribbon_btn("Klasör İçe\nAktar", "Bir klasör dolusu PDF, Word veya metin belgesini topluca projeye ekleyin.", lambda: self.document_tree._import_folder(), "📁", COLORS['action_export'], overlay="⚡"))
        imp_layout.addWidget(self.create_ribbon_btn("Belge İçe\nAktar", "Tekil belgeleri (PDF, DOCX, TXT) projenize ekleyin.", lambda: self.document_tree._import_document(), "📄", COLORS['action_export'], overlay="➕"))
        imp_layout.addWidget(self.create_ribbon_btn("Anket İçe\nAktar", "Excel anket verilerini belge ve değişkenlere ayırarak içe aktarın.", self._show_survey_import_dialog, "📊", COLORS['primary_600'], overlay="✨"))
        imp_layout.addWidget(self.create_ribbon_btn("Ses/Video\nÇevir", "Yapay Zeka (Whisper) kullanarak ses ve video kayıtlarını metne dönüştürün.", self._show_transcription_dialog, "🎙️", COLORS['action_save']))
        import_layout.addWidget(imp_frame)
        wrap_tab(import_tab, "İçe Aktar")

        # --- Tab 3: Kodlar ve Memolar ---
        codes_tab = QWidget()
        codes_layout = QHBoxLayout(codes_tab)
        codes_layout.setContentsMargins(4, 4, 4, 4)
        codes_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        c_frame, c_layout = self.create_group()
        c_layout.addWidget(self.create_ribbon_btn("Yeni\nKod", "Seçilen metinleri kategorize etmek için yeni bir kod/etiket oluşturun.", lambda: self.code_tree._create_code(None), "🏷️", COLORS['action_delete'])) 
        c_layout.addWidget(self.create_ribbon_btn("Bul ve\nKodla", "Tüm belgelerde kelime araması yapın ve toplu kodlama işlemi gerçekleştirin.", self._show_search_dialog, "🔦", COLORS['action_search']))
        c_layout.addWidget(self.create_ribbon_btn("Kod\nBulutu", "Projedeki kodların kullanım sıklığını görsel bir bulut olarak inceleyin.", self._show_code_cloud, "☁️", COLORS['action_view']))
        c_layout.addWidget(self.create_ribbon_btn("İlişki\nAğı", "Hangi kodların birbiriyle ilişkili olduğunu bir ağ grafiği üzerinde görün.", self._show_code_graph, "🕸️", COLORS['action_search']))
        codes_layout.addWidget(c_frame)
        
        m_frame, m_layout = self.create_group(has_divider=False)
        m_layout.addWidget(self.create_ribbon_btn("Yeni Serbest\nMemo", "Belli bir belgeye bağlı olmayan genel araştırma notları oluşturun.", self._create_free_memo, "✍️", COLORS['action_new']))
        m_layout.addWidget(self.create_ribbon_btn("Not\nDeposu", "Projedeki tüm araştırma notlarını ve teorik memoları yönetin.", lambda: self._show_memo_manager(focus_search=False), "📚", COLORS['action_export']))
        codes_layout.addWidget(m_frame)
        wrap_tab(codes_tab, "Kodlama ve Notlar")

        # --- Tab 4: Analiz (Nitel Analiz) ---
        analysis_tab = QWidget()
        analysis_layout = QHBoxLayout(analysis_tab)
        analysis_layout.setContentsMargins(4, 2, 4, 2)
        analysis_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        analysis_layout.setSpacing(0)

        # Sorgulama
        q_frame, q_layout = self.create_group()
        q_layout.addWidget(self.create_ribbon_btn("Gelişmiş\nSorgu", "Mantıksal operatörler (VE, VEYA) kullanarak karmaşık kod aramaları yapın.", self._on_query_requested, "🔬", COLORS['action_search']))
        q_layout.addWidget(self.create_ribbon_btn("Metin\nTara", "Aktif belgelerin içeriğinde hızlı kelime veya cümle araması yapın.", self._show_document_search, "🔍", COLORS['primary_600']))
        analysis_layout.addWidget(q_frame)

        # Matrisler & Tablolar (Single row)
        m_frame, m_layout = self.create_group()
        m_layout.addWidget(self.create_ribbon_btn("Kod\nMatrisi", "Kodların belgelere veya gruplara göre dağılımını matris olarak inceleyin.", self._show_code_matrix, "🔲", COLORS['action_view']))
        m_layout.addWidget(self.create_ribbon_btn("Özet\nIzgarası", "Kodlanmış segmentleri ve özetlerini bir ızgara üzerinde yan yana görün.", self._show_summary_grid, "📋", COLORS['action_save']))
        m_layout.addWidget(self.create_ribbon_btn("Kod\nİstatist.", "Kodların kullanım sayıları ve karakter uzunluklarını listeleyin.", self._show_statistics, "📊", COLORS['action_view']))
        analysis_layout.addWidget(m_frame)

        # Araçlar
        t_frame, t_layout = self.create_group()
        t_layout.addWidget(self.create_ribbon_btn("Değişken\nTara", "Belgelere atanmış demografik veya kategorik değişkenleri yönetin.", self._show_variable_manager, "🧪", COLORS['action_new']))
        t_layout.addWidget(self.create_ribbon_btn("Veri\nTablosu", "Tüm belge değişkenlerini Excel benzeri bir tabloda düzenleyin.", self._show_data_editor, "📂", COLORS['action_new']))
        t_layout.addWidget(self.create_ribbon_btn("Değişken\nİstatist.", "Değişkenlerin dağılımını (frekans ve yüzde) tablo olarak görün.", self._show_variable_statistics, "📊", COLORS['action_view']))
        t_layout.addWidget(self.create_ribbon_btn("Analist\nUyumu", "İki farklı kodlayıcının kodlama tutarlılığını (Reliability) analiz edin.", self._show_irr_analysis, "🤝", COLORS['action_save']))
        t_layout.addWidget(self.create_ribbon_btn("Belgeleri\nKıyasla", "İki belgeyi kodlamaları veya içerikleri açısından yan yana karşılaştırın.", self._show_comparison, "⚖️", COLORS['action_view']))
        analysis_layout.addWidget(t_frame)

        # Görselleştirme (New Group)
        v_frame, v_layout = self.create_group(has_divider=False)
        v_layout.addWidget(self.create_ribbon_btn("Grafik\nGalerisi", "Kodları ve değişkenleri pasta, sütun ve halka grafiklerle görselleştirin.", self._show_visualization_gallery, "📈", COLORS['action_export']))
        analysis_layout.addWidget(v_frame)

        wrap_tab(analysis_tab, "Analiz")

        # --- Tab 5: Karma Yöntemler (Mixed Methods) ---
        mixed_tab = QWidget()
        mixed_layout = QHBoxLayout(mixed_tab)
        mixed_layout.setContentsMargins(4, 2, 4, 2)
        mixed_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        m_frame, m_layout = self.create_group(has_divider=False)
        m_layout.addWidget(self.create_ribbon_btn("Değişkenlere\nGöre Etkinleştir", "Belgeleri değişken koşullarına göre filtrele ve aktif hale getir.", self._show_activate_by_variables, "🔍", COLORS['primary_600']))
        m_layout.addWidget(self.create_ribbon_btn("Değişkenlere\nGöre Alıntılar", "Bir kodun farklı değişken değerlerine göre dağılımını metin olarak inceleyin.", self._show_quotes_by_variables, "💡", COLORS['primary_600']))
        m_layout.addWidget(self.create_ribbon_btn("Alıntı\nMatrisi", "Kod × Değişken matrisinde alıntı sayılarını gör ve incele.", self._show_quote_matrix, "🔣", COLORS['primary_600']))
        m_layout.addWidget(self.create_ribbon_btn("Çapraz\nTablo", "Kodları demografik veya kategorik değişkenlerle kıyaslayın.", self._show_crosstabs, "📊", COLORS['primary_600']))
        m_layout.addWidget(self.create_ribbon_btn("Yan Yana\nGörüntüle", "İki değişken grubunu yan yana kıyasla.", self._show_side_by_side, "🆚", COLORS['primary_600']))
        m_layout.addWidget(self.create_ribbon_btn("Varyans\nAnalizi", "Kod frekanslarını gruplar arasında istatistiksel olarak (ANOVA) kıyasla.", self._show_variance_analysis, "📉", COLORS['primary_600']))
        mixed_layout.addWidget(m_frame)
        
        wrap_tab(mixed_tab, "Karma Yöntemler")

        # --- Tab 6: AI Araçları (Yapay Zeka & NLP) ---
        ai_tab = QWidget()
        ai_layout = QHBoxLayout(ai_tab)
        ai_layout.setContentsMargins(4, 2, 4, 2)
        ai_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # NLP Tools (Single row)
        nlp_f, nlp_l = self.create_group()
        nlp_l.addWidget(self.create_ribbon_btn("Duygu\nAnalizi", "Yapay zeka ile metinlerdeki olumlu/olumsuz duygu tonunu tespit edin.", self._show_sentiment_analysis, "🎭", COLORS['action_search']))
        nlp_l.addWidget(self.create_ribbon_btn("Konu\nTespiti", "Belgelerdeki gizli ana temaları otomatik olarak gruplandırın (LDA).", self._show_topic_modeling, "🗂️", COLORS['action_new']))
        nlp_l.addWidget(self.create_ribbon_btn("Varlık\nTanıma", "Metinlerdeki kişi, kurum ve yer isimlerini otomatik olarak işaretleyin (NER).", self._show_ner_analysis, "🏷️", COLORS['action_export']))
        nlp_l.addWidget(self.create_ribbon_btn("Anahtar\nKelimeler", "Metinlerde en önemli ve belirleyici olan kavramları otomatik olarak ayıklayın.", self._show_keyword_extraction, "🔑", COLORS['action_search']))
        nlp_l.addWidget(self.create_ribbon_btn("Anlamsal\nHarita", "Sınıf ve metin anlamlarını çok boyutlu bir uzayda kümeleyerek görselleştirin.", self._show_semantic_map, "🌌", COLORS['action_new']))
        nlp_l.addWidget(self.create_ribbon_btn("Bağlam içi\nKelime", "Bir kelimenin geçtiği yerleri sağ ve sol bağlamıyla listeleyin (KWIC).", self._show_kwic_dialog, "🎯", COLORS['primary_600']))
        nlp_l.addWidget(self.create_ribbon_btn("Kelime\nSayımı", "Bütün kelimelerin kullanım sıklıklarını ve dağılımlarını görün.", self._show_word_frequency, "🔢", COLORS['action_view']))
        ai_layout.addWidget(nlp_f)
        
        # Visuals (Single row)
        viz_f, viz_l = self.create_group(has_divider=False)
        viz_l.addWidget(self.create_ribbon_btn("Kelime\nBulutu", "En çok geçen kelimeleri boyutlarına göre görselleştirin.", self._show_word_cloud, "☁️", COLORS['action_export']))
        viz_l.addWidget(self.create_ribbon_btn("Kod\nYoğunluğu", "Kodların belgelerdeki yoğunluğunu gösteren ısı haritası ve dağılım.", self._show_code_coverage, "🌡️", COLORS['warning']))
        viz_l.addWidget(self.create_ribbon_btn("Kod\nZamanı", "Belge akışı boyunca kodların nerede geçtiğini gösteren zaman çizelgesi.", self._show_code_timeline, "⏲️", COLORS['action_export']))
        viz_l.addWidget(self.create_ribbon_btn("Belge\nResmi", "Belge yapısını kod renkleriyle bir desen (Portrait) olarak görselleştirin.", self._show_document_portrait, "🖼️", COLORS['action_view']))
        viz_l.addWidget(self.create_ribbon_btn("Akış\nDiyagramı", "Kodlar arasındaki geçişleri ve ilişki akışını Sankey diyagramı ile görün.", self._show_sankey_diagram, "🌊", COLORS['action_search']))
        ai_layout.addWidget(viz_f)
        
        wrap_tab(ai_tab, "Yapay Zeka")

        # --- Tab 7: Yardım ---
        h_tab = QWidget()
        h_layout = QHBoxLayout(h_tab)
        h_layout.setContentsMargins(4, 4, 4, 4)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        h_f, h_l = self.create_group(has_divider=False)
        h_l.addWidget(self.create_ribbon_btn("Bilgi\nAnsiklopedisi", "Programın her özelliğini detaylıca açıklayan kapsamlı bilgi veri tabanı.", self._show_manual, "📖", COLORS['action_help']))
        h_l.addWidget(self.create_ribbon_btn("Kısayollar", "Uygulama içi klavye kısayollarını görüntüleyin.", lambda: self.shortcut_manager.show_cheat_sheet(), "⌨️", COLORS['action_view']))
        h_l.addWidget(self.create_ribbon_btn("Dil Modeli\nKontrolü", "Lokal dil modellerinde güncelleme olup olmadığını kontrol edin; varsa indirip güncelleyin.", self._check_updates, "🔄", COLORS['primary_600']))
        h_l.addWidget(self.create_ribbon_btn("Hakkında", "LexiScholar versiyon ve geliştirici bilgileri.", self._show_about, "ℹ️", COLORS['action_undo']))
        h_layout.addWidget(h_f)
        wrap_tab(h_tab, "Yardım")

    def _setup_corner_controls(self):
        """Setup persistent global controls in the ribbon's top-right corner."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 4, 0) # Right margin for spacing
        layout.setSpacing(2)
        
        def create_corner_btn(symbol, tooltip, callback, font_size=13, plain_text=False):
            btn = QPushButton()
            btn.setToolTip(tooltip)
            btn.setStatusTip(tooltip)
            btn.setAccessibleName(tooltip.split("(")[0].strip())
            btn.setAccessibleDescription(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if callback:
                btn.clicked.connect(callback)
            btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            if plain_text:
                btn.setText(symbol)
            else:
                btn.setIcon(IconProvider.get_icon(symbol, COLORS['text_secondary']))
                btn.setIconSize(QSize(18, 18))
            btn.setFixedSize(32, 28)
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: 1px solid transparent;
                    border-radius: 4px;
                    padding: 0px;
                    font-size: {font_size}px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['ribbon_hover']};
                    border: 1px solid {COLORS['border_hover']};
                    color: {COLORS['primary_600']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['border']};
                }}
            """)
            return btn

        # Undo/Redo (Standard Symbols)
        btn_undo = create_corner_btn("↩", "Geri Al (Ctrl+Z)", self._undo, 14, plain_text=True)
        btn_redo = create_corner_btn("↪", "Yinele (Ctrl+Y)", self._redo, 14, plain_text=True)
        self.btn_undo = btn_undo
        self.btn_redo = btn_redo
        
        # Layout Toggle (Custom Drawn for perfect symmetry)
        self.btn_layout_toggle = QPushButton()
        self.btn_layout_toggle.setToolTip("Ekran Düzeni (Ctrl+L)")
        self.btn_layout_toggle.setStatusTip("Ekran Düzeni (Ctrl+L)")
        self.btn_layout_toggle.setAccessibleName("Ekran Düzeni")
        self.btn_layout_toggle.setAccessibleDescription("Panel yerleşimini yatay veya dikey moda geçirir.")
        self.btn_layout_toggle.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_layout_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_layout_toggle.clicked.connect(self._toggle_layout)
        self.btn_layout_toggle.setIcon(IconProvider.get_layout_icon("vertical", COLORS['text_secondary']))
        self.btn_layout_toggle.setIconSize(QSize(18, 18))
        self.btn_layout_toggle.setFixedSize(32, 28)
        self.btn_layout_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['ribbon_hover']};
                border: 1px solid {COLORS['border_hover']};
                color: {COLORS['primary_600']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
        """)
        
        # AI Settings
        btn_ai_settings = create_corner_btn("🤖", "Yapay Zeka Ayarları", self._show_ai_settings)
        self.btn_ai_settings = btn_ai_settings

        # Guide
        btn_guide = create_corner_btn("🎓", "Yardımcı Rehber (Ctrl+T)", self._show_onboarding)
        self.btn_guide = btn_guide



        layout.addWidget(btn_undo)
        layout.addWidget(btn_redo)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedSize(1, 16)
        line.setStyleSheet(f"background-color: {COLORS['border']}; margin: 6px 4px;")
        layout.addWidget(line)

        layout.addWidget(self.btn_layout_toggle)
        layout.addWidget(btn_ai_settings)
        layout.addWidget(btn_guide)

        # Determine corner (TopRight is standard for tab widgets)
        self.ribbon.setCornerWidget(container, Qt.Corner.TopRightCorner)

        # CRITICAL: Store reference for Onboarding tutorial
        self.persistent_controls_widget = container
