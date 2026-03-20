"""
Worker Threads for LexiScholar
Moves heavy NLP, analysis and IO tasks to background threads to keep UI responsive.

Sınıflar:
    NLPWorker    — Duygu analizi, NER, anahtar kelime, konu modellemesi
    GenericWorker — Herhangi bir callable'ı arka planda çalıştırır (proje kaydetme vb.)
"""

from __future__ import annotations
from typing import Any, Callable
from PyQt6.QtCore import QThread, pyqtSignal
import logging
from .common_ui import show_info, show_warning, show_error, ask_confirmation

logger = logging.getLogger(__name__)


class NLPWorker(QThread):
    """Generic worker for running NLP tasks in the background."""
    
    # Signals
    progress = pyqtSignal(int, str)  # current_index, status_message
    finished = pyqtSignal(list)      # results
    error = pyqtSignal(str)         # error message
    
    def __init__(self, task_type: str, texts: list, options: dict = None):
        super().__init__()
        self.task_type = task_type # 'sentiment', 'ner', 'keywords', etc.
        self.texts = texts
        self.options = options or {}
        self._is_canceled = False

    def cancel(self):
        """Request cancellation of the task."""
        self._is_canceled = True

    def run(self):
        """Execute the requested NLP task."""
        try:
            if self.task_type == 'sentiment':
                self._run_sentiment()
            elif self.task_type == 'ner':
                self._run_ner()
            elif self.task_type == 'keywords':
                self._run_keywords()
            elif self.task_type == 'topic_modeling':
                self._run_topic_modeling()
            elif self.task_type == 'kwic':
                self._run_kwic()
            elif self.task_type == 'document_portrait':
                self._run_document_portrait()
            # Add more task types as needed
        except Exception as e:
            logger.error(f"NLP Worker Error ({self.task_type}): {e}")
            self.error.emit(str(e))

    def _run_topic_modeling(self):
        from nlp_engine import extract_topics, extract_topics_online, extract_topics_hybrid
        
        n_topics = self.options.get('n_topics', 5)
        mode = self.options.get('mode', 'local')  # 'local', 'online', 'hybrid'
        model = self.options.get('model', None)
        
        if mode == 'local':
            self.progress.emit(0, "Konular modelleniyor (LDA - bu işlem biraz zaman alabilir)...")
            topic_data = extract_topics(self.texts, n_topics=n_topics)
        elif mode == 'online':
            self.progress.emit(0, f"Konular online AI ile analiz ediliyor ({model or 'varsayılan'})...")
            topic_data = extract_topics_online(self.texts, n_topics=n_topics, model=model)
        else:  # hybrid
            self.progress.emit(0, "Hibrit konu modelleme başlatılıyor (LDA + Online AI)...")
            topic_data = extract_topics_hybrid(self.texts, n_topics=n_topics, model=model)
        
        if topic_data.get("error"):
            self.error.emit(topic_data["error"])
        else:
            # Wrap in list to match finished signal signature
            self.finished.emit([topic_data])

    def _run_sentiment(self):
        from nlp_engine import analyze_sentiment, analyze_sentiment_online
        results = []
        total = len(self.texts)
        mode = self.options.get('mode', 'local') # 'local', 'online', 'hybrid'
        model = self.options.get('model', None)
        
        for i, doc in enumerate(self.texts):
            if self._is_canceled:
                return
            
            status = f"Analiz ediliyor ({mode}): {doc['title']} ({i+1}/{total})"
            self.progress.emit(i, status)
            
            res = {
                "doc_id": doc["doc_id"],
                "title": doc.get("title", "Belge"),
                "mode": mode
            }
            
            if mode in ['local', 'hybrid']:
                sentiment = analyze_sentiment(doc["text"])
                res["local"] = sentiment
                # Compatibility defaults
                res["label"] = sentiment.get("label")
                res["score"] = sentiment.get("score")
                res["summary"] = sentiment.get("summary")
                
            if mode in ['online', 'hybrid']:
                online_sentiment = analyze_sentiment_online(doc["text"], model=model)
                res["online"] = online_sentiment
                if mode == 'online':
                    res["label"] = online_sentiment.get("label")
                    res["score"] = online_sentiment.get("score")
                    res["summary"] = online_sentiment.get("summary")
            
            results.append(res)
            
        self.finished.emit(results)

    def _run_ner(self):
        from nlp_engine import extract_entities, extract_entities_online, compare_entity_results, _aggregate_entity_documents
        total = len(self.texts)
        mode = self.options.get('mode', 'local')
        model = self.options.get('model', None)
        
        documents = []
        
        for i, doc in enumerate(self.texts):
            if self._is_canceled:
                return
            
            self.progress.emit(i, f"Varlıklar aranıyor ({mode}): {doc['title']} ({i+1}/{total})")

            if mode == 'local':
                entities = extract_entities(doc["text"])
                documents.append({
                    "doc_id": doc["doc_id"],
                    "title": doc.get("title", "Belge"),
                    "entities": entities
                })
            elif mode == 'online':
                entities = extract_entities_online(doc["text"], model=model)
                documents.append({
                    "doc_id": doc["doc_id"],
                    "title": doc.get("title", "Belge"),
                    "entities": entities
                })
            else:
                local_entities = extract_entities(doc["text"])
                online_entities = extract_entities_online(doc["text"], model=model)
                documents.append({
                    "doc_id": doc["doc_id"],
                    "title": doc.get("title", "Belge"),
                    "local_entities": local_entities,
                    "online_entities": online_entities,
                    "comparison": compare_entity_results(local_entities, online_entities)
                })

        if self._is_canceled:
            return
            
        final_data = [_aggregate_entity_documents(documents, mode=mode)]
        self.finished.emit(final_data)

    def _run_keywords(self):
        from nlp_engine import extract_keywords, clean_html
        
        combined_text = self.options.get('combined_text', "")
        doc_label = self.options.get('doc_label', "Belge")
        top_n = self.options.get('top_n', 30)
        ngram_size = self.options.get('ngram_size', 2)
        dedup_lim = self.options.get('dedup_lim', 0.9)
        
        if not combined_text:
            self.error.emit("Analiz edilecek metin bulunamadı.")
            return

        self.progress.emit(0, "Anahtar kelimeler ayıklanıyor...")
        keywords = extract_keywords(combined_text, top_n=top_n, ngram_size=ngram_size, dedup_lim=dedup_lim)
        
        self.finished.emit([ {
            "keywords": keywords,
            "doc_label": doc_label,
            "settings": {
                'top_n': top_n, 
                'ngram_size': ngram_size, 
                'dedup_lim': dedup_lim
            }
        } ])

    def _run_kwic(self):
        from nlp_engine import extract_kwic
        keyword = self.options.get('keyword', '').strip()
        if not keyword:
            self.error.emit("KWIC için anahtar kelime boş olamaz.")
            return
        total = len(self.texts)
        all_results = []
        for i, doc in enumerate(self.texts):
            if self._is_canceled:
                return
            self.progress.emit(i, f"KWIC aranıyor: {doc['title']} ({i+1}/{total})")
            hits = extract_kwic(doc["text"], keyword)
            for hit in hits:
                hit['doc_title'] = doc['title']
            all_results.extend(hits)
        self.finished.emit([{
            "keyword": keyword,
            "doc_label": f"{total} belge" if total > 1 else (self.texts[0]["title"] if self.texts else ""),
            "results": all_results
        }])

    def _run_document_portrait(self):
        from nlp_engine import calculate_document_portrait
        doc_len = self.options.get('doc_len', 0)
        title = self.options.get('title', 'Belge')
        segments = self.options.get('segments', [])
        self.progress.emit(0, "Belge portresi hesaplanıyor...")
        grid_colors = calculate_document_portrait(doc_len, segments)
        self.finished.emit([{
            "title": title,
            "segments_count": len(segments),
            "grid_colors": grid_colors
        }])


