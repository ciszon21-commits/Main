"""
OpenSearch Client Service
Handles connection and queries to OpenSearch
"""
from opensearchpy import OpenSearch
from django.conf import settings
from django.core.cache import cache
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Singleton client instance for connection reuse
_client = None


def get_client():
    """
    Get OpenSearch client instance (singleton pattern).
    
    This implementation:
    - Reuses the same connection pool across requests
    - Configures timeout, retries, and compression for optimal performance
    - Reduces connection overhead for high-frequency searches
    """
    global _client
    if _client is None:
        _client = OpenSearch(
            hosts=[settings.OPENSEARCH_HOST],
            http_auth=(settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD),
            verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
            ssl_show_warn=False,
            # Performance optimization parameters
            timeout=getattr(settings, 'OPENSEARCH_TIMEOUT', 30),
            max_retries=getattr(settings, 'OPENSEARCH_MAX_RETRIES', 1),
            retry_on_timeout=getattr(settings, 'OPENSEARCH_RETRY_ON_TIMEOUT', False),
            http_compress=getattr(settings, 'OPENSEARCH_HTTP_COMPRESS', True),
        )
    return _client


def reset_client():
    """
    Reset the OpenSearch client singleton.
    Useful for testing or when connection settings change.
    """
    global _client
    _client = None


def get_indices():
    """Get list of user indices with stats"""
    client = get_client()
    indices = client.cat.indices(format='json')
    # Filter out system indices
    user_indices = [i for i in indices if not i['index'].startswith('.')]
    return sorted(user_indices, key=lambda x: x.get('index', ''))


