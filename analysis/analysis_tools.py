"""
Analysis modules for LexiScholar - Refactored for Stage 4
Implements Strategy Pattern for different analysis types.
"""

import re
from functools import lru_cache
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Any, Protocol
from dataclasses import dataclass

TR_STOP_WORDS = {
    've', 'bir', 'bu', 'de', 'da', 'ile', 'için', 'ama', 'daha', 'çok', 'en', 'olarak', 
    'gibi', 'kadar', 'var', 'yok', 'diye', 'olan', 'ya', 'ki', 'ise', 'mi', 'mı', 'mu', 'mü',
    'şeyi', 'şeye', 'şeyi', 'bunun', 'buna', 'bunu', 'şunun', 'şuna', 'şunu', 'onun', 'ona', 'onu',
    'kendi', 'kendisi', 'çünkü', 'göre', 'bile', 'eğer', 'ise', 'ancak', 'veya', 'yahut', 'belki',
    'nasıl', 'neden', 'niçin', 'kim', 'hangi', 'nereye', 'nerede', 'nereden', 'ne', 'zaman'
}

EN_STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', 
    "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 
    'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't", 'also', 'therefore', 'could', 'would'
}

STOP_WORDS = TR_STOP_WORDS | EN_STOP_WORDS

class AnalysisStrategy(Protocol):
    """Protocol for analytical computation strategies."""
    def run(self, daos: Any, **kwargs) -> Any:
        ...

class CodeStatisticsStrategy:
    def run(self, daos: Any) -> List[Dict]:
        codes = daos.codes.get_all()
        stats = []
        for code in codes:
            segments = daos.segments.get_by_code(code['id'])
            doc_ids = set(s['document_id'] for s in segments)
            total_chars = sum(s['end_pos'] - s['start_pos'] for s in segments)
            stats.append({
                'id': code['id'], 'name': code['name'], 'color': code['color'],
                'segment_count': len(segments), 'document_count': len(doc_ids),
                'total_characters': total_chars
            })
        return sorted(stats, key=lambda x: x['segment_count'], reverse=True)

class WordFrequencyStrategy:
    @lru_cache(maxsize=8)
    def _get_word_pattern(self, min_length: int) -> re.Pattern:
        return re.compile(rf'\b[a-zçğıöşü]{{{min_length},}}\b')

    def run(self, daos: Any, doc_id: Optional[int] = None, min_length: int = 3, top_n: int = 50) -> List[Tuple[str, int]]:
        documents = [daos.documents.get_by_id(doc_id)] if doc_id else daos.documents.get_all()
        counter = Counter()
        pattern = self._get_word_pattern(min_length)
        
        for doc in documents:
            if not doc: continue
            text = (doc.get('extracted_text') or doc.get('content') or "").lower()
            
            # Remove style/script tags and their contents
            text = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL)
            # Remove remaining HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Remove HTML entities
            text = re.sub(r'&[a-z]+;', ' ', text)
            
            words = pattern.findall(text)
            counter.update([w for w in words if w not in STOP_WORDS])
            
        return counter.most_common(top_n)

class CoOccurrenceStrategy:
    def run(self, daos: Any, code_ids: List[int] = None) -> Tuple[List[Dict], List[List[int]]]:
        all_codes = daos.codes.get_all()
        codes = [c for c in all_codes if c['id'] in code_ids] if code_ids else all_codes
        n = len(codes)
        matrix = [[0 for _ in range(n)] for _ in range(n)]
        code_docs = {c['id']: set(s['document_id'] for s in daos.segments.get_by_code(c['id'])) for c in codes}
        
        for i in range(n):
            for j in range(n):
                if i == j: matrix[i][j] = len(code_docs[codes[i]['id']])
                else: matrix[i][j] = len(code_docs[codes[i]['id']].intersection(code_docs[codes[j]['id']]))
        return codes, matrix

