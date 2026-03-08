"""
Advanced Visualization Actions Mixin for LexiScholar Main Window.
Code coverage heatmap, code timeline, and Sankey diagram.
"""

from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt
from core.utils import natural_sort_key
from . import common_ui
from .common_ui import show_info, show_warning, show_error, ask_confirmation


class VisualizationActions:
    """Mixin class providing advanced visualization methods for MainWindow."""

    def _show_visualization_gallery(self):
        """Open the unified visualization dashboard as a central tab."""
        # Check if tab already exists
        title = "Görselleştirme Galerisi"
        for i in range(self.central_tabs.count()):
            if self.central_tabs.tabText(i) == title:
                self.central_tabs.setCurrentIndex(i)
                return
        
        from .visualizations.visualization_gallery_dialog import VisualizationGalleryWidget
        widget = VisualizationGalleryWidget(db_path=self.db_path)
        
        help_tooltip = "Görselleştirme Galerisi: Verilerinizi (Kodlar, Değişkenler) sütun, pasta veya halka grafiklerle analiz edin ve makale kalitesinde (300 DPI) dışa aktarın."
        self.add_analysis_tab(widget, title, help_tooltip=help_tooltip, help_page="visualizations.html", help_anchor="charts")
        
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage("📊 Görselleştirme galerisi açıldı.")

    def _show_code_coverage(self):
        """Show Code Coverage Heatmap (Docs vs Codes)."""
        active_docs = [d for d in self.doc_dao.get_all() if d.get('is_active', True)]
        # Filter codes? For now all codes or active codes
        active_codes = self.code_dao.get_all()
        # Optional: Filter active codes
        active_code_ids = self.code_dao.get_active_ids()
        if active_code_ids:
            active_codes = [c for c in active_codes if c['id'] in active_code_ids]
            
        if not active_docs or not active_codes:
            show_warning(self, "Uyarı", "Görüntülenecek belge veya kod yok.")
            return

        # Prepare heatmap data Z-matrix
        # X = Doc titles, Y = Code names
        doc_ids = [d['id'] for d in active_docs]
        code_ids = [c['id'] for c in active_codes]
        
        doc_titles = [d.get('title', f"Doc {d['id']}") for d in active_docs]
        code_names = [c['name'] for c in active_codes]
        
        z_values = []
        for c_id in code_ids:
            row = []
            for d_id in doc_ids:
                # Calculate coverage % for code c in doc d
                # Get segments
                segments = self.segment_dao.get_by_document(d_id)
                # Filter by code
                code_segs = [s for s in segments if s['code_id'] == c_id]
                
                if not code_segs:
                    row.append(0)
                    continue
                    
                # Total length covered
                total_len = sum(s['end_pos'] - s['start_pos'] for s in code_segs)
                
                # Doc length (stripping HTML for accurate representation)
                doc = next(d for d in active_docs if d['id'] == d_id)
                content = doc.get('extracted_text') or doc.get('content') or ""
                if content:
                    import re
                    content = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', content, flags=re.DOTALL)
                    content = re.sub(r'<[^>]+>', ' ', content)
                    content = re.sub(r'&[a-z]+;', ' ', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                
                doc_len = len(content) if content else 1
                
                coverage = (total_len / doc_len) * 100 if doc_len > 0 else 0
                row.append(coverage)
            z_values.append(row)
            
        data = {
            'documents': doc_titles,
            'codes': code_names,
            'z_values': z_values
        }
        
        self._open_code_coverage(data)

    def _open_code_coverage(self, data):
        """Helper to open code coverage visualization in standalone window."""
        from .visualizations import generate_coverage_heatmap_html
        file_path = generate_coverage_heatmap_html(data)
        
        title = "Kod Kapsam Haritası"
        subtitle = f"{len(data['documents'])} belge • {len(data['codes'])} kod"
        
        widget = self._open_visualization(title, file_path, subtitle=subtitle)
        
        if widget:
            # 1. Show default toolbar
            widget.set_toolbar_visible(True)
            widget.add_simple_controls()

    def _show_code_timeline(self):
        """Show Code Timeline for the active document or prompt selection."""
        from .modern_dialogs import ModernComboboxDialog
        
        # Target: Active documents
        active_docs = [d for d in self.doc_dao.get_all() if d.get('is_active', True)]
        
        # Sort documents by title naturally
        active_docs.sort(key=lambda x: natural_sort_key(x.get('title', '')))

        if not active_docs:
            show_warning(self, "Uyarı", "Aktif belge bulunamadı.")
            return
            
        target_doc = None
        
        # If multiple documents are active, ask user to select one
        if len(active_docs) > 1:
            items = [d.get('title', f"Belge {d['id']}") for d in active_docs]
            item, ok = ModernComboboxDialog.get_item(
                self, 
                "Belge Seçimi", 
                "Zaman çizelgesi oluşturulacak belgeyi seçin:", 
                items
            )
            if ok and item:
                # Find the selected document object
                for d in active_docs:
                    if d.get('title', f"Belge {d['id']}") == item:
                        target_doc = d
                        break
            else:
                return # User cancelled
        else:
            # Only one document active, use it directly
            target_doc = active_docs[0]
            
        if not target_doc: return

        segments = self.segment_dao.get_by_document(target_doc['id'])
        
        if not segments:
            show_info(self, "Bilgi", "Belgede kodlanmış bölüm yok.")
            return
            
        # Prepare data for Gantt
        timeline_data = []
        for s in segments:
            # Need code name and color
            code = self.code_dao.get_by_id(s['code_id'])
            if not code: continue
            
            timeline_data.append({
                'Code': code['name'],
                'Start': s['start_pos'],
                'End': s['end_pos'],
                'Color': code['color'],
                'Text': s.get('text', '')
            })
            
        self._open_code_timeline(timeline_data, target_doc.get('title', 'Belge'))

    def _open_code_timeline(self, data, doc_title):
        """Helper to open timeline visualization in standalone window."""
        from .visualizations import generate_code_timeline_html
        
        file_path = generate_code_timeline_html(data, doc_title)
        
        # Title must match the one in main_window check
        title = "Kod Zaman Çizelgesi"
        subtitle = f"{doc_title} • {len(data)} kod segmenti"
        
        widget = self._open_visualization(title, file_path, subtitle=subtitle)
        
        if widget:
            # 1. Show default toolbar
            widget.set_toolbar_visible(True)
            widget.add_simple_controls()

    def _show_sankey_diagram(self):
        """Show Sankey diagram for code co-occurrences."""
        # Use existing logic to get matrix
        from analysis import AnalysisTools
        analysis = AnalysisTools(self.doc_dao, self.code_dao, self.segment_dao)
        
        # Get matrix (Codes x Codes)
        codes, matrix = analysis.get_cooccurrence_matrix()
        
        # Filter active
        active_ids = self.code_dao.get_active_ids()
        if active_ids:
             # Filter logic similar to code graph
             indices = [i for i, c in enumerate(codes) if c['id'] in active_ids]
             codes = [codes[i] for i in indices]
             # Filter matrix rows/cols
             matrix = [[matrix[r][c] for c in indices] for r in indices]
             
        if not codes:
            show_info(self, "Bilgi", "Görüntülenecek veri yok.")
            return

        # Prepare Sankey links
        # Source -> Target with Value
        source_indices = []
        target_indices = []
        values = []
        
        # Matrix is symmetric, use upper triangle
        for i in range(len(codes)):
            for j in range(i + 1, len(codes)):
                val = matrix[i][j]
                if val > 0:
                    source_indices.append(i)
                    target_indices.append(j)
                    values.append(val)
                    
        data = {
            'labels': [c['name'] for c in codes],
            'source': source_indices,
            'target': target_indices,
            'value': values
        }
        
        self._open_sankey(data)

    def _open_sankey(self, data):
        """Helper to open sankey visualization in standalone window."""
        from .visualizations import generate_sankey_html
        file_path = generate_sankey_html(data)
        self._open_visualization("Kod İlişkileri (Sankey)", file_path)

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
            
            # Title for main_window check
            title = "Kelime Bulutu"
            from datetime import datetime
            subtitle = f"{len(word_freq)} kelime • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            widget = self._open_visualization(title, file_path, subtitle=subtitle)
            
            if widget:
                # Add word cloud controls (This adds the toolbar below the blue header)
                widget.add_word_cloud_controls()
                
                # We don't hide the toolbar here because word cloud controls are complex 
                # and sit better in their own bar, similar to Keyword Analysis.
                # But we need to remove the duplicate 'Save' and 'Detach' from that toolbar 
                # if we are moving them to the blue header.
                
                # Actually, user said: "Düzenleme barı mavi barın altında olacak."
                # So we keep the toolbar visible.
                
                # However, user also said: "ayrılınca minimize, tam ekran ve kapatma butonları çıkacak."
                # which is handled by PanelHeader/MainWindow logic we just enabled.
                
                # Let's clean up the toolbar to remove redundant "Kaydet" and "Detach" 
                # if we decide to put "Kaydet" in the blue header too.
                # For now, let's keep "Kaydet" in the toolbar as requested "Anahtar kelime analizindeki arayüz gibi"
                # In Keyword Analysis, we have a toolbar below blue header.
                
                pass

        except Exception as e:
            common_ui.show_error(self, "Hata", f"Kelime bulutu oluşturulamadı:\n{str(e)}")
        finally: 
            QApplication.restoreOverrideCursor()