def get_index_categories():
    """Get indices grouped by category"""
    # Try to get from cache first
    cache_key = 'opensearch_index_categories'
    cached_categories = cache.get(cache_key)
    if cached_categories:
        return cached_categories

    indices = get_indices()
    
    categories = {
        'sinobook_journal': {'name': '期刊', 'icon': '📰', 'indices': [], 'pattern': 'sinobook_journal*'},
        'sinobook': {'name': '圖書', 'icon': '📚', 'indices': [], 'pattern': 'sinobook*'},
        'sino_map': {'name': '地理圖資', 'icon': '🗺️', 'indices': [], 'pattern': 'sino_map*'},
        'sinoqa': {'name': '工程問題與對策', 'icon': '❓', 'indices': [], 'pattern': 'sinoqa*'},
        'sino_kmv1': {'name': '技術文件', 'icon': '📄', 'indices': [], 'pattern': 'sino_kmv1*'},
        'sino_kmv2': {'name': '組織知識', 'icon': '📑', 'indices': [], 'pattern': 'sino_kmv2*'},
        'sino_budget': {'name': '預算書', 'icon': '💰', 'indices': [], 'pattern': 'sino_budget*'},
        'sino_spec': {'name': '施工規範', 'icon': '📋', 'indices': [], 'pattern': 'sino_spec*'},
        'sino_cns': {'name': 'CNS 標準', 'icon': '📐', 'indices': [], 'pattern': 'sino_cns*'},
        # 'sinopmis_meeting': {'name': '會議紀錄', 'icon': '🗣️', 'indices': [], 'pattern': 'sinopmis_meeting*'},
        # 'sinopmis_file': {'name': 'PMIS 檔案', 'icon': '📁', 'indices': [], 'pattern': 'sinopmis_file*'},
        # 'sinopmis_iobook_in': {'name': '收文', 'icon': '📥', 'indices': [], 'pattern': 'sinopmis_iobook_in*'},
        # 'sinopmis_iobook_out': {'name': '發文', 'icon': '📤', 'indices': [], 'pattern': 'sinopmis_iobook_out*'},
        'sinoproject-dept': {'name': '部門封存', 'icon': '🏢', 'indices': [], 'pattern': 'sinoproject-dept*'},
        'sinoproject-early': {'name': '結案光碟', 'icon': '💿', 'indices': [], 'pattern': 'sinoproject-early*'},
        'sinoproject': {'name': '計畫封存', 'icon': '📦', 'indices': [], 'pattern': 'sinoproject*'},
        'sinoeng': {'name': '環興封存', 'icon': '🏗️', 'indices': [], 'pattern': 'sinoeng-*'},
        'sinobim_element': {'name': 'BIM 元件', 'icon': '🧱', 'indices': [], 'pattern': 'sinobim_element*'},
        'sinobim_issue': {'name': 'BIM 議題', 'icon': '⚠️', 'indices': [], 'pattern': 'sinobim_issue*'},
        'sinobim_file': {'name': 'BIM 檔案', 'icon': '📐', 'indices': [], 'pattern': 'sinobim_file*'},
        'sino_website_in': {'name': '內部網站', 'icon': '🌐', 'indices': [], 'pattern': 'sino_website_in*'},
        'sino_website_out': {'name': '外部網站', 'icon': '🔗', 'indices': [], 'pattern': 'sino_website_out*'},
        'sino_website_user': {'name': '用戶網站', 'icon': '👤', 'indices': [], 'pattern': 'sino_website_user*'},
        'sino_website_prkms': {'name': '採購網', 'icon': '🌍', 'indices': [], 'pattern': 'sino_website_prkms*'},
        'sino_prkms': {'name': '領標資料', 'icon': '🛒', 'indices': [], 'pattern': 'sino_prkms*'},
        'sino_carbon': {'name': '碳排放', 'icon': '🌱', 'indices': [], 'pattern': 'sino_carbon*'},
        'sino_drawing': {'name': '圖紙', 'icon': '✏️', 'indices': [], 'pattern': 'sino_drawing*'},
    }
    
    for idx in indices:
        name = idx['index']
        # Strip 're_' prefix for matching purposes (re-indexed indices)
        match_name = name[3:] if name.startswith('re_') else name
        matched = False
        # Order matters - more specific patterns first
        for cat_key in ['sinobook_journal', 'sinoproject-dept', 'sinoproject-early', 
                        'sinopmis_meeting', 'sinopmis_file', 'sinopmis_iobook_in', 'sinopmis_iobook_out',
                        'sinobim_element', 'sinobim_issue', 'sinobim_file',
                        'sino_website_in', 'sino_website_out', 'sino_website_user', 'sino_website_prkms',
                        'sinobook', 'sino_map', 'sinoqa', 'sino_kmv1', 'sino_kmv2',
                        'sino_budget', 'sino_spec', 'sino_cns', 'sinoproject', 'sinoeng',
                        'sino_prkms', 'sino_carbon', 'sino_drawing']:
            if cat_key in categories:
                pattern = cat_key.replace('-', '-')
                if match_name.startswith(pattern) or match_name.startswith(cat_key):
                    categories[cat_key]['indices'].append(idx)
                    matched = True
                    break
    
    # Calculate totals
    for cat in categories.values():
        cat['total_docs'] = sum(int(i.get('docs.count', 0) or 0) for i in cat['indices'])
        cat['count'] = len(cat['indices'])
    
    # Cache using configurable timeout (default 900 seconds = 15 minutes)
    cache_timeout = getattr(settings, 'OPENSEARCH_INDEX_CACHE_TIMEOUT', 900)
    cache.set(cache_key, categories, cache_timeout)
    
    return categories


# Department code reference
DEPT_CODES = {
    '02': '業務部',
    '03': '行政部',
    '04': '考核部',
    '06': '研資部',
    '08': '財會部',
    '11': '水利部',
    '12': '電力部',
    '14': '軌一部',
    '15': '環工部',
    '18': '建築部',
    '22': '園路部',
    '23': '法務部',
    '24': '軌二部',
    '25': '職安中心',
    '31': '結構部',
    '32': '地工部',
    '33': '機械部',
    '34': '系電部',
    '39': '工管部',
    '40': '機工部',
    '59': '中工中心',
    '92': '南工中心',
}


