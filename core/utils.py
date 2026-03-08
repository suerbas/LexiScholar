"""
General utility functions for LexiScholar logic.
Shared across database, processors, and UI.
"""
import os
import re

def sanitize_filename(filename):
    """Removes invalid characters from a filename."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def format_file_size(size_bytes):
    """Converts bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def natural_sort_key(s):
    """
    Key function for natural sorting (e.g., K1, K2, K10 instead of K1, K10, K2).
    Can be used in list.sort(key=...) or sorted(key=...).
    """
    if not isinstance(s, str):
        return [s]
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]
