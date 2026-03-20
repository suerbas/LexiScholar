from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QWidget, QTextBrowser, 
    QPushButton, QHBoxLayout, QLabel, QFrame, 
    QLineEdit, QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap
from ui.icons import IconProvider
from ui.styles import DIALOG_STYLE, get_color
from __version__ import APP_DISPLAY_VERSION
from .common.modern_dialog import ModernBaseDialog

HELP_CONTENT = {
    "Hoş Geldiniz": {
        "tags": ["başlangıç", "giriş", "welcome", "rehber"],
        "content": """
        <h1>👋 LexiScholar'a Hoş Geldiniz</h1>
        <p>LexiScholar, nitel araştırma süreçlerinizi dijitalleştirmek, hızlandırmak ve derinleştirmek için tasarlanmış profesyonel bir <b>CAQDAS</b> (Bilgisayar Destekli Nitel Veri Analizi Yazılımı) çözümüdür.</p>
        <p>Bu kılavuz, kodlama sisteminden ileri düzey yapay zeka analizlerine kadar projenizin her aşamasında size rehberlik edecektir. Sol taraftaki menüyü kullanarak veya yukarıdaki arama kutusuna <i>"sankey", "değişken", "whisper"</i> gibi terimler yazarak istediğiniz konuya hızlıca ulaşabilirsiniz.</p>
        <div class="note">
            <b>YENİ:</b> Versiyon 3.8 ile gelen <b>Kapsamlı Güvenlik Denetimi İyileştirmeleri</b>, <b>FTS5 Tam Metin Arama Senkronizasyonu</b> ve hibrit AI analizlerindeki kararlılık artışları ile araştırmalarınızı bir üst seviyeye taşıyın.
        </div>
        <h2>Nitel Araştırmada Dijital Yardımcınız</h2>
        <p>LexiScholar, sadece metinleri renklendirmekle kalmaz; mülakatlarınızı deşifre eder (Whisper), metinlerdeki akademik tonu ölçer (Sentiment) ve kodlarınız arasındaki stratejik bağları görselleştirir.</p>
        """
    },
    "Adım 1: Proje Kurulumu": {
        "tags": ["yeni", "aç", "kaydet", "backup", "proje", "veritabanı", "başlangıç"],
        "content": """
        <h1>📁 Proje Yönetimi ve Güvenlik</h1>
        <p>LexiScholar'da her çalışma bir <b>Proje</b> olarak adlandırılır. Projeniz içindeki tüm belgeler, kodlar, memolar ve değişkenler tek bir <code>.db</code> dosyasında saklanır.</p>
        
        <h2>Yeni Bir Çalışma Başlatma</h2>
        <ol>
            <li><b>Giriş</b> sekmesinden <b>Yeni Proje</b> butonuna tıklayın.</li>
            <li>Projeniz için bilgisayarınızda güvenli bir klasör seçin.</li>
            <li>Sistem, tüm veritabanı altyapısını saniyeler içinde kurarak size boş bir çalışma alanı sunacaktır.</li>
        </ol>

        <h2>Otomatik Kayıt ve Yedekleme</h2>
        <p>LexiScholar, "Auto-Save" mimarisiyle çalışır. Yaptığınız her kodlama, yazdığınız her not anında veritabanına işlenir. Elektrik kesintisi gibi durumlarda veri kaybı yaşanmaz.</p>
        
        <div class="note">
            <b>Altın Kural:</b> Önemli analiz evrelerinden (örn. 1. döngü kodlama bittiğinde) sonra <b>Farklı Kaydet</b> butonunu kullanarak "Versiyon 1", "Versiyon 2" şeklinde manuel yedekler oluşturmanız araştırmanızın güvenliği için kritik önemdedir.
        </div>
        """
    },
    "Adım 2: Veri Hazırlama": {
        "tags": ["import", "pdf", "docx", "excel", "txt", "belge", "klasör", "aktar"],
        "content": """
        <h1>📥 Veri İçe Aktarma (Import)</h1>
        <p>Analize başlamadan önce mülakatlar, saha notları veya PDF dökümanları projeye dahil edilmelidir.</p>

        <h2>Desteklenen Dosya Tipleri</h2>
        <ul>
            <li><b>Microsoft Word (.docx)</b>: Mülakat deşifreleri için standart format.</li>
            <li><b>PDF (.pdf)</b>: Akademik makaleler, raporlar ve taranmış belgeler.</li>
            <li><b>Excel (.xlsx)</b>: Anketlerin açık uçlu soruları için idealdir. Her satır ayrı bir döküman olarak alınır.</li>
            <li><b>Metin Dosyaları (.rtf, .txt)</b>: Basit notlar ve ham metinler.</li>
        </ul>

        <h2>Toplu Aktarım Kolaylığı</h2>
        <p><b>Klasör İçe Aktar</b> özelliğini kullanarak, içinde onlarca PDF olan bir klasörü tek tıkla hiyerarşiyi bozmadan sisteme yükleyebilirsiniz.</p>
        
        <div class="note">
            <b>İpucu:</b> PDF belgelerinizin metin tabakasına sahip (selectable text) olduğundan emin olun. Taranmış resim formatındaki PDF'ler kodlanamaz.
        </div>
        """
    },
    "Değişkenler (Variables)": {
        "tags": ["değişken", "demografik", "yaş", "cinsiyet", "crosstab", "çapraz tablo", "survey"],
        "content": """
        <h1>🧪 Değişkenler ve Demografik Veriler</h1>
        <p>Nitel analizi nicel verilerle zenginleştirmek için <b>Değişkenler</b> kullanılır. Örneğin, mülakat yapılan kişilerin <i>Yaş, Cinsiyet, Meslek</i> gibi bilgilerini sisteme tanımlayabilirsiniz.</p>

        <h2>Değişken Tanımlama adımları:</h2>
        <ol>
            <li><b>Analiz</b> sekmesinden <b>Değişkenler</b> butonuna tıklayın.</li>
            <li>Değişken ismini (örn: Cinsiyet) ve tipini (Metin, Sayı) belirleyin.</li>
            <li>Ardından <b>Veri Tablosu</b> (Data Editor) ekranına geçerek, her belge için ilgili değerleri (örn: Kadın/Erkek) girin.</li>
        </ol>

        <h2>Neden Değişken Kullanmalısınız?</h2>
        <p>Değişkenler sayesinde <b>Çapraz Tablo</b> analizi yapabilirsiniz. Örneğin: "30-40 yaş arası katılımcılar 'Çevre Politikaları' kodunu, 20-30 yaş grubuna göre daha mı sık kullanmış?" sorusuna anında yanıt alırsınız.</p>
        """
    },
    "AI Transkripsiyon (Whisper)": {
        "tags": ["audio", "video", "transkripsiyon", "whisper", "ses", "mülakat", "deşifre"],
        "content": """
        <h1>🎙️ Yapay Zeka ile Otomatik Deşifre</h1>
        <p>Mülakat kayıtlarınızı deşifre etmek için aylarca beklemeyin. LexiScholar içinde yerleşik olarak bulunan <b>Whisper AI</b> motoru, ses ve video dosyalarınızı yüksek doğrulukla metne dönüştürür.</p>

        <h2>Deşifre Süreci</h2>
        <ul>
            <li><b>İçe Aktar</b> sekmesinden <b>Ses/Video Çevir</b> butonuna basın.</li>
            <li>Dosyanızı seçin ve model büyüklüğünü belirleyin (Önerilen: <i>Small</i>).</li>
            <li>Sistem metni oluşturduğunda, metin otomatik olarak projeye yeni bir belge olarak eklenir.</li>
        </ul>

        <h2>Etkileşimli Dinleme (Sync)</h2>
        <p>Transkripsiyon sonucunda metne eklenen zaman damgalarına (`[01:22]`) tıkladığınızda, orijinal ses kaydı o saniyeye gider. Böylece deşifre hatalarını kontrol etmek veya tonlamayı dinlemek çok kolaylaşır.</p>

        <div class="note">
            <b>🛡️ Gizlilik Notu:</b> Deşifre işlemi tamamen sizin işlemciniz/ekran kartınız üzerinde yapılır. Ses dosyalarınız internete veya bulut servislerine gönderilmez. KVKK uyumludur.
        </div>
        """
    },
    "Kodlama Stratejileri": {
        "tags": ["coding", "etiket", "kategori", "renk", "in vivo", "sağ tık", "sürükle bırak"],
        "content": """
        <h1>🏷️ Kodlama Sistematiği</h1>
        <p>LexiScholar, tümevarımsal (inductive) veya tümdengelimsel (deductive) analizleriniz için esnek kodlama yöntemleri sunar.</p>

        <h2>Kodlama Yöntemleri</h2>
        <ul>
            <li><b>Sürükle-Bırak:</b> Metni seçin ve soldaki kod ağacındaki kodun üzerine sürükleyin.</li>
            <li><b>In-Vivo Kodlama:</b> Metindeki bir ifadeyi doğrudan kod ismi yapmak için seçip sağ tıklayın.</li>
            <li><b>Hızlı Kodlama:</b> Daha önce oluşturulmuş bir kodu, metni seçip sağ tıklayarak saniyeler içinde atayın.</li>
        </ul>

        <h2>Kod Organizasyonu</h2>
        <p>Kodlarınızı hiyerarşik (ana kod/alt kod) yapıda düzenleyin. Renk paletini kullanarak kodlarınızı kategorize edin. Örneğin, riskleri kırmızı tonlarında, fırsatları yeşil tonlarında gruplayabilirsiniz.</p>
        """
    },
    "Akıllı Analiz (AI & NLP)": {
        "tags": ["ai", "duygu", "ner", "varlık", "sentiment", "keywords", "ton", "akademik"],
        "content": """
        <h1>🤖 Akıllı Analiz ve NLP Araçları</h1>
        <p>Bilgisayarın gücünü kullanarak verilerinizdeki satır aralarını okuyun.</p>

        <h2>Duygu ve Söylem Analizi</h2>
        <p>Sadece kelimeleri değil, anlatıcının tavrını da ölçün. LexiScholar; metnin <b>Pozitif/Negatif</b> dengesini ve <b>Akademik/Eleştirel</b> tonunu analiz eder.</p>

        <h2>Varlık Tanıma (NER)</h2>
        <p>Metinlerde geçen kişi, kurum, lokasyon ve tarih gibi varlıklar otomatik olarak tespit edilir. Bu, vaka analizlerinde "Kim, nerede, ne zaman?" sorularını hızlıca cevaplamanızı sağlar.</p>

        <h2>Otomatik Anahtar Kelimeler</h2>
        <p>YAKE algoritması ile metnin en belirleyici kavramları tek tıkla önünüze gelir. Bu özellik, henüz kodlama yapmadığınız dökümanlara hızlıca göz gezdirmek için harikadır.</p>
        """
    },
    "İleri Görselleştirme": {
        "tags": ["sankey", "heatmap", "timeline", "viz", "görsel", "analiz"],
        "content": """
        <h1>📊 Veriyi Görselleştirme</h1>
        <p>Nitel bulguları görsel kanıtlarla desteklemek, çalışmanızın ikna ediciliğini artırır.</p>

        <h2>Akış Diyagramı (Sankey)</h2>
        <p>Kodların birbiriyle olan dinamik ilişkisini ve co-occurrence (birlikte görülme) akışını estetik bir grafik olarak sunar.</p>

        <h2>Kod Yoğunluğu (Heatmap)</h2>
        <p>Belge grubu bazında kodların ne kadar yoğun kullanıldığını bir ısı haritası üzerinden izleyin. Koyu renkler yüksek yoğunluğu temsil eder.</p>

        <h2>Etkileşimli Kelime Bulutu</h2>
        <p>Frekans tabanlı kelime bulutu ile metnin temalarını görselleştirin. Kelimelerin büyüklüğünü kontrol ederek görselin estetiğini ayarlayabilirsiniz.</p>
        """
    },
    "Raporlama ve Yazım": {
        "tags": ["rapor", "export", "çıktı", "summary grid", "özet", "akademik", "word"],
        "content": """
        <h1>📝 Bulguların Raporlanması</h1>
        <p>Analizinizi makale formatına dönüştürme aşamasında LexiScholar size çeşitli araçlar sunar.</p>
        
        <h2>Dışa Aktarma Formatları</h2>
        <p>Kodladığınız tüm segmentleri veya projenin tamamını <b>Word, TXT, JSON veya HTML</b> formatlarında dışa aktarabilirsiniz.</p>

        <h2>Özet Izgarası (Summary Grid)</h2>
        <p>Bu ekran, ham döküman metniyle sizin analitik yorumunuzu yan yana getirir. Her kodlama için kendi yorumunuzu yazabilir ve bu yorumları topluca raporlayabilirsiniz.</p>

        <h2>Kod Kitabı (Codebook)</h2>
        <p>Araştırmanızın güvenilirliği için kod tanımlarınızı (memolarınızı) içeren profesyonel bir Kod Kitabı PDF/Word dökümanı oluşturabilirsiniz.</p>
        """
    },
    "Geri Çağırma (Retrieval)": {
        "tags": ["retrieval", "filtre", "aktif", "criter", "sorgu"],
        "content": """
        <h1>🔍 Bölüm Geri Çağırma (Retrieval)</h1>
        <p>İhtiyacınız olan spesifik veri parçalarına ulaşmanın en hızlı yolu <b>Etkinleştirme</b> sistemidir.</p>

        <h2>Analiz Odaklama</h2>
        <p>Diyelim ki sadece "X şehri"nde yapılan mülakatlardaki "Eğitim" kodlu bölümleri görmek istiyorsunuz:</p>
        <ol>
            <li>O şehre ait belgeleri yanındaki daireye tıklayarak aktif edin (Kırmızı olur).</li>
            <li>Kod listesinden "Eğitim" kodunu aktif edin.</li>
            <li>Sağ alttaki <b>Geri Çağrılan Bölümler</b> paneli sadece bu iki kriter kesişen bölümleri gösterecektir.</li>
        </ol>
        """
    }
}