class SemanticWorker(QThread):
    """Background worker for Semantic Mapping with BGE-M3."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, segments: list):
        super().__init__()
        self.segments = segments

    def run(self):
        try:
            from nlp.tasks.semantic import build_cluster_map_data
            self.progress.emit(0, "BERT/BGE-M3 Modeli yükleniyor...")
            
            # This is where the heavy work happens
            # Note: build_cluster_map_data can take significant time
            cluster_data = build_cluster_map_data(self.segments)
            
            self.progress.emit(100, "Analiz tamamlandı.")
            self.finished.emit(cluster_data)
        except Exception as e:
            logger.error(f"SemanticWorker Error: {e}", exc_info=True)
            self.error.emit(str(e))


# ============================================================================
# SynthesisWorker — Hibrit NER Sonuçlarını AI Hakem ile Sentezleme
# ============================================================================

class SynthesisWorker(QThread):
    """
    Runs AI-judge synthesis of hybrid NLP results in a background thread.
    Supports NER, Sentiment, and Topic Modeling.

    Signals:
        finished(object): The synthesized data (dict or list).
        error(str): Error message if synthesis fails.
        progress(int, str): Progress updates.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, data: object, task_type: str = "ner", judge_model: str = None, original_model: str = None):
        super().__init__()
        self.data = data
        self.task_type = task_type
        self.judge_model = judge_model
        self.original_model = original_model
        self._is_canceled = False

    def cancel(self):
        self._is_canceled = True

    def run(self):
        try:
            self.progress.emit(0, f"Hakem AI {self.task_type} sonuçlarını sentezliyor...")
            
            if self.task_type == "ner":
                from nlp.tasks.consensus import synthesize_entity_results_online
                result = synthesize_entity_results_online(
                    self.data, 
                    model=self.original_model, 
                    judge_model=self.judge_model
                )
            elif self.task_type == "sentiment":
                from nlp.tasks.consensus import synthesize_sentiment_results_online
                result = synthesize_sentiment_results_online(
                    self.data, 
                    judge_model=self.judge_model
                )
            elif self.task_type == "topics":
                from nlp.tasks.consensus import synthesize_topic_results_online
                result = synthesize_topic_results_online(
                    self.data, 
                    judge_model=self.judge_model
                )
            else:
                self.error.emit(f"Bilinmeyen görev türü: {self.task_type}")
                return

            if self._is_canceled:
                return

            if isinstance(result, dict) and result.get("error"):
                self.error.emit(result["error"])
            else:
                self.finished.emit(result)
        except Exception as e:
            logger.error(f"SynthesisWorker error: {e}", exc_info=True)
            self.error.emit(str(e))


