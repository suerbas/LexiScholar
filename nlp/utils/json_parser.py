import json
import re
import logging

logger = logging.getLogger(__name__)

def _parse_json_response(response_text: str):
    # Strip markdown code blocks if present
    if "```json" in response_text:
        response_text = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    
    try:
        # strict=False allows control characters like newlines inside strings
        return json.loads(response_text, strict=False)
    except json.JSONDecodeError as e:
        logger.warning(f"Initial JSON parse failed: {e}. Attempting recovery.")
        
        # 1. Basic cleaning: remove trailing commas before closing braces/brackets
        cleaned_text = re.sub(r',\s*([\}\]])', r'\1', response_text)
        
        # 2. Try to find the first { and last }
        match = re.search(r'(\{.*\})|(\[.*\])', cleaned_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(), strict=False)
            except json.JSONDecodeError:
                pass
        
        # 3. Heuristic: If it looks truncated (missing closing brace/quote), try to patch it
        patched_text = cleaned_text.strip()
        if patched_text.startswith('{') and not patched_text.endswith('}'):
            logger.info("Response looks like truncated JSON. Attempting to patch.")
            
            # If it ends inside a string (no closing quote)
            unescaped_quotes = len(re.findall(r'(?<!\\)"', patched_text))
            if unescaped_quotes % 2 != 0:
                patched_text += '"'
            
            # Ensure all open braces are closed
            open_braces = patched_text.count('{')
            close_braces = patched_text.count('}')
            if open_braces > close_braces:
                patched_text += '}' * (open_braces - close_braces)
            
            # Ensure all open brackets are closed
            open_brackets = patched_text.count('[')
            close_brackets = patched_text.count(']')
            if open_brackets > close_brackets:
                patched_text += ']' * (open_brackets - close_brackets)
            
            try:
                return json.loads(patched_text, strict=False)
            except json.JSONDecodeError:
                pass

        # Final fallback
        logger.error(f"Failed to parse LLM response as JSON: {response_text[:500]}...")
        raise json.JSONDecodeError(f"Model geçersiz veya yarım kalan bir JSON döndürdü. (Hata: {str(e)})", e.doc, e.pos)
