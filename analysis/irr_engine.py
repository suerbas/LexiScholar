"""
IRR Engine for LexiScholar
Calculates Cohen's Kappa and Percent Agreement between raters.
"""

import numpy as np
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from sklearn.metrics import cohen_kappa_score

class IRREngine:
    """Calculates reliability metrics between two coders using character-level arrays."""
    
    def __init__(self, doc_dao, segment_dao):
        self.doc_dao = doc_dao
        self.segment_dao = segment_dao

    def calculate_reliability(self, doc_ids: List[int], coder1_id: int, coder2_id: int, code_ids: List[int] = None) -> Dict:
        """
        Calculate IRR metrics between two coders using sklearn's cohen_kappa_score on a character level.
        """
        coder1_data = defaultdict(list)
        coder2_data = defaultdict(list)
        
        segs1_bulk = self.segment_dao.get_by_documents_bulk(doc_ids, coder_id=coder1_id)
        segs2_bulk = self.segment_dao.get_by_documents_bulk(doc_ids, coder_id=coder2_id)

        for doc_id in doc_ids:
            segs1 = segs1_bulk.get(doc_id, [])
            segs2 = segs2_bulk.get(doc_id, [])
            
            for s in segs1:
                if code_ids is None or s['code_id'] in code_ids:
                    coder1_data[(doc_id, s['code_id'])].append(s)
            
            for s in segs2:
                if code_ids is None or s['code_id'] in code_ids:
                    coder2_data[(doc_id, s['code_id'])].append(s)
        
        # Get all relevant codes
        all_codes = set()
        for doc_id, code_id in coder1_data.keys(): all_codes.add(code_id)
        for doc_id, code_id in coder2_data.keys(): all_codes.add(code_id)
        
        if not all_codes:
            return {
                'overall_percent': 0.0,
                'kappa': 0.0,
                'total_agreements': 0,
                'total_instances': 0,
                'per_code': {}
            }
            
        doc_lengths = {}
        for doc_id in doc_ids:
            doc = self.doc_dao.get_by_id(doc_id)
            if doc and doc.get('extracted_text'):
                doc_lengths[doc_id] = len(doc['extracted_text'])
            else:
                doc_lengths[doc_id] = 0
                
        total_y1 = []
        total_y2 = []
        per_code_stats = {}
        
        for code_id in all_codes:
            code_y1 = []
            code_y2 = []
            
            for doc_id in doc_ids:
                doc_len = doc_lengths.get(doc_id, 0)
                if doc_len == 0: continue
                
                c1_arr = np.zeros(doc_len, dtype=int)
                c2_arr = np.zeros(doc_len, dtype=int)
                
                for s in coder1_data.get((doc_id, code_id), []):
                    start = max(0, s['start_pos'])
                    end = min(doc_len, s['end_pos'])
                    c1_arr[start:end] = 1
                    
                for s in coder2_data.get((doc_id, code_id), []):
                    start = max(0, s['start_pos'])
                    end = min(doc_len, s['end_pos'])
                    c2_arr[start:end] = 1
                    
                code_y1.extend(c1_arr.tolist())
                code_y2.extend(c2_arr.tolist())
            
            if not code_y1:
                continue
                
            code_agreements = sum(1 for i in range(len(code_y1)) if code_y1[i] == code_y2[i])
            instances = len(code_y1)
            percent = (code_agreements / instances * 100) if instances > 0 else 0
            
            # Show only coded instances (Union) in the UI tables instead of document length
            coded_instances = sum(1 for i in range(len(code_y1)) if code_y1[i] == 1 or code_y2[i] == 1)
            coded_agreements = sum(1 for i in range(len(code_y1)) if code_y1[i] == 1 and code_y2[i] == 1)
            
            per_code_stats[code_id] = {
                'agreements': coded_agreements, 
                'instances': coded_instances,   
                'percent': percent              
            }
            
            total_y1.extend(code_y1)
            total_y2.extend(code_y2)

        if not total_y1:
            return {
                'overall_percent': 0.0,
                'kappa': 0.0,
                'total_agreements': 0,
                'total_instances': 0,
                'per_code': per_code_stats
            }

        try:
            kappa = cohen_kappa_score(total_y1, total_y2)
            if str(kappa) == 'nan': kappa = 0.0 
        except Exception:
            kappa = 0.0
            
        total_instances = len(total_y1)
        total_agreements = sum(1 for i in range(total_instances) if total_y1[i] == total_y2[i])
        percent_agreement = (total_agreements / total_instances * 100) if total_instances > 0 else 0.0

        ui_total_instances = sum(1 for i in range(len(total_y1)) if total_y1[i] == 1 or total_y2[i] == 1)
        ui_total_agreements = sum(1 for i in range(len(total_y1)) if total_y1[i] == 1 and total_y2[i] == 1)

        return {
            'overall_percent': percent_agreement,
            'kappa': round(kappa, 4),
            'total_agreements': ui_total_agreements,
            'total_instances': ui_total_instances,
            'per_code': per_code_stats
        }