# ============================================================================
# GenericWorker — Tek Seferlik / IO Ağır İşlemler
# ============================================================================

class GenericWorker(QThread):
    """
    Herhangi bir callable'ı arka planda çalıştıran genel amaçlı thread.

    Kullanım örneği:
        worker = GenericWorker(project_manager.save, path="/proje/yolu")
        worker.finished_ok.connect(lambda result: statusbar.showMessage("Kaydedildi"))
        worker.finished_err.connect(lambda err: show_error(...))
        worker.start()

    Avantajı:
        - Proje kaydetme, DB export, toplu NLP gibi IO-heavy işleri UI'dan koparır.
        - Aynı sinyal/slot altyapısıyla çalışır → tutarlı hata raporlama.
    """

    finished_ok  = pyqtSignal(object)   # callable'ın dönüş değeri
    finished_err = pyqtSignal(str)       # hata mesajı
    progress     = pyqtSignal(int, str)  # opsiyonel ilerleme (% , mesaj)

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._is_canceled = False

    def cancel(self) -> None:
        """İşlemi iptal etmek için işaret koyar (cooperative cancellation)."""
        self._is_canceled = True

    def run(self) -> None:
        if self._is_canceled:
            return
        try:
            result = self._fn(*self._args, **self._kwargs)
            if not self._is_canceled:
                self.finished_ok.emit(result)
        except Exception as exc:
            logger.error(
                f"GenericWorker [{self._fn.__name__}] hatası: {exc}",
                exc_info=True,
            )
            if not self._is_canceled:
                self.finished_err.emit(str(exc))


