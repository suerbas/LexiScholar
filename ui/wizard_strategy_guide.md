# Wizard Stratejisi Standardizasyon Rehberi

## 🎯 Genel Kural

**"Modern Wizard Experience" - Tüm wizard'lar aynı UX prensibine sahip olmalı.**

---

## 📋 Wizard Türleri ve Stratejileri

### ✅ QWizard (Öncelikli Tercih)
**Kullanım alanları:**
- **SurveyImportWizard** - Çok adımlı veri içe aktarım
- **Export Wizards** - Karmaşık dışa aktarım süreçleri
- **Configuration Wizards** - Ayar sihirbazları

**Özellikler:**
- Native wizard navigasyonu
- Otomatik step management
- Platform uyumlu
- Built-in next/previous/back buttons

**Standart Yapı:**
```python
class MyWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Modern styling
        self.setStyleSheet(f"""
            QWizard {{
                background-color: {get_color('bg_panel')};
            }}
            QWizardPage {{
                background-color: {get_color('bg_main')};
                border: 1px solid {get_color('border')};
                border-radius: 8px;
                margin: 10px;
            }}
            QLabel {{ color: {get_color('text_primary')}; }}
        """)
        
        # Wizard options
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveCustomButton1, False)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.setOption(QWizard.WizardOption.NoBackButtonOnLastPage, True)
        
        # Setup pages
        self._setup_pages()
    
    def _setup_pages(self):
        """Setup wizard pages with consistent structure."""
        pass
```

---

### ⚠️ ModernBaseDialog Wizard (Özel Durumlar)

**Sadece şu durumlarda:**
- **SetupWizard** - Tek adımlı kurulum süreçleri
- **Simple wizards** - 2-3 adımlı basit süreçler
- **Custom UI gerektiren wizard'lar**

**Özellikler:**
- Frameless modern görünüm
- Özel navigasyon kontrolleri
- Esnek layout tasarımı
- Ribbon header uyumu

**Standart Yapı:**
```python
class MyWizard(ModernBaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, min_width=600, min_height=500)
        
        # Custom navigation
        self._current_step = 0
        self._total_steps = 3
        
        self._setup_ui()
        self._setup_navigation()
    
    def _setup_ui(self):
        """Setup wizard UI with step indicators."""
        self._setup_base_ui()
        
        # Header with progress
        header = self.build_ribbon_header("🧙", "Wizard Başlığı")
        self.layout.addWidget(header)
        
        # Progress indicator
        self._setup_progress_indicator()
        
        # Content area
        self._setup_content_area()
        
        # Navigation buttons
        self._setup_navigation_buttons()
```

---

## 🎨 Ortak UX Prensipleri

### 1. Progress İndicators
**QWizard için:**
- Otomatik step göstergeleri
- Progress bar (isteğe bağlı)

**ModernBaseDialog için:**
- Dot indicators (●○○)
- Step numbers (1/3)
- Progress bar

### 2. Navigation Standartları
**Buton sırası:** `[Previous] [İptal] [İleri] [Bitir]`

**Buton davranışları:**
- Previous: İlk adımda devre dışı
- Next/Finish: Son adımda "Bitir" olur
- Cancel: Her zaman aktif

### 3. Validation Standartları
- Her adımda validation
- Error mesajları consistent
- Next butonu validation'a bağlı

---

## 📐 Layout Standardizasyonu

### QWizard Page Yapısı
```python
class MyWizardPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Adım Başlığı")
        self.setSubTitle("Adım açıklaması")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Content
        self._setup_content()
    
    def _setup_content(self):
        """Setup page content."""
        pass
    
    def validatePage(self):
        """Validate current page before proceeding."""
        return True
```

### ModernBaseDialog Wizard Yapısı
```python
def _setup_content_area(self):
    """Setup main content area with step content."""
    self.content_stack = QStackedWidget()
    
    # Add step widgets
    for i in range(self._total_steps):
        step_widget = self._create_step_widget(i)
        self.content_stack.addWidget(step_widget)
    
    self.layout.addWidget(self.content_stack, 1)
```

---

## 🔧 Geçiş Stratejisi

### Mevcut Wizard'ları Dönüştürme

**SetupWizard (ModernBaseDialog → QWizard):**
1. **Avantajları**: Native navigation, consistency
2. **Dezavantajları**: Özellik kaybı (custom logs)
3. **Karar**: ModernBaseDialog'da kalmak (özellikler kritik)

**SurveyImportWizard (QWizard → ModernBaseDialog):**
1. **Avantajları**: Modern görünüm, esnek layout
2. **Dezavantajları**: Native navigation kaybı
3. **Karar**: QWizard'da kalmak (complexity düşük)

### Yeni Wizard Kuralları

**Kullanım kriterleri:**
- **3+ adım** → QWizard
- **Özel UI gerekiyorsa** → ModernBaseDialog
- **Native look önemliyse** → QWizard
- **Esnek layout gerekirse** → ModernBaseDialog

---

## 📝 Kontrol Listesi

Yeni wizard oluştururken:
- [ ] Doğru wizard tipi seçildi mi?
- [ ] Progress indicator var mı?
- [ ] Navigation standartlarına uyuyor mu?
- [ ] Validation mekanizması var mı?
- [ ] Error handling consistent mi?
- [ ] Accessibility destekleniyor mu?
- [ ] Responsive tasarım yapıldı mı?
- [ ] Platform uyumlu mu?

---

## 🚀 İyileştirme Önerileri

### Kısa Vadeli (P0)
- SurveyImportWizard styling'i güncelle
- Progress indicator standardizasyonu
- Navigation button consistency

### Orta Vadeli (P1)
- SetupWizard'ı QWizard'a dönüştür (özellikler korunarak)
- Common wizard base class oluşturma
- Validation framework'i

### Uzun Vadeli (P2)
- Wizard template generator
- Automated testing framework
- Advanced progress indicators