class CodeMatrixStrategy:
    """Calculates code frequency per document (Heatmap data)."""
    def run(self, daos: Any) -> Tuple[List[Dict], List[Dict], List[List[int]]]:
        codes = daos.codes.get_all()
        docs = daos.documents.get_all()
        
        n_codes = len(codes)
        n_docs = len(docs)
        matrix = [[0 for _ in range(n_docs)] for _ in range(n_codes)]
        
        # Build mapping for fast indexing
        code_idx = {c['id']: i for i, c in enumerate(codes)}
        doc_idx = {d['id']: j for j, d in enumerate(docs)}
        
        # Fill matrix
        for i, code in enumerate(codes):
            segments = daos.segments.get_by_code(code['id'])
            for s in segments:
                d_id = s.get('document_id')
                if d_id in doc_idx:
                    matrix[i][doc_idx[d_id]] += 1
                    
        return codes, docs, matrix

class VariableStatisticsStrategy:
    """Calculates frequency distribution for a document variable."""
    def run(self, daos: Any, var_id: int) -> Dict:
        # Get all document values for this variable
        all_values = daos.variable_values.get_all_document_values()
        var_values = [v for v in all_values if v['variable_id'] == var_id]
        
        # Get all document titles for labels
        docs = daos.documents.get_all()
        doc_map = {d['id']: d['title'] for d in docs}
        
        counts = Counter()
        doc_lists = defaultdict(list)
        
        for v in var_values:
            val_str = str(v['value']).strip() if v['value'] is not None else "(Boş)"
            if val_str == "": val_str = "(Boş)"
            counts[val_str] += 1
            
            d_id = v['document_id']
            if d_id in doc_map:
                doc_lists[val_str].append(doc_map[d_id])
            
        total = sum(counts.values())
        
        stats = []
        # Sort values
        sorted_values = sorted(counts.keys())
        
        for val in sorted_values:
            count = counts[val]
            percentage = (count / total * 100) if total > 0 else 0
            stats.append({
                'value': val,
                'count': count,
                'percentage': percentage,
                'docs': sorted(doc_lists[val])
            })
            
        return {
            'stats': stats,
            'total_count': total
        }

class QuotesByVariablesStrategy:
    """Groups coded segments by document variable values."""
    def run(self, daos: Any, code_ids: List[int], var_id: int) -> Dict:
        # Get all selected code names for labels
        all_codes = daos.codes.get_all()
        code_names = {c['id']: c['name'] for c in all_codes if c['id'] in code_ids}
        
        # Collect all segments for all selected codes
        all_segments = []
        for c_id in code_ids:
            segs = daos.segments.get_by_code(c_id)
            for s in segs:
                s['code_name'] = code_names.get(c_id, "Bilinmeyen Kod")
                all_segments.append(s)
        
        # Get variable values for all documents for this variable
        all_values = daos.variable_values.get_all_document_values()
        var_values = {v['document_id']: str(v['value']).strip() if v['value'] is not None else "(Boş)" 
                      for v in all_values if v['variable_id'] == var_id}
        
        # Get document titles for display
        docs = daos.documents.get_all()
        doc_titles = {d['id']: d['title'] for d in docs}
        
        # Group segments
        grouped_data = defaultdict(list)
        for seg in all_segments:
            doc_id = seg.get('document_id')
            val = var_values.get(doc_id, "(Boş)")
            if val == "": val = "(Boş)"
            
            # Enrich segment with document title
            seg['document_title'] = doc_titles.get(doc_id, f"Belge {doc_id}")
            grouped_data[val].append(seg)
            
        return {
            'groups': dict(grouped_data),
            'total_segments': len(all_segments)
        }

