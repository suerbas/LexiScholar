/**
 * LexiScholar Encyclopedia Global Search Logic
 */

const searchIndex = [
    { title: "Veri Yönetimi", desc: "Corpus yönetimi, anket dönüşümü ve veri stratejisi.", url: "data_management.html", keywords: "import excel anket klasör tree corpus denetim izi audit trail" },
    { title: "Veri Editörü", desc: "Değişkenleri ve katılımcı matrisini tablo üzerinden düzenleyin.", url: "data_management.html#variable-editor", keywords: "spreadsheet tablo değişken editör matris purposive sampling" },
    { title: "Kodlama Rehberi", desc: "Taksonomi oluşturma, Aksiyel ve In-Vivo kodlama mantığı.", url: "coding_guide.html", keywords: "tag hiyerarşi invivo renklendirme taksonomi aksiyel axial memo" },
    { title: "Analiz Araçları", desc: "Timeline, Görsel Kod Dağılımı ve metodolojik derinleşme.", url: "analysis_tools.html", keywords: "zaman çizelgesi ısı haritası grafik hiyerarşi timeline heatmap coverage" },
    { title: "Karma Yöntemler", desc: "Triangülasyon ve nitel-nicel veri entegrasyonu.", url: "mixed_methods.html", keywords: "crosstab çapraz tablo matris karışık triangulation triangülasyon çeşitleme entegrasyon" },
    { title: "Yapay Zeka (AI)", desc: "Akademik Persona ve Kıdemli Hakem Sistemi.", url: "ai_features.html", keywords: "gemini deepseek claude openrouter bot asistan rag sentez sentezleme referee hakem model bakım boyut size mb gb indir download" },
    { title: "OpenRouter Rehberi", desc: "API entegrasyonu ve model çeşitliliği yönetimi.", url: "openrouter_guide.html", keywords: "key anahtar bakiye kredi api entegrasyon model diversity" },
    { title: "Görselleştirme", desc: "Semantik haritalama, akış diyagramları ve semanti yakınlık.", url: "visualizations.html", keywords: "chart grafik portrait sankey ağ semantik harita haritalama co-occurrence" },
    { title: "Belge Portresi", desc: "Belgenin kod yoğunluğunu lineer akış üzerinde analiz edin.", url: "visualizations.html#portrait", keywords: "portrait desen motif piksel syntagmatic" },
    { title: "Sankey Diyagramı", desc: "Kavramsal akış ve nedensellik ilişkilerini inceleyin.", url: "visualizations.html#sankey", keywords: "akış sankey geçiş transfer causality nedensellik" },
    { title: "Kod İlişki Grafiği", desc: "Semantik yakınlık ve çekirdek kategori analizi.", url: "visualizations.html#network", keywords: "graph network ağ ilişkisel co-occurrence semantic semantik centrality" },
    { title: "Takım Çalışması", desc: "Akademik işbirliği, güvenilirlik ve etik standartlar.", url: "teamwork_reliability.html", keywords: "teamwork ekip grup takımı işbirliği senkronize güvenilirlik dependability reflexivity" },
    { title: "Analist Uyumu (IRR)", desc: "Cohen's Kappa analizi ve uzlaşma paneli.", url: "teamwork_reliability.html#irr-analysis", keywords: "kappa irr uyum tutarlılık güvenilirlik cohen consensus uzlaşma" },
    { title: "Kodlayıcı Yönetimi", desc: "Analiz izlenebilirliği (traceability) ve araştırmacı rolleri.", url: "teamwork_reliability.html#coder-management", keywords: "coder kodlayıcı araştırmacı user kullanıcı traceability izlenebilirlik" },
    { title: "Kısayollar", desc: "Analitik akış (flow) için klavye verimliliği.", url: "keyboard_shortcuts.html", keywords: "klavye tuş shortcut flow verimlilik" }
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