class HelpWindow(QDialog):
    """
    Enhanced Wiki-style User Manual with Search.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LexiScholar Wiki - Kullanım Kılavuzu")
        self.resize(1100, 750)
        self.setStyleSheet(DIALOG_STYLE)
        
        self._setup_ui()
        self._load_section("Hoş Geldiniz")
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header (Fixed height and focused UI)
        header = QFrame()
        header.setFixedHeight(85) # Increased height for better readability
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('bg_main')}; 
                border-bottom: 2px solid {get_color('border')}; 
                padding: 10px 20px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 8, 20, 8) # Added vertical margin to prevent clipping
        
        icon_label = QLabel()
        icon_label.setPixmap(IconProvider.get_icon("🎓", get_color('primary'), 28).pixmap(28, 28))
        header_layout.addWidget(icon_label)
        
        title = QLabel("LexiScholar Wiki")
        title.setStyleSheet(f"""
            font-size: 20px; 
            font-weight: 800; 
            color: {get_color('text_primary')}; 
            margin-right: 30px;
            letter-spacing: -0.5px;
        """)
        header_layout.addWidget(title)
        
        # Professional Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Kılavuzda ara... (örn: whisper, kodlama, NLP)")
        self.search_box.setFixedWidth(450)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {get_color('bg_panel')};
                border: 1px solid {get_color('border')};
                border-radius: 8px;
                padding: 8px 15px;
                font-size: 13px;
                color: {get_color('text_secondary')};
            }}
            QLineEdit:focus {{
                background-color: {get_color('bg_main')};
                border: 2px solid {get_color('primary')};
            }}
        """)
        self.search_box.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_box)
        
        header_layout.addStretch()
        
        # Web Guide Button (Prominent)
        self.btn_web_guide = QPushButton("🌐 Detaylı Kılavuzu Aç (HTML)")
        self.btn_web_guide.setFixedSize(220, 32)
        self.btn_web_guide.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_web_guide.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {get_color('accent')}; /* Amber/Accent color to stand out */
                border: none;
                border-radius: 6px;
                color: {get_color('text_inverse')};
                font-size: 13px;
                font-weight: 700;
            }} 
            QPushButton:hover {{ 
                background-color: {get_color('accent_dark')};
            }}
        """)
        self.btn_web_guide.clicked.connect(self._open_web_guide)
        header_layout.addWidget(self.btn_web_guide)
        
        # Clear Close Button (Professional Text Button)
        self.btn_close_top = QPushButton("Kapat")
        self.btn_close_top.setFixedSize(100, 32)
        self.btn_close_top.clicked.connect(self.accept)
        self.btn_close_top.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_top.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {get_color('bg_panel')};
                border: 1px solid {get_color('border')};
                border-radius: 6px;
                color: {get_color('text_muted')};
                font-size: 13px;
                font-weight: 600;
            }} 
            QPushButton:hover {{ 
                background-color: {get_color('error_bg')};
                color: {get_color('error')}; 
                border-color: {get_color('error')};
            }}
        """)
        header_layout.addWidget(self.btn_close_top)
        
        main_layout.addWidget(header)
        
        # Splitter for Sidebar and Content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {get_color('border')}; width: 1px; }}")
        
        # Sidebar
        sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sidebar_list = QListWidget()
        self.sidebar_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {get_color('bg_sidebar')};
                border: none;
                font-size: 13px;
                padding: 15px 10px;
                outline: none; /* CRITICAL FIX: Removes the black focus rectangle */
            }}
            QListWidget::item {{
                background-color: {get_color('ribbon_bg')}; /* Pastel Blue - Matches Ribbon Tabs */
                color: {get_color('text_secondary')};
                padding: 10px 15px;
                border-radius: 6px;
                margin-bottom: 6px;
                border: 1px solid transparent;
            }}
            QListWidget::item:selected {{
                background-color: {get_color('ribbon_active')}; /* Pastel Orange - Matches Active Ribbon */
                color: {get_color('text_primary')};
                font-weight: bold;
                border: 1px solid {get_color('border')};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {get_color('primary_100')}; /* Darker blue hover */
                color: {get_color('text_primary')};
            }}
        """)
        for section in HELP_CONTENT.keys():
            self.sidebar_list.addItem(section)
            
        self.sidebar_list.currentTextChanged.connect(self._load_section)
        sidebar_layout.addWidget(self.sidebar_list)
        
        splitter.addWidget(sidebar_container)
        
        # Main View (TextBrowser)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {get_color('bg_main')};
                border: none;
                padding: 30px 50px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 15px;
                line-height: 1.7;
                color: {get_color('text_secondary')};
            }}
        """)
        splitter.addWidget(self.browser)
        
        splitter.setSizes([260, 840])
        main_layout.addWidget(splitter)
        
    def _open_web_guide(self):
        """Opens the detailed HTML guide in the default web browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        import os
        
        guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "kullanim_kilavuzu.html")
        if os.path.exists(guide_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(guide_path))
            
    def _load_section(self, section_name):
        if not section_name or section_name not in HELP_CONTENT:
            return
            
        content = HELP_CONTENT[section_name]["content"]
        style = f"""
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; color: {get_color('text_secondary')}; }}
            h1 {{ color: {get_color('text_primary')}; font-size: 32px; margin-bottom: 25px; border-bottom: 2px solid {get_color('bg_panel')}; padding-bottom: 12px; font-weight: 800; }}
            h2 {{ color: {get_color('primary')}; font-size: 22px; margin-top: 35px; margin-bottom: 12px; font-weight: 700; }}
            p {{ margin-bottom: 18px; }}
            ul, ol {{ margin-bottom: 20px; padding-left: 20px; }}
            li {{ margin-bottom: 10px; }}
            b {{ color: {get_color('text_primary')}; font-weight: 700; }}
            i {{ color: {get_color('text_muted')}; }}
            .note {{ background-color: {get_color('primary_50')}; border-left: 4px solid {get_color('primary')}; padding: 20px; color: {get_color('text_primary')}; margin: 25px 0; border-radius: 0 8px 8px 0; font-size: 14px; }}
            .note b {{ color: {get_color('text_primary')}; }}
        </style>
        """
        self.browser.setHtml(style + "<body>" + content + "</body>")
        # Scroll to top
        self.browser.verticalScrollBar().setValue(0)
        
    def _on_search(self, text):
        text = text.lower().strip()
        self.sidebar_list.clear()
        
        if not text:
            for section in HELP_CONTENT.keys():
                self.sidebar_list.addItem(section)
            return
            
        results = []
        for section, data in HELP_CONTENT.items():
            # Search in Title, Content, or Tags
            if (text in section.lower() or 
                text in data["content"].lower() or 
                any(text in tag.lower() for tag in data["tags"])):
                results.append(section)
        
        if results:
            self.sidebar_list.addItems(results)
        else:
            self.sidebar_list.addItem("Sonuç bulunamadı.")

class AboutDialog(ModernBaseDialog):
    """
    Displays 'About' information dynamically modernized with ModernBaseDialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent, min_width=500, min_height=350)
        self._setup_ui()
        
    def _setup_ui(self):
        self._setup_base_ui()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left Panel (Gradient)
        left_panel = QFrame()
        left_panel.setFixedWidth(160)
        left_panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {get_color('primary_dark')}, stop:1 {get_color('primary')});
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
                margin: 0;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 30, 10, 30)
        left_layout.addStretch()
        
        icon_label = QLabel("🎓")
        icon_label.setStyleSheet(f"font-size: 70px; color: {get_color('text_inverse')}; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(icon_label)
        left_layout.addStretch()
        
        # Right Panel (Content)
        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{ 
                background: {get_color('bg_main')}; 
                border-top-right-radius: 16px; 
                border-bottom-right-radius: 16px; 
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(30, 20, 20, 20)
        right_layout.setSpacing(15)
        
        # Close button inside right panel top-right
        close_top_layout = QHBoxLayout()
        close_top_layout.addStretch()
        close_btn_top = QPushButton("✕")
        close_btn_top.setFixedSize(32, 32)
        close_btn_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_top.clicked.connect(self.reject)
        close_btn_top.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {get_color('text_muted')}; font-size: 18px; font-weight: bold; border: none; border-radius: 16px; }}
            QPushButton:hover {{ background: {get_color('error_bg')}; color: {get_color('error')}; }}
        """)
        close_top_layout.addWidget(close_btn_top)
        right_layout.addLayout(close_top_layout)
        
        title = QLabel("LexiScholar")
        title.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {get_color('text_primary')}; background: transparent;")
        right_layout.addWidget(title)
        
        version = QLabel(f"Sürüm: {APP_DISPLAY_VERSION}")
        version.setStyleSheet(f"font-size: 14px; color: {get_color('primary')}; font-weight: 700; background: transparent;")
        right_layout.addWidget(version)
        
        desc = QLabel("Nitel Veri Analizi ve Akademik Yazım Aracı")
        desc.setStyleSheet(f"font-size: 14px; color: {get_color('text_secondary')}; background: transparent;")
        desc.setWordWrap(True)
        right_layout.addWidget(desc)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {get_color('border')}; background: transparent;")
        right_layout.addWidget(line)
        
        dev = QLabel("<b>Geliştirici:</b> Suat Erbaş<br><i>(C) 2026 - Tüm Hakları Saklıdır</i>")
        dev.setStyleSheet(f"font-size: 13px; color: {get_color('text_muted')}; background: transparent; line-height: 1.4;")
        right_layout.addWidget(dev)
        right_layout.addStretch()
        
        # Bottom right confirmation
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Tamam")
        btn_close.setFixedWidth(100)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(f"""
            QPushButton {{ background-color: {get_color('primary')}; color: {get_color('text_inverse')}; border-radius: 6px; padding: 10px; font-weight: 700; font-size: 13px; }}
            QPushButton:hover {{ background-color: {get_color('primary_dark')}; }}
        """)
        btn_layout.addWidget(btn_close)
        right_layout.addLayout(btn_layout)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, stretch=1)
        self.layout.addLayout(main_layout)