class QuoteMatrixStrategy:
    """Calculates code x variable matrix with segment references."""
    def run(self, daos: Any, code_ids: List[int], var_id: int) -> Dict:
        # Get codes
        all_codes = daos.codes.get_all()
        selected_codes = [c for c in all_codes if c['id'] in code_ids]
        
        # Get document values for column grouping
        all_values = daos.variable_values.get_all_document_values()
        doc_vars = {v['document_id']: str(v['value']).strip() if v['value'] is not None else "(Boş)" 
                    for v in all_values if v['variable_id'] == var_id}
        
        # Unique group values (columns)
        groups = sorted(list(set(doc_vars.values())))
        if not groups: groups = ["(Boş)"]
        
        # Get document titles
        docs = daos.documents.get_all()
        doc_map = {d['id']: d['title'] for d in docs}
        
        matrix = []
        quotes_lookup = {} # Key: "code_id:group_val", Value: [segment, ...]
        
        for code in selected_codes:
            row = []
            segments = daos.segments.get_by_code(code['id'])
            
            # Count by group
            counts = Counter()
            temp_quotes = defaultdict(list)
            
            for s in segments:
                d_id = s.get('document_id')
                g_val = doc_vars.get(d_id, "(Boş)")
                if g_val == "": g_val = "(Boş)"
                counts[g_val] += 1
                
                # Enrich segment for display
                s['document_title'] = doc_map.get(d_id, f"Belge {d_id}")
                s['code_name'] = code['name']
                temp_quotes[g_val].append(s)
                
            for g_val in groups:
                row.append(counts[g_val])
                quotes_lookup[f"{code['id']}:{g_val}"] = temp_quotes[g_val]
                
            matrix.append(row)
            
        return {
            'codes': selected_codes,
            'groups': groups,
            'matrix': matrix,
            'quotes': quotes_lookup
        }

class VarianceAnalysisStrategy:
    """Performs One-Way ANOVA for code frequencies across variable groups."""
    def run(self, daos: Any, code_id: int, var_id: int) -> Dict:
        try:
            from scipy import stats
            import numpy as np
        except ImportError:
            return {'error': "Scipy kütüphanesi yüklü değil."}
        
        # Get variable values for all documents
        all_vals = daos.variable_values.get_all_document_values()
        # Filter for selected variable and valid values
        var_vals = {v['document_id']: str(v['value']) for v in all_vals 
                   if v['variable_id'] == var_id and v['value'] is not None and str(v['value']).strip() != ""}
        
        if not var_vals:
            return {'error': "Seçilen değişken için veri bulunamadı."}

        # Get code segments
        segments = daos.segments.get_by_code(code_id)
        doc_freqs = Counter([s['document_id'] for s in segments])
        
        # Group data
        groups = defaultdict(list)
        all_docs = daos.documents.get_all()
        
        for doc in all_docs:
            d_id = doc['id']
            # Only consider documents that have a value for this variable
            if d_id in var_vals:
                group_val = var_vals[d_id]
                freq = doc_freqs.get(d_id, 0)
                groups[group_val].append(freq)
                
        # Filter groups with less than 2 samples (ANOVA requires variance)
        valid_groups = {k: v for k, v in groups.items() if len(v) >= 2}
        
        if len(valid_groups) < 2:
            return {'error': "ANOVA analizi için en az 2 farklı grup ve her grupta en az 2 belge gereklidir."}
            
        # Run ANOVA
        group_lists = list(valid_groups.values())
        
        # Check if all values are identical (zero variance), f_oneway throws error or warning
        if all(len(set(g)) == 1 and g[0] == group_lists[0][0] for g in group_lists):
             return {'error': "Tüm gruplarda varyans sıfır (değerler aynı). İstatistiksel test yapılamaz."}

        try:
            f_stat, p_val = stats.f_oneway(*group_lists)
        except Exception as e:
            return {'error': f"İstatistiksel hesaplama hatası: {str(e)}"}
        
        # Stats per group
        group_stats = {}
        for g_name, values in valid_groups.items():
            group_stats[g_name] = {
                'n': len(values),
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'sum': int(sum(values)),
                'values': values # Keep for boxplot if needed later
            }
            
        return {
            'f_statistic': float(f_stat),
            'p_value': float(p_val),
            'groups': group_stats,
            'significant': p_val < 0.05,
            'df_between': len(valid_groups) - 1,
            'df_within': sum(len(v) for v in valid_groups.values()) - len(valid_groups)
        }