def parse_search_query(query):
    """
    Parse search query for special operators.
    
    Supported operators:
    - title:關鍵字 - Search only in title field
    - ext:pdf - Search by file extension (e.g., ext:pdf, ext:docx)
    - proj:0001b - Search by project number (5 chars after sinoproject-)
    - dept:11 - Search by department number (2 chars after sinoproject-dept_)
    
    Returns:
        dict with keys: 'query' (remaining query), 'title', 'ext', 'proj', 'dept'
    """
    import re
    
    result = {
        'query': '',
        'title': None,
        'ext': None,
        'proj': None,
        'dept': None,
    }
    
    if not query:
        return result
    
    query = query.strip()
    
    # Extract title: operator
    title_match = re.search(r'title:(\S+)', query, re.IGNORECASE)
    if title_match:
        result['title'] = title_match.group(1)
        query = query.replace(title_match.group(0), '').strip()
    
    # Extract ext: operator
    ext_match = re.search(r'ext:(\S+)', query, re.IGNORECASE)
    if ext_match:
        result['ext'] = ext_match.group(1)
        query = query.replace(ext_match.group(0), '').strip()
    
    # Extract proj: operator (project number)
    proj_match = re.search(r'proj:(\S+)', query, re.IGNORECASE)
    if proj_match:
        result['proj'] = proj_match.group(1).lower()
        query = query.replace(proj_match.group(0), '').strip()
    
    # Extract dept: operator (department number)
    dept_match = re.search(r'dept:(\d{1,2})', query, re.IGNORECASE)
    if dept_match:
        # Pad to 2 digits if needed
        dept_code = dept_match.group(1).zfill(2)
        result['dept'] = dept_code
        query = query.replace(dept_match.group(0), '').strip()
    
    result['query'] = query
    return result


