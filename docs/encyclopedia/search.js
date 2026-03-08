/**
 * LexiScholar Encyclopedia Global Search Logic
 */

const searchIndex = [
    { title: "Veri Yönetimi", desc: "Belge ağacı, içe aktarma ve dosya yönetimi.", url: "data_management.html", keywords: "import excel anket klasör tree" },
    { title: "Veri Editörü", desc: "Değişkenleri Excel gibi tablo üzerinden düzenleyin.", url: "data_management.html#variable-editor", keywords: "spreadsheet tablo değişken editör matris" },
    { title: "Anket İçe Aktarma", desc: "Excel dosyalarını 3 adımda projeye dahil edin.", url: "data_management.html#survey-import", keywords: "wizard sihirbaz excel anket" },
    { title: "Kodlama Rehberi", desc: "İn-Vivo kodlama ve hiyerarşik kod ağacı mantığı.", url: "coding_guide.html", keywords: "tag hiyerarşi invivo renklendirme" },
    { title: "Analiz Araçları", desc: "Timeline, Heatmap ve Sankey diyagramları.", url: "analysis_tools.html", keywords: "zaman çizelgesi ısı haritası grafik hiyerarşi" },
    { title: "Karma Yöntemler", desc: "Nitel ve nicel veriyi birleştiren analizler.", url: "mixed_methods.html", keywords: "crosstab çapraz tablo matris karışık" },
    { title: "Yapay Zeka (AI)", desc: "OpenRouter entegrasyonu ve AI asistanı.", url: "ai_features.html", keywords: "gemini deepseek claude openrouter bot asistan" },
    { title: "OpenRouter Rehberi", desc: "API anahtarı alma ve para yükleme kılavuzu.", url: "openrouter_guide.html", keywords: "key anahtar bakiye kredi nasıl alınır" },
    { title: "Görselleştirme", desc: "Diyagramlar, portreler ve ağ grafikleri.", url: "visualizations.html", keywords: "chart grafik portrait sankey ağ" },
    { title: "Belge Portresi", desc: "Belgenin kod yoğunluğunu bir desen olarak görün.", url: "visualizations.html#portrait", keywords: "portrait desen motif piksel" },
    { title: "Sankey Diyagramı", desc: "Kodlar arası akış ve geçişleri inceleyin.", url: "visualizations.html#sankey", keywords: "akış sankey geçiş transfer" },
    { title: "Kod İlişki Grafiği", desc: "Kodların birbirine yakınlığını ağ haritasında görün.", url: "visualizations.html#network", keywords: "graph network ağ ilişkisel co-occurrence" },
    { title: "Takım Çalışması", desc: "Grup çalışması, kodlayıcı yönetimi ve güvenilirlik.", url: "teamwork_reliability.html", keywords: "teamwork ekip grup takımı işbirliği senkronize" },
    { title: "Analist Uyumu (IRR)", desc: "Kodlayıcılar arası tutarlılık ve Kappa analizi.", url: "teamwork_reliability.html#irr-analysis", keywords: "kappa irr uyum tutarlılık güvenilirlik" },
    { title: "Kodlayıcı Yönetimi", desc: "Projeye yeni araştırmacılar ekleyin ve yönetin.", url: "teamwork_reliability.html#coder-management", keywords: "coder kodlayıcı araştırmacı user kullanıcı" },
    { title: "Kısayollar", desc: "Hızlı kodlama ve navigasyon kısayolları.", url: "keyboard_shortcuts.html", keywords: "klavye tuş shortcut" },
    { title: "Dışa Aktarma", desc: "Word ve Excel raporları oluşturma.", url: "data_management.html#export", keywords: "xlsx docx rapor çıktı" },
    { title: "Memos (Notlar)", desc: "Analitik ve teorik notların yönetimi.", url: "data_management.html#memos", keywords: "not memo günlük günlükler" }
];

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('.search-input');
    const searchContainer = document.querySelector('.search-container');

    if (!searchInput || !searchContainer) return;

    // Create results container
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'search-results';
    searchContainer.appendChild(resultsContainer);

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();

        if (query.length < 2) {
            resultsContainer.classList.remove('active');
            return;
        }

        const filtered = searchIndex.filter(item => {
            return item.title.toLowerCase().includes(query) ||
                item.desc.toLowerCase().includes(query) ||
                item.keywords.toLowerCase().includes(query);
        });

        renderResults(filtered);
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (!searchContainer.contains(e.target)) {
            resultsContainer.classList.remove('active');
        }
    });

    function renderResults(results) {
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="search-no-results">Sonuç bulunamadı.</div>';
        } else {
            results.forEach(item => {
                const div = document.createElement('a');
                div.href = item.url;
                div.className = 'search-result-item';
                div.innerHTML = `
                    <span class="search-result-title">${item.title}</span>
                    <span class="search-result-desc">${item.desc}</span>
                `;
                resultsContainer.appendChild(div);
            });
        }

        resultsContainer.classList.add('active');
    }
});
