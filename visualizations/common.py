import os
import tempfile
from datetime import datetime
from pathlib import Path

def _get_js_content(filename):
    """Read local JS file content."""
    try:
        # Try both development path and frozen path (if compiled)
        paths = [
            Path(__file__).parent.parent / "resources" / "js" / filename,
            Path(__file__).parent.parent.parent / "resources" / "js" / filename
        ]
        
        for js_path in paths:
            if js_path.exists():
                return js_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading JS file {filename}: {e}")
    return None

def save_html(html_content, prefix="report"):
    """Save HTML content to a temporary file and return the path."""
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(temp_dir, f"lexischolar_{prefix}_{timestamp}.html")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return file_path

def get_template(name):
    """Placeholder for template loading if needed."""
    return ""