class AnalysisTools:
    """Entry point for executing analytical strategies."""
    def __init__(self, doc_dao, code_dao, segment_dao, var_dao=None, var_value_dao=None):
        # Initializing a proxy DAO manager for internal consistency
        from dataclasses import make_dataclass
        fields = ["documents", "codes", "segments"]
        values = [doc_dao, code_dao, segment_dao]
        
        if var_dao:
            fields.append("variables")
            values.append(var_dao)
        if var_value_dao:
            fields.append("variable_values")
            values.append(var_value_dao)
            
        self.daos = make_dataclass("DAOs", fields)(*values)

    def analyze(self, strategy: AnalysisStrategy, **kwargs) -> Any:
        return strategy.run(self.daos, **kwargs)

    # Backward compatibility wrapper methods
    def get_code_statistics(self) -> List[Dict]:
        return self.analyze(CodeStatisticsStrategy())

    def get_word_frequency(self, doc_id: Optional[int] = None, min_length: int = 3, top_n: int = 50) -> List[Tuple[str, int]]:
        return self.analyze(WordFrequencyStrategy(), doc_id=doc_id, min_length=min_length, top_n=top_n)

    def get_cooccurrence_matrix(self, code_ids: List[int] = None) -> Tuple[List[Dict], List[List[int]]]:
        return self.analyze(CoOccurrenceStrategy(), code_ids=code_ids)

    def get_code_matrix(self) -> Tuple[List[Dict], List[Dict], List[List[int]]]:
        return CodeMatrixStrategy().run(self.daos)

    def extract_keywords(self, doc_id: Optional[int] = None, top_n: int = 20) -> List[Dict]:
        return KeywordExtractionStrategy().run(self.daos, doc_id=doc_id, top_n=top_n)

    def get_kwic(self, keyword: str, context_chars: int = 50, doc_id: Optional[int] = None) -> List[Dict]:
        return KWICStrategy().run(self.daos, keyword=keyword, context_chars=context_chars, doc_id=doc_id)

    def get_document_portrait(self, doc_id: int) -> List[str]:
        return DocumentPortraitStrategy().run(self.daos, doc_id=doc_id)

    def get_crosstab_matrix(self, var_id: int) -> Tuple[List[Dict], List[str], List[List[int]]]:
        return CrosstabStrategy().run(self.daos, var_id=var_id)

    def get_variable_statistics(self, var_id: int) -> Dict:
        return VariableStatisticsStrategy().run(self.daos, var_id=var_id)

    def get_quotes_by_variables(self, code_ids: List[int], var_id: int) -> Dict:
        return QuotesByVariablesStrategy().run(self.daos, code_ids=code_ids, var_id=var_id)

    def get_quote_matrix(self, code_ids: List[int], var_id: int) -> Dict:
        return QuoteMatrixStrategy().run(self.daos, code_ids=code_ids, var_id=var_id)
        
    def get_variance_analysis(self, code_id: int, var_id: int) -> Dict:
        return VarianceAnalysisStrategy().run(self.daos, code_id=code_id, var_id=var_id)


class KeywordExtractionStrategy:
    """Extracts keywords using TF-IDF like simple frequency for now."""
    def run(self, daos: Any, doc_id: Optional[int] = None, top_n: int = 20) -> List[Dict]:
        documents = [daos.documents.get_by_id(doc_id)] if doc_id else daos.documents.get_all()
        
        pattern = re.compile(r'\b\w{3,}\b')
        counter = Counter()

        for doc in documents:
            if not doc: continue
            text = (doc.get('extracted_text') or doc.get('content') or "").lower()
            
            # Remove style/script tags and their contents
            text = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL)
            # Remove remaining HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Remove HTML entities
            text = re.sub(r'&[a-z]+;', ' ', text)
            
            words = pattern.findall(text)
            counter.update([w for w in words if w not in STOP_WORDS])
            
        common = counter.most_common(top_n)
        if not common: return []
        
        max_count = common[0][1]
        return [{'keyword': w, 'score': c / max_count, 'count': c} for w, c in common]