def search(query, indices="*", size=20, from_=0, sort_by=None, date_from=None, date_to=None, include_content=False):
    """
    Execute search query against OpenSearch
    
    Args:
        query: Search query string
        indices: Index pattern to search (default: all)
        size: Number of results to return
        from_: Offset for pagination
        sort_by: Sort field and order (e.g., "dt:desc")
        date_from: Filter by date from (ISO format)
        date_to: Filter by date to (ISO format)
        include_content: Whether to search inside full-text content (slower)
    
    Returns:
        Search response with hits
    
    Note:
        Only indices with alias_ or reviewing_ prefix are searchable.
        - alias_* = online, normal display
        - reviewing_* = online but ALL results are treated as secret/sensitive
        The indices parameter is automatically converted to alias pattern.
        e.g., "sinoproject*" searches both "alias_sinoproject*" and "reviewing_sinoproject*"
    """
    client = get_client()
    
    # Convert index pattern to alias patterns (only search online indices)
    # Indices without alias_ or reviewing_ prefix are considered offline
    if indices == "*":
        # Search both alias_ and reviewing_ prefixed indices
        search_indices = "alias_*,reviewing_*"
    else:
        # Handle comma-separated patterns
        parts = [p.strip() for p in indices.split(',')]
        alias_parts = []
        for part in parts:
            if part.startswith('alias_') or part.startswith('reviewing_'):
                alias_parts.append(part)
            else:
                # Add both alias_ and reviewing_ versions
                alias_parts.append(f'alias_{part}')
                alias_parts.append(f'reviewing_{part}')
        search_indices = ','.join(alias_parts)
    
    # Parse special search operators from query
    # Supported operators:
    # - title:關鍵字 - Search only in title field
    # - ext:pdf - Search by file extension
    # - proj:0001b - Search by project number (5 chars after sinoproject-)
    # - dept:11 - Search by department number (2 chars after sinoproject-dept_)
    parsed = parse_search_query(query)
    
    # Build query based on parsed operators
    must_clauses = []
    filter_clauses = []
    
    # Handle project number filter
    if parsed.get('proj'):
        proj_code = parsed['proj'].lower()
        # Project pattern: sinoproject-XXXXX where XXXXX is the 5-char code
        filter_clauses.append({
            "wildcard": {"_index": f"*sinoproject-{proj_code}*"}
        })
    
    # Handle department filter
    if parsed.get('dept'):
        dept_code = parsed['dept']
        # Department pattern: sinoproject-dept_XX where XX is the 2-char code
        filter_clauses.append({
            "wildcard": {"_index": f"*sinoproject-dept_{dept_code}*"}
        })
    
    # Handle file extension filter
    if parsed.get('ext'):
        ext = parsed['ext'].lower()
        if not ext.startswith('.'):
            ext = f'.{ext}'
        filter_clauses.append({
            "bool": {
                "should": [
                    {"wildcard": {"file.filename": f"*{ext}"}},
                    {"wildcard": {"path.real": f"*{ext}"}},
                    {"wildcard": {"file": f"*{ext}"}}
                ],
                "minimum_should_match": 1
            }
        })
    
    # Build main query
    main_query = parsed.get('query', '').strip()
    
    if parsed.get('title'):
        # Title-only search
        title_terms = parsed['title']
        must_clauses.append({
            "match_phrase": {
                "title": title_terms
            }
        })
    
    if main_query:
        terms = main_query.split()
        
        if len(terms) == 1:
            # Single term - use best_fields for faster query
            search_fields = ["title^3", "file.filename^2", "path.real^2", "meta", "file.extension"]
            if include_content:
                search_fields.append("content^1")
            
            must_clauses.append({
                "multi_match": {
                    "query": main_query,
                    "fields": search_fields,
                    "type": "best_fields",
                    "tie_breaker": 0.3
                }
            })
        else:
            # Multiple terms: use bool should for OR matching
            should_clauses = []
            search_fields = ["title^3", "file.filename^2", "path.real^2", "meta", "file.extension"]
            if include_content:
                search_fields.append("content^1")
                
            for term in terms:
                should_clauses.append({
                    "multi_match": {
                        "query": term,
                        "fields": search_fields,
                        "type": "best_fields",
                        "tie_breaker": 0.3
                    }
                })
            must_clauses.append({
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            })
    
    # Combine into final must_query
    if must_clauses:
        if len(must_clauses) == 1:
            must_query = must_clauses[0]
        else:
            must_query = {"bool": {"must": must_clauses}}
    else:
        must_query = {"match_all": {}}
    
    # Build filter for date range and special operators
    filters = filter_clauses.copy()  # Include proj/dept/ext filters
    if date_from or date_to:
        date_filter = {"range": {"dt": {}}}
        if date_from:
            date_filter["range"]["dt"]["gte"] = date_from
        if date_to:
            date_filter["range"]["dt"]["lte"] = date_to
        filters.append(date_filter)
    
    # Construct body with performance optimizations
    body = {
        "query": {
            "bool": {
                "must": must_query,
                "filter": filters
            }
        },
        # Limit _source to essential fields only (exclude large content field unless requested)
        "_source": {
            "excludes": ["content"] if not include_content else []
        },
        # Optimized highlight - skip content field unless requested
        "highlight": {
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
            "fields": {
                "title": {"number_of_fragments": 0},
                "file": {"number_of_fragments": 0},
                "path": {"number_of_fragments": 0}
            }
        },
        "size": size,
        "from": from_,
        "terminate_after": 5000  # Performance: Stop after finding enough candidates
    }
    
    # Add sort
    if sort_by:
        field, order = sort_by.split(':') if ':' in sort_by else (sort_by, 'desc')
        body["sort"] = [{field: {"order": order, "unmapped_type": "date"}}]
    
    try:
        response = client.search(
            index=search_indices,
            body=body,
            ignore_unavailable=True,
            request_timeout=getattr(settings, 'OPENSEARCH_TIMEOUT', 30)
        )
        return response
    except Exception as e:
        return {"error": str(e), "hits": {"hits": [], "total": {"value": 0}}}


