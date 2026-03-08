# Dialog Standardizasyon Rehberi

## 🎯 Genel Kural

**"Modern Frameless First" stratejisi - Tüm yeni dialoglar `ModernBaseDialog` kullanmalı.**

---

## 📋 Dialog Türleri ve Kullanım Alanları

### ✅ ModernBaseDialog (Öncelikli Tercih)
**Kullanım alanları:**
- Ana ayar dialogları (`SettingsDialog`, `AI_SettingsDialog`)
- Veri yönetimi dialogları (`ProjectDialog`, `VariableManagerDialog`)
- Analiz ve raporlama dialogları (`StatisticsDialog`, `ExportDialog`)
- İçe/dışa aktarım dialogları (`SurveyImportWizard`, `DocumentImportDialog`)

**Özellikler:**
- Frameless (kenarsız) modern görünüm
- Ribbon header ile tutarlı başlık
- Otomatik resize ve drag desteği
- Merkezi palet renkleri
- Standart buton stili

**Örnek:**
```python
from .common.modern_dialog import ModernBaseDialog

class MyDialog(ModernBaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, min_width=500, min_height=400)
        self._setup_ui()
```

---

### ⚠️ QDialog (Sınırlı Kullanım)
**Sadece şu durumlarda:**
- Sistem-native dialoglar gerekliğinde (file dialog, color picker)
- Basit quick message box'lar için
- Üçüncü parti kütüphane uyumluluğu gerektiğinde

**Özellikler:**
- Native window decorations
- Platform-specific davranış
- Sınırlı özelleştirme

**Örnek:**
```python
# Sadece sistem dialogları için
QFileDialog.getOpenFileName(self, "Dosya Seç")
QColorDialog.getColor()
```

---

## 🎨 Stil Standardizasyonu

### Renk Kullanımı
**Tüm renkler `palette.py` üzerinden:**
```python
from ..styles import get_color

# Doğru ✅
button.setStyleSheet(f"background-color: {get_color('primary')};")

# Yanlış ❌
button.setStyleSheet("background-color: #4F46E5;")
```

### Buton Stilleri
**Standart butonlar için `style_button()` helper:**
```python
from ..styles import style_button

# Doğru ✅
save_btn = QPushButton("Kaydet")
save_btn.setStyleSheet(style_button(save_btn, "primary"))

# Özel stiller için palette renkleri kullan
cancel_btn.setStyleSheet(f"""
    QPushButton {{
        background-color: {get_color('bg_panel')};
        border: 1px solid {get_color('border')};
        color: {get_color('text_secondary')};
    }}
""")
```

---

## 📐 Boyut ve Layout

### Minimum Boyutlar
- **Simple dialog**: 400x300
- **Complex dialog**: 600x500  
- **Wizard**: 800x600
- **Full-featured**: 1000x700

### Layout Standartları
```python
def _setup_ui(self):
    self._setup_base_ui()
    
    # Header (ribbon style)
    header = self.build_ribbon_header("🎯", "Dialog Başlığı")
    self.layout.addWidget(header)
    
    # Content area
    content = QWidget()
    # ... content setup
    self.layout.addWidget(content, 1)  # Stretch
    
    # Footer (buttons)
    footer = QHBoxLayout()
    footer.addStretch()
    # ... buttons
    self.layout.addLayout(footer)
```

---

## 🔧 İstisnalar ve Özel Durumlar

### Wizard Dialogları
- `SurveyImportWizard` → QWizard (mevcut yapısı korunsun)
- `SetupWizard` → ModernBaseDialog'e dönüştürülebilir

### Mesaj Box'ları
- **Info/Warning/Error**: `ModernMessageBox`
- **Confirmation**: `ModernConfirmationDialog`
- **Scrollable Info**: `ScrollableMessageBox`

### Floating Windows
- **Panel detaching**: `FramelessPanelWindow` (mevcut yapısı korunsun)
- **Dialog detaching**: ModernBaseDialog kullanılabilir

---

## 📝 Kontrol Listesi

Yeni dialog oluştururken:
- [ ] `ModernBaseDialog` miras alınıyor mu?
- [ ] Tüm renkler `get_color()` kullanıyor mu?
- [ ] Minimum boyut belirlendi mi?
- [ ] Ribbon header var mı?
- [ ] Butonlar standart stilde mi?
- [ ] Responsive tasarım yapıldı mı?
- [ ] Erişilebilirlik (keyboard navigation) destekleniyor mu?

---

## 🚀 Geçiş Stratejisi

### Mevcut QDialog'ları Dönüştürme
1. **Öncelik**: En çok kullanılan dialoglar
2. **Sıra**: Ayarlar → Analiz → İçe/dışa aktarım
3. **Test**: Her dönüşüm sonrası UI testi

### Korumalı Alanlar
- File/Color dialogları (sistem native kalmalı)
- Üçüncü parti kütüphane dialogları
- Kritik sistem dialogları
