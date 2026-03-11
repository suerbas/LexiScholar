"""
Visualization actions for LexiScholar.
"""

from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt
from ..common_ui import show_info, show_warning, show_error, ask_confirmation

class VisualsActionsMixin:
    """Methods for generating and viewing visualizations."""

    def _open_visualization(self, title, file_path, subtitle=None, sentiment_results=None, topic_results=None, ner_results=None, model_type="BERT"):
        """Open visualization in a central tab."""
        from ..common.browser_dialog import BrowserWidget
        
        # Check if tab already exists
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == title:
                self.central_tabs.setCurrentIndex(i)
                return None # Already exists
                
        widget = BrowserWidget(title, file_path, self)
        
        # Store sentiment results if provided (for export functionality)
        if sentiment_results is not None:
            widget._sentiment_results = sentiment_results
            widget._sentiment_model = model_type
        
        # Store topic results if provided (for export functionality)
        if topic_results is not None:
            widget._topic_results = topic_results
            widget._topic_model = model_type

        if ner_results is not None:
            widget._ner_results = ner_results
            widget._ner_model = model_type
        
        # Determine contextual help
        t = title.lower()
        help_page = "analysis_tools.html"
        help_tooltip = "Görselleştirme hakkında yardım"
        help_anchor = None
        
        # Specifically for Keyword Analysis, hide its toolbar
        # if "Anahtar Kelime Analizi" in title:
        #    widget.set_toolbar_visible(False)
        
        if "hibrit" in t and ("konu" in t or "topic" in t):
            widget.add_simple_controls()
            help_page = "analysis_tools.html"
            help_anchor = "ai-topic-modeling"
            help_tooltip = "Hibrit Konu Modelleme: Lokal LDA ile online AI modelinin belge başına baskın konu atamalarını, konu etiketlerini ve anahtar kelimelerini karşılaştırır. Uyumlu, yakın ve farklı sonuçları birlikte yorumlamanızı sağlar."
        elif "hibrit" in t and ("duygu" in t or "sentiment" in t):
            widget.add_simple_controls()
            help_page = "analysis_tools.html"
            help_anchor = "ai-sentiment"
            help_tooltip = "Hibrit Duygu Analizi: Lokal BERT ile online AI modelinin aynı belge için ürettiği duygu etiketlerini ve kısa gerekçelerini karşılaştırır; farklılıklar nüans, bağlam ve ironi yorumlarını görmenizi sağlar."
            widget._is_sentiment_analysis = True
        elif any(x in t for x in ["kelime", "bulut", "cloud"]) and "anahtar" not in t:
            widget.add_word_cloud_controls()
            help_anchor = "word-cloud" if "kelime" in t else "code-cloud"
            help_tooltip = "Kelime Bulutu: Metindeki sık tekrarlanan kavramları vurgulayarak ön plana çıkarır. Boyut kontrolleriyle özelleştirilebilir."
        elif "anahtar" in t and "kelime" in t:
            # Anahtar Kelime Analizi (YAKE)
            # Controls will be added by the caller (nlp_actions.py) because they need callbacks
            help_anchor = "keyword-analysis"
            help_tooltip = "Anahtar Kelime Analizi: Metindeki en önemli kavramları istatistiksel algoritmalarla (YAKE) belirler. Sadece sıklığa değil, bağlam ve konuma da bakar."
        elif any(x in t for x in ["frekans", "frequency"]):
            widget.add_simple_controls()
            help_anchor = "word-frequency"
            help_tooltip = "Kelime Frekansı: Metinde geçen terimleri sayar ve sıklığa dayalı bir liste sunarak anahtar kelimeleri gösterir."
        elif any(x in t for x in ["çapraz", "crosstab"]):
            widget.add_crosstab_controls()
            help_anchor = "crosstab"
            help_tooltip = "Çapraz Tablo: Atanmış nitel kodlar ile kategorik değişkenler (örn. yaş, meslek) arasındaki frekansları iki boyutlu matris olarak özetler."
        elif any(x in t for x in ["kod matris", "matris", "matrix"]):
            widget.add_code_matrix_controls()
            help_anchor = "code-matrix"
            help_tooltip = "Kod Matrisi: Çalışma boyutundaki nitel kodların hangi belge ya da alt gruplarda ne yoğunlukta bulunduğunu çapraz dağılımla gösterir."
        elif any(x in t for x in ["zaman", "timeline", "dağılım"]):
            widget.add_simple_controls()
            help_anchor = "timeline"
            help_tooltip = "Zaman Çizelgesi: Olay ve alıntıların sıralamasını, kodlanmış etiketler kılavuzluğuyla zamansal ya da metin-içi doğrusal şekilde canlandırır."
        elif any(x in t for x in ["kapsam", "ısı", "heatmap"]):
            widget.add_simple_controls()
            help_anchor = "coverage-heatmap"
            help_tooltip = "Kapsam Haritası: Kodlamaların belge veya klasör tabanında nerede kümelendiğini renk doygunluğu prensibiyle izah eder."
        elif "sankey" in t:
            widget.add_simple_controls()
            help_page = "visualizations.html"
            help_anchor = "sankey"
            help_tooltip = "Sankey Diyagramı: Temalar ya da kodlar arası ilişki yönünü ve ortak frekansları akış çizgilerinin kalınlıklarıyla ifade eder."
        elif any(x in t for x in ["ilişki", "ilişk", "network", "graph", "grafiğ"]):
            widget.add_simple_controls()
            help_page = "visualizations.html"
            help_anchor = "network"
            help_tooltip = "Kod İlişki Grafiği: Kodların birbiriyle olan bağlantılarını ve birlikte kullanılma (co-occurrence) yoğunluklarını interaktif bir ağ haritası üzerinde analiz edin."
        elif "portre" in t or "resmi" in t or "portrait" in t:
            widget.add_simple_controls()
            help_page = "visualizations.html"
            help_anchor = "portrait"
            help_tooltip = "Belge Portresi: Belge yapısını ve kodlama yoğunluklarını bir desen (Portrait) olarak görselleştirerek genel bir bakış sağlar."
        elif "duygu" in t or "sentiment" in t:
            # Sentiment analysis - add export controls
            widget.add_simple_controls()
            help_page = "visualizations.html"
            help_anchor = "sentiment-analysis"
            help_tooltip = "Duygu Analizi: Metinlerin duygusal tonunu (pozitif, negatif, nötr) yapay zeka ile analiz eder."
            
            # Add sentiment export controls to the widget's header
            # This will be called by nlp_actions.py after the tab is created
            widget._is_sentiment_analysis = True
        elif any(x in t for x in ["varlık", "ner", "entity"]):
            widget.add_simple_controls()
            help_page = "analysis_tools.html"
            help_anchor = "ai-ner"
            help_tooltip = "Varlık Tanıma (NER): Metindeki kişi, kurum, yer ve tarih gibi özel adları otomatik olarak tespit eder. Kategoriler bölümünde bulunan varlık türleri, tablo bölümünde ise belge bazlı dağılım gösterilir."
        elif "anlamsal harita" in t or "semantic map" in t:
            widget.add_simple_controls()
            help_page = "analysis_tools.html"
            help_anchor = "semantic-mapping"
            help_tooltip = "Anlamsal Haritalama: Seçilen sınıf/kod ya da tüm proje verisi içindeki örtüşen anlamları yapay zeka (BGE-M3) yardımıyla çok boyutlu bir uzay üzerinden analiz eder ve kümelemeleri gösterir."
        else:
            widget.add_simple_controls()
            help_page = "visualizations.html"
            help_tooltip = "LexiScholar Görsel Analiz Rehberi: Bilgi ansiklopedisindeki ilgili konuyu inceleyin."

        self.add_analysis_tab(widget, title, help_tooltip=help_tooltip, help_page=help_page, help_anchor=help_anchor, subtitle=subtitle)
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage(f"📈 {title} hazır.")
        return widget

    def _show_semantic_map(self):
        """Show interactive Semantic Cluster Map using BGE-M3 embeddings."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            from nlp.tasks.semantic import build_cluster_map_data
            from ..visualizations import generate_semantic_map_html
            
            # Fetch segments
            active_doc_ids = self.doc_dao.get_active_ids()
            if active_doc_ids:
                bulk_segments = self.segment_dao.get_by_documents_bulk(active_doc_ids)
                # Flatten the dictionary {doc_id: [segments]} into a flat list
                segments = []
                for doc_segs in bulk_segments.values():
                    segments.extend(doc_segs)
            else:
                segments = self.segment_dao.get_all()
            
            if len(segments) < 3:
                show_info(self, "Yetersiz Veri", "Anlamsal haritalama için en az 3 kodlanmış bölüme ihtiyacınız var.")
                return
            
            # User warning for resources
            msg = (
                "Anlamsal haritalama işlemi derin öğrenme modelleri (BGE-M3) kullanır.\n\n"
                "• Yaklaşık 2-4 GB RAM kullanımı gerektirebilir.\n"
                "• Bilgisayarınızın gücüne göre işlem birkaç dakika sürebilir (Örn: 2000 segment için ~1 dk).\n"
                "• GPU destekleniyorsa otomatik kullanılacaktır.\n\n"
                "Analizi başlatmak istiyor musunuz?"
            )
            if not ask_confirmation(self, "Analiz Onayı", msg):
                return
            
            from ..common.modern_progress_dialog import ModernProgressDialog
            from ..worker_threads import SemanticWorker
            from ..visualizations import generate_semantic_map_html

            # Create and show progress dialog
            progress = ModernProgressDialog(self, "Anlamsal Haritalama", "Anlamsal analiz başlatılıyor...", "İptal")
            
            # Start worker thread
            self._sem_worker = SemanticWorker(segments)
            
            def handle_finished(cluster_data):
                progress.close()
                try:
                    file_path = generate_semantic_map_html(cluster_data)
                    self._open_visualization("Anlamsal Haritalama", file_path)
                except Exception as e:
                    show_error(self, "Görselleştirme Hatası", f"Harita dosyası oluşturulamadı: {e}")

            def handle_error(error_msg):
                progress.close()
                if "Kütüphane_Eksik" in error_msg:
                    show_error(self, "Gerekli Kütüphaneler Eksik", "Anlamsal haritalama için gerekli kütüphaneler eksik:\n\npip install umap-learn hdbscan sentence-transformers")
                elif "Model_Missing" in error_msg:
                    show_info(self, "Dil Modeli Gerekli", "Bu özellik BAAI/bge-m3 dil modelini gerektirir.\n\nLütfen üst menüden 'Dil Modellerini Kontrol Et' seçeneği ile modeli indirin.")
                else:
                    show_error(self, "Harita Hatası", f"Anlamsal haritalama oluşturulamadı:\n{error_msg}")

            def handle_progress(val, msg):
                progress.setLabelText(msg)

            # Connect signals
            self._sem_worker.finished.connect(handle_finished)
            self._sem_worker.error.connect(handle_error)
            self._sem_worker.progress.connect(handle_progress)
            
            # Handle cancellation
            progress.canceled.connect(self._sem_worker.terminate)
            
            self._sem_worker.start()
            progress.show()

        finally:
            QApplication.restoreOverrideCursor()

    def _show_code_graph(self):
        """Show interactive code relationship graph."""
        from analysis import AnalysisTools
        from ..visualizations import generate_cooccurrence_graph
        analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao)
        active_code_ids = self.code_dao.get_active_ids()
        codes, matrix = analysis.get_cooccurrence_matrix(code_ids=active_code_ids if active_code_ids else None)
        if not codes: return
        code_data = [{'id': c['id'], 'name': c['name'], 'color': c['color']} for c in codes]
        file_path = generate_cooccurrence_graph(code_data, matrix)
        dialog = self._open_visualization("Kod İlişki Grafiği", file_path)
        if dialog:
            edge_count = sum(1 for i in range(len(matrix)) for j in range(i + 1, len(matrix[i])) if matrix[i][j] > 0)
            dialog.add_graph_controls(node_count=len(codes), edge_count=edge_count)

    def _show_word_cloud(self):
        """Show word cloud visualization."""
        from analysis import AnalysisTools
        from ..visualizations import generate_word_cloud_html
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao)
            active_doc_ids = self.doc_dao.get_active_ids()
            if active_doc_ids:
                from collections import Counter
                total_freq = Counter()
                for doc_id in active_doc_ids:
                    freq = analysis.get_word_frequency(doc_id=doc_id, min_length=3, top_n=200)
                    if freq: total_freq.update(dict(freq))
                word_freq = total_freq.most_common(150)
            else:
                word_freq = analysis.get_word_frequency(doc_id=None, min_length=3, top_n=150)
            if not word_freq: return
            file_path = generate_word_cloud_html(word_freq)
            dialog = self._open_visualization("Kelime Bulutu", file_path)
            if dialog:
                dialog.add_word_cloud_controls()
        finally: QApplication.restoreOverrideCursor()

    def _show_code_cloud(self):
        """Show code cloud visualization."""
        from ..visualizations import generate_word_cloud_html
        active_only = bool(self.code_dao.get_active_ids())
        freqs = self.code_dao.get_code_frequencies(active_only=active_only)
        if not freqs: return
        file_path = generate_word_cloud_html(freqs)
        dialog = self._open_visualization("Kod Bulutu", file_path)
        if dialog:
            dialog.add_word_cloud_controls()

    def _show_code_matrix(self):
        """Show interactive code matrix visualization."""
        from analysis import AnalysisTools
        from ..visualizations import generate_code_matrix_html
        analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao)
        active_doc_ids = self.doc_dao.get_active_ids()
        active_code_ids = self.code_dao.get_active_ids()
        codes, docs, matrix = analysis.get_code_matrix()
        # Filter logic...
        if active_code_ids:
            new_codes, new_matrix = [], []
            for i, c in enumerate(codes):
                if c['id'] in active_code_ids:
                    new_codes.append(c); new_matrix.append(matrix[i])
            codes, matrix = new_codes, new_matrix
        if active_doc_ids:
            new_docs, kept_indices = [], []
            for i, d in enumerate(docs):
                if d['id'] in active_doc_ids:
                    new_docs.append(d); kept_indices.append(i)
            matrix = [[row[i] for i in kept_indices] for row in matrix]
            docs = new_docs
        if not codes or not docs: return
        file_path = generate_code_matrix_html(codes, docs, matrix)
        dialog = self._open_visualization("Kod Matris Tarayıcısı", file_path)
        if dialog:
            dialog.add_code_matrix_controls()

    def _show_sankey_diagram(self):
        """Show Sankey Diagram."""
        from analysis import AnalysisTools
        from ..visualizations import generate_sankey_html
        try:
            analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao)
            codes, matrix = analysis.get_cooccurrence_matrix()
            labels = [c['name'] for c in codes]
            src, tgt, val = [], [], []
            n = len(codes)
            for i in range(n):
                for j in range(i+1, n):
                    if matrix[i][j] > 0: src.append(i); tgt.append(j); val.append(matrix[i][j])
            if not src: return
            file_path = generate_sankey_html({'labels': labels, 'source': src, 'target': tgt, 'value': val})
            
            # Use specific title to trigger analysis mode in main_window
            title = "Kod İlişkileri (Sankey Diyagramı)"
            
            # Open the tab
            widget = self._open_visualization(title, file_path, subtitle="Kodlar arası ilişki akışı")
            
            if widget:
                # 1. Hide default toolbar (since we move controls to header)
                widget.set_toolbar_visible(False)
                # Note: 'Kaydet' button is automatically handled by BrowserWidget.setup_header_controls
                        
        except Exception as e:
            # Show error if something fails
            from PyQt6.QtWidgets import QMessageBox
            show_error(self, "Hata", f"Sankey diyagramı oluşturulamadı:\n{str(e)}")