def search_fast(query, indices="*", size=10):
    """
    Ultra-fast search for instant results (autocomplete, suggestions).
    
    Optimizations:
    - No highlight
    - Minimal _source fields
    - terminate_after for early termination
    - Shorter timeout
    
    Args:
        query: Search query string
        indices: Index pattern to search
        size: Number of results (default: 10)
    
    Returns:
        Search response with minimal hits
    """
    client = get_client()
    
    # Convert to alias patterns
    if indices == "*":
        search_indices = "alias_*,reviewing_*"
    else:
        parts = [p.strip() for p in indices.split(',')]
        alias_parts = []
        for part in parts:
            if part.startswith('alias_') or part.startswith('reviewing_'):
                alias_parts.append(part)
            else:
                alias_parts.append(f'alias_{part}')
                alias_parts.append(f'reviewing_{part}')
        search_indices = ','.join(alias_parts)
    
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "file.filename^2", "path.real"],
                "type": "best_fields",
                "tie_breaker": 0.3
            }
        },
        "_source": ["title", "file.filename", "path.real", "dt", "_index"],
        "size": size,
        "terminate_after": size * 10  # Stop after finding enough candidates
    }
    
    try:
        response = client.search(
            index=search_indices,
            body=body,
            ignore_unavailable=True,
            request_timeout=5  # Very short timeout for fast search
        )
        return response
    except Exception as e:
        return {"error": str(e), "hits": {"hits": [], "total": {"value": 0}}}


def get_category_from_index(index_name):
    """Determine category from index name"""
    # Order matters - more specific patterns first
    patterns = [
        ('sinobook_journal', 'book_journal'),
        ('sinoproject-dept', 'dept_file'),
        ('sinoproject-early', 'early_file'),
        ('sinopmis_meeting', 'pmis_meeting'),
        ('sinopmis_file', 'pmis_file'),
        ('sinopmis_iobook_in', 'pmis_iobook_in'),
        ('sinopmis_iobook_out', 'pmis_iobook_out'),
        ('sinobim_element', 'bim_element'),
        ('sinobim_issue', 'bim_issue'),
        ('sinobim_file', 'bim_file'),
        ('sino_website_in', 'website_insite'),
        ('sino_website_out', 'website_outsite'),
        ('sino_website_user', 'website_user'),
        ('sino_website_prkms', 'website_prkms'),
        ('sino_map_dept', 'map_dept'),
        ('sino_map_tw_1', 'map_tw_1'),
        ('sino_map_tw_2', 'map_tw_2'),
        ('sinobook', 'book'),
        ('sino_map', 'map'),
        ('sinoqa', 'qa'),
        ('sino_kmv1', 'kmv1'),
        ('sino_kmv2', 'kmv2'),
        ('sino_drawing', 'drawing'),
        ('sino_carbon', 'carbon'),
        ('sino_prkms', 'prkms_tender'),
        ('sino_budget', 'spec_budget'),
        ('sino_spec', 'spec'),
        ('sino_cns', 'cns'),
        ('sinoproject', 'file'),
        ('sinoeng', 'eng_file'),
    ]
    
    for pattern, template in patterns:
        if pattern in index_name:
            return template
    
    return 'default'


def get_aggregations(query, indices="*"):
    """Get aggregations for search filters"""
    client = get_client()
    
    body = {
        "size": 0,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["*"]
            }
        } if query else {"match_all": {}},
        "aggs": {
            "by_index": {
                "terms": {
                    "field": "_index",
                    "size": 50
                }
            }
        }
    }
    
    try:
        response = client.search(
            index=indices,
            body=body,
            ignore_unavailable=True
        )
        return response.get('aggregations', {})
    except Exception:
        return {}
