"""
OpenSearch Template Tags and Filters
"""
from django import template
import re

register = template.Library()


@register.filter
def clean_snippet(value):
    """
    Clean up snippet content by removing JSON-like metadata patterns
    """
    if not value:
        return ""
    
    # Convert to string
    text = str(value)
    
    # If it looks like a JSON/dict string, try to extract readable parts
    if text.startswith('{') or text.startswith("{'"):
        return ""
    
    # Remove common metadata patterns
    patterns_to_remove = [
        r"'created':\s*'[^']*'",
        r"'last_modified':\s*'[^']*'",
        r"'filename':\s*'[^']*'",
        r"'extension':\s*'[^']*'",
        r"'content_type':\s*'[^']*'",
        r"'filesize':\s*\d+",
        r"'indexing_date':\s*'[^']*'",
        r"'last_accessed':\s*'[^']*'",
        r"file://[^\s,}]+",
        r"\\\\[\w\-\.]+\\[^\s,}']+",
        r"//[\d\.]+/[^\s,}']+",
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text)
    
    # Clean up leftover punctuation
    text = re.sub(r"[{}']+", ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(' ,.:')
    
    return text


@register.filter
def extract_title(source):
    """
    Extract a clean title from source document
    """
    if not source:
        return "(無標題)"
    
    # Priority order for title extraction
    if source.get('title') and not str(source.get('title')).startswith('{'):
        return source.get('title')
    
    if source.get('file'):
        file_val = source.get('file')
        # If file looks like a filename, use it
        if '.' in str(file_val) and not str(file_val).startswith('{'):
            return file_val
    
    if source.get('projname'):
        return source.get('projname')
    
    if source.get('filename'):
        return source.get('filename')
    
    return "(無標題)"


@register.filter
def extract_snippet(source, highlight=None):
    """
    Extract a clean snippet from source document
    """
    if highlight:
        if highlight.get('content'):
            content_list = highlight.get('content', [])
            if content_list:
                return ' ... '.join(content_list)
        if highlight.get('file'):
            return f"檔案：{highlight.get('file')[0]}"
        if highlight.get('path'):
            return f"路徑：{highlight.get('path')[0]}"
    
    if not source:
        return ""
    
    # For file-based records, show file and path
    if source.get('file') and source.get('path'):
        file_val = str(source.get('file', ''))
        path_val = str(source.get('path', ''))
        
        # Skip if they look like JSON
        if not file_val.startswith('{') and not path_val.startswith('{'):
            result = f"檔案：{file_val}"
            if path_val:
                result += f"\n路徑：{path_val[:100]}..."
            return result
    
    # Try content field
    content = source.get('content', '')
    if content:
        content_str = str(content)
        if not content_str.startswith('{') and not content_str.startswith("{'"):
            return content_str[:250]
    
    # For project records, combine projname and constrname
    parts = []
    if source.get('projname'):
        parts.append(str(source.get('projname')))
    if source.get('constrname'):
        parts.append(str(source.get('constrname')))
    if source.get('client'):
        parts.append(f"業主：{source.get('client')}")
    
    if parts:
        return ' - '.join(parts)
    
    return ""


@register.filter
def to_windows_path(value):
    """Convert forward slashes to backslashes for Windows path display"""
    if not value:
        return value
    path = str(value)
    # Convert forward slashes to backslashes
    path = path.replace('/', '\\')
    return path


@register.filter
def is_json_like(value):
    """Check if value looks like JSON/dict or is actually a dict"""
    if not value:
        return False
    # If it's already a dict or list, it's "json like"
    if isinstance(value, (dict, list)):
        return True
    text = str(value)
    return text.startswith('{') or text.startswith("{'") or text.startswith('[')


@register.filter
def parse_fscrawler_meta(source):
    """
    Parse fscrawler metadata from source document.
    fscrawler stores data as:
    - file: dict with {url, virtual, root}
    - meta: dict with {created, date, modifier, author, title, etc.}
    - path: dict with {root, virtual, real}
    Returns a dict with: filename, created, modified, creator, path, extension, filesize, title
    """
    import os
    
    result = {
        'filename': '',
        'created': '',
        'modified': '',
        'creator': '',
        'path': '',
        'extension': '',
        'filesize': '',
        'title': '',
    }
    
    if not source:
        return result
    
    # Handle file field (can be dict or string)
    file_val = source.get('file')
    if file_val:
        if isinstance(file_val, dict):
            # fscrawler format: {'url': 'file://...', 'virtual': '/path/to/file.doc', ...}
            virtual = file_val.get('virtual', '')
            if virtual:
                result['filename'] = os.path.basename(virtual)
                result['path'] = virtual
            url = file_val.get('url', '')
            if url and url.startswith('file://'):
                result['path'] = url.replace('file://', '')
        elif isinstance(file_val, str) and not file_val.startswith('{'):
            result['filename'] = file_val
    
    # Handle path field (can be dict or string)  
    path_val = source.get('path')
    if path_val and not result.get('path'):
        if isinstance(path_val, dict):
            # fscrawler format: {'root': ..., 'virtual': '/path', 'real': '/full/path'}
            real = path_val.get('real', '') or path_val.get('virtual', '')
            if real:
                result['path'] = real
        elif isinstance(path_val, str) and not path_val.startswith('{'):
            result['path'] = path_val
    
    # Handle meta field (can be dict or string)
    meta = source.get('meta')
    if meta:
        if isinstance(meta, dict):
            # fscrawler format: {'created': 'ISO time', 'date': 'ISO time', 'modifier': '3155', ...}
            result['created'] = meta.get('created', '') or meta.get('date', '')
            result['modified'] = meta.get('date', '') or meta.get('modified', '')
            result['creator'] = meta.get('author', '') or meta.get('modifier', '') or meta.get('creator', '')
            result['title'] = meta.get('title', '')
            
            # Get file size if available in meta
            filesize = meta.get('filesize') or meta.get('content_length')
            if filesize:
                try:
                    size = int(filesize)
                    if size > 1024 * 1024:
                        result['filesize'] = f"{size / (1024*1024):.1f} MB"
                    elif size > 1024:
                        result['filesize'] = f"{size / 1024:.1f} KB"
                    else:
                        result['filesize'] = f"{size} B"
                except:
                    pass
    
    # Also check file.filesize (fscrawler stores size in file object)
    if not result.get('filesize') and file_val and isinstance(file_val, dict):
        filesize = file_val.get('filesize')
        if filesize:
            try:
                size = int(filesize)
                if size > 1024 * 1024:
                    result['filesize'] = f"{size / (1024*1024):.1f} MB"
                elif size > 1024:
                    result['filesize'] = f"{size / 1024:.1f} KB"
                else:
                    result['filesize'] = f"{size} B"
            except:
                pass
    
    # Extract filename from path if not already set
    if result['path'] and not result['filename']:
        result['filename'] = os.path.basename(result['path'])
    
    # Extract extension from filename
    if result['filename'] and '.' in result['filename']:
        result['extension'] = result['filename'].rsplit('.', 1)[-1].upper()
    
    # Format dates (convert ISO to readable)
    for date_field in ['created', 'modified']:
        if result[date_field]:
            date_val = str(result[date_field])
            if 'T' in date_val:
                date_val = date_val.split('T')[0]
            result[date_field] = date_val
    
    return result


@register.filter
def is_file_based(source):
    """Check if this is a file-based record (fscrawler)"""
    if not source:
        return False
    
    # fscrawler documents have 'file' as a dict with 'virtual' or 'url'
    file_val = source.get('file')
    if isinstance(file_val, dict):
        return 'virtual' in file_val or 'url' in file_val
    
    # Or 'path' as a dict
    path_val = source.get('path')
    if isinstance(path_val, dict):
        return 'virtual' in path_val or 'real' in path_val
    
    # Or 'meta' as a dict with file metadata
    meta = source.get('meta')
    if isinstance(meta, dict):
        return 'created' in meta or 'modifier' in meta or 'author' in meta
    
    return False


@register.filter
def is_secret_data(source):
    """Check if this document is marked as secret (sensitive data)"""
    if not source:
        return False
    return bool(source.get('secret'))