class KWICStrategy:
    """Keywords in Context analysis."""
    def run(self, daos: Any, keyword: str, context_chars: int = 50, doc_id: Optional[int] = None) -> List[Dict]:
        documents = [daos.documents.get_by_id(doc_id)] if doc_id else daos.documents.get_all()
        results = []
        keyword_lower = keyword.lower()
        
        for doc in documents:
            if not doc: continue
            text = (doc.get('extracted_text') or doc.get('content') or "")
            
            # Clean HTML to prevent CSS class leaks and HTML tags in context
            text = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'&[a-z]+;', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            text_lower = text.lower()
            
            start = 0
            while True:
                idx = text_lower.find(keyword_lower, start)
                if idx == -1: break
                
                # Extract context
                left_idx = max(0, idx - context_chars)
                right_idx = min(len(text), idx + len(keyword) + context_chars)
                
                results.append({
                    'doc_id': doc['id'],
                    'doc_title': doc['title'],
                    'left': text[left_idx:idx].strip(),
                    'keyword': text[idx:idx+len(keyword)],
                    'right': text[idx+len(keyword):right_idx].strip(),
                    'position': idx
                })
                start = idx + 1
        return results

class DocumentPortraitStrategy:
    """Generates a color sequence representing the document structure sorted by position."""
    def run(self, daos: Any, doc_id: int) -> List[str]:
        segments = daos.segments.get_by_document(doc_id)
        if not segments: return []
        
        # Sort by start position
        segments.sort(key=lambda x: x['start_pos'])
        
        # Map to colors
        # For a "portrait", we might want a grid where each cell represents a segment
        # OR a uniform grid representing the whole text, colored by dominant code at that position.
        # Simple version: Sequence of segment colors.
        return [s.get('code_color', '#cccccc') for s in segments]

class CrosstabStrategy:
    """Calculates code frequencies across document variable groups."""
    def run(self, daos: Any, var_id: int) -> Tuple[List[Dict], List[str], List[List[int]]]:
        codes = daos.codes.get_all()
        if not hasattr(daos, 'variable_values'):
            return codes, [], []
            
        # Get variable values for all documents
        all_values = daos.variable_values.get_all_document_values()
        
        # Filter values for the selected variable
        var_values = [v for v in all_values if v['variable_id'] == var_id]
        if not var_values:
            return codes, [], []
            
        # Group documents by variable value
        groups = sorted(list(set(str(v['value']).strip() if v['value'] is not None else "(Boş)" for v in var_values)))
        group_to_idx = {val: i for i, val in enumerate(groups)}
        doc_to_group = {v['document_id']: str(v['value']).strip() if v['value'] is not None else "(Boş)" for v in var_values}
        
        # Filter codes to only those belonging to the project and enrich with hierarchy
        code_metadata = []
        for c in codes:
            code_metadata.append({
                'id': c['id'],
                'name': c['name'],
                'color': c.get('color', '#3B82F6'),
                'parent_id': c.get('parent_id')
            })
            
        n_codes = len(code_metadata)
        n_groups = len(groups)
        matrix = [[0 for _ in range(n_groups)] for _ in range(n_codes)]
        
        # Fill matrix
        for i, code in enumerate(code_metadata):
            segments = daos.segments.get_by_code(code['id'])
            for s in segments:
                d_id = s.get('document_id')
                if d_id in doc_to_group:
                    val = doc_to_group[d_id]
                    if val in group_to_idx:
                        matrix[i][group_to_idx[val]] += 1
                        
        return code_metadata, groups, matrix