# ============================================================================
# SurveyImportWorker — Excel Anket Gönderimi Prosesi
# ============================================================================

class SurveyImportWorker(QThread):
    """Worker for importing structured survey data into the database."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(int)  # returns number of imported documents
    error = pyqtSignal(str)

    def __init__(self, db_path: str, rows: list, folder_id: int = None, survey_name: str = "Anket Verisi", include_headers: bool = False):
        super().__init__()
        self.db_path = db_path
        self.rows = rows  # List[SurveyRow]
        self.folder_id = folder_id
        self.survey_name = survey_name
        self.include_headers = include_headers
        self._is_canceled = False

    def cancel(self):
        self._is_canceled = True

    def run(self):
        try:
            from database.document_dao import DocumentDAO
            from database.variable_dao import VariableDAO, VariableValueDAO
            from database.code_dao import CodeDAO
            from database.segment_dao import CodedSegmentDAO
            from database.folder_dao import FolderDAO
            
            doc_dao = DocumentDAO(self.db_path)
            var_dao = VariableDAO(self.db_path)
            val_dao = VariableValueDAO(self.db_path)
            code_dao = CodeDAO(self.db_path)
            seg_dao = CodedSegmentDAO(self.db_path)
            folder_dao = FolderDAO(self.db_path)
            
            # Cache structures to avoid redundant db calls
            existing_vars = {v['name']: v['id'] for v in var_dao.get_all()}
            existing_codes = {c['name']: c['id'] for c in code_dao.get_all()}
            
            # Determine the base folder for this import
            import_base_folder_id = self.folder_id
            if self.survey_name:
                # Find if survey folder already exists under the current parent
                all_folders = folder_dao.get_all()
                survey_folder = next((f for f in all_folders if f['name'] == self.survey_name and f['parent_id'] == self.folder_id), None)
                
                if survey_folder:
                    import_base_folder_id = survey_folder['id']
                else:
                    import_base_folder_id = folder_dao.create(self.survey_name, self.folder_id)
            
            # Cache folders that are direct children of the import base folder (for row.group_name)
            existing_folders = {f['name']: f['id'] for f in folder_dao.get_all() if f['parent_id'] == import_base_folder_id}
            
            # Create Parent Code for this Survey
            parent_code_id = None
            if self.survey_name:
                if self.survey_name in existing_codes:
                    parent_code_id = existing_codes[self.survey_name]
                else:
                    parent_code_id = code_dao.create(
                        name=self.survey_name, 
                        description="Anket İçe Aktarım Grubu", 
                        color="#10B981" # Emerald color for the parent survey code
                    )
                    existing_codes[self.survey_name] = parent_code_id
            
            total = len(self.rows)
            imported_count = 0
            for i, row in enumerate(self.rows):
                if self._is_canceled:
                    break
                
                self.progress.emit(i, f"İçe aktarılıyor: {row.doc_name} ({i+1}/{total})")
                
                # Determine Target Folder based on Grouping
                target_folder_id = import_base_folder_id
                if row.group_name:
                    group_name = str(row.group_name).strip()
                    if group_name:
                        if group_name not in existing_folders:
                            new_folder_id = folder_dao.create(group_name, import_base_folder_id)
                            existing_folders[group_name] = new_folder_id
                        target_folder_id = existing_folders[group_name]
                        
                # Combine coded_texts into a single document text
                blocks = []
                for title, text in row.coded_texts.items():
                    # Temizleyip düz \n satır sonlarına indirgeyelim! DB/QTextEdit karakter kaymasına engel olmak için.
                    cl_text = str(text).replace('\r\n', '\n').replace('\r', '\n')
                    if self.include_headers:
                        blocks.append(f"--- {title} ---\n{cl_text}")
                    else:
                        blocks.append(cl_text)
                
                full_text = "\n\n".join(blocks)
                if not full_text:
                    full_text = "Metin Yok"
                
                # Create Document
                import uuid
                unique_path = f"survey_import_{uuid.uuid4().hex[:8]}_{i}"
                doc_id = doc_dao.create(
                    title=row.doc_name,
                    file_path=unique_path,
                    file_type="survey",
                    extracted_text=full_text,
                    folder_id=target_folder_id
                )
                
                # Process Variables
                for var_name, var_value in row.variables.items():
                    # Get or Create Variable with specific Type
                    if var_name not in existing_vars:
                        # Determine Type (from Wizard) mapped to DB constraint ('text', 'integer', 'boolean')
                        v_type_raw = row.var_types.get(var_name, "Metin")
                        v_type_map = {"Metin": "text", "Tarih/Saat": "text", "Tamsayı": "integer", "Ondalık": "text"}
                        mapped_v_type = v_type_map.get(v_type_raw, "text")
                        
                        var_id = var_dao.create(var_name, mapped_v_type)
                        existing_vars[var_name] = var_id
                    else:
                        var_id = existing_vars[var_name]
                        
                    # Save Variable Value for this Document
                    val_dao.set_value(doc_id, var_id, var_value)
                    
                # Create/Set Codes and Segments
                current_pos = 0
                for title, text in row.coded_texts.items():
                    cl_text = str(text).replace('\r\n', '\n').replace('\r', '\n')
                    header = f"--- {title} ---\n" if self.include_headers else ""
                    start_pos = current_pos + len(header)
                    end_pos = start_pos + len(cl_text)
                    
                    if title not in existing_codes:
                        org_name = row.org_coded_names.get(title, "Anket açık uçlu sorusu")
                        cid = code_dao.create(
                            name=title, 
                            description=org_name, 
                            color="#4F46E5", # Use indigo for survey codes
                            parent_id=parent_code_id
                        ) 
                        existing_codes[title] = cid
                        
                    seg_dao.create(
                        document_id=doc_id,
                        code_id=existing_codes[title],
                        start_pos=start_pos,
                        end_pos=end_pos,
                        segment_text=cl_text
                    )
                    
                    # Move position marker by exact block size plus the double newline joiner
                    block_len = len(header) + len(cl_text)
                    current_pos += block_len + 2
                
                imported_count = i + 1
            
            self.finished.emit(imported_count)
            
        except Exception as e:
            logger.error(f"Survey Import Error: {e}", exc_info=True)
            self.error.emit(str(e))



# ============================================================================
# DataLoaderWorker — Background Loading of Initial Project Data
# ============================================================================

class DataLoaderWorker(QThread):
    """
    Background worker for loading initial project data (documents, folders, codes).
    Prevents UI freeze on startup for large projects.
    """
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, doc_dao, folder_dao, code_dao):
        super().__init__()
        self.doc_dao = doc_dao
        self.folder_dao = folder_dao
        self.code_dao = code_dao

    def run(self):
        try:
            # 1. Load Documents & Folders
            documents = self.doc_dao.get_all()
            folders = self.folder_dao.get_all()
            
            # 2. Load Codes
            codes = self.code_dao.get_all()
            
            results = {
                'documents': documents,
                'folders': folders,
                'codes': codes
            }
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"DataLoaderWorker Error: {e}", exc_info=True)
            self.error.emit(str(e))
