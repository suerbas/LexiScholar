import re
from typing import List, Dict
from nlp.utils.text_utils import clean_html

def extract_kwic(text: str, keyword: str, context_window: int = 10) -> List[Dict]:
    clean_text = clean_html(text)
    words = clean_text.split()
    results, kw_lower = [], keyword.lower()
    for i, word in enumerate(words):
        if kw_lower in re.sub(r'[^\w\s]', '', word).lower():
            start, end = max(0, i - context_window), min(len(words), i + 1 + context_window)
            results.append({"left": " ".join(words[start:i]), "keyword": word, "right": " ".join(words[i+1:end])})
            if len(results) >= 500: break
    return results
