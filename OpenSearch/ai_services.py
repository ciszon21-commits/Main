"""
AI-Powered Search Services
Combines OpenSearch with OSS for intelligent question answering
"""
import requests
import logging
import urllib3
from django.conf import settings
from django.utils.timezone import make_aware
from datetime import datetime
from . import services

# Suppress SSL warnings for internal API calls
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# OSS API Configuration
OSS_API_URL = "https://50-129.sinotech.com.tw:777/api/v1/workspace/openai/chat"


def _call_oss_api(prompt: str, user_name: str = "system") -> dict:
    """
    Internal function to call OSS API.
    
    Args:
        prompt: The prompt to send to OSS
        user_name: User name for tracking
        
    Returns:
        dict with 'success', 'content', 'metrics', 'error' keys
    """
    headers = {
        "Authorization": f"Bearer {settings.ANYTHINGLLM_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "mode": "chat",
        "message": prompt,
        "user": user_name,
    }
    
    try:
        response = requests.post(
            OSS_API_URL, 
            headers=headers, 
            json=data, 
            timeout=60,
            verify=False  # For internal SSL
        )
        
        if response.status_code != 200:
            logger.error(f"OSS API error: status {response.status_code}")
            return {
                'success': False,
                'content': '',
                'metrics': {},
                'error': f"API returned status {response.status_code}"
            }
        
        result = response.json()
        return {
            'success': True,
            'content': result.get('textResponse', ''),
            'metrics': result.get('metrics', {}),
            'request_id': result.get('id', 'unknown'),
            'error': None
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"OSS API request failed: {e}")
        return {
            'success': False,
            'content': '',
            'metrics': {},
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error calling OSS API: {e}")
        return {
            'success': False,
            'content': '',
            'metrics': {},
            'error': str(e)
        }


def _build_keyword_prompt(question: str, attempt: int = 1) -> str:
    """
    Build prompt for keyword extraction based on attempt number.
    
    Args:
        question: User's question
        attempt: Retry attempt number (1-3)
        
    Returns:
        Formatted prompt string
    """
    question = (question or "").strip()
    if not question:
        return ""
    
    if attempt == 1:
        # First attempt: Extract 3-4 core keywords
        strategy = """
**策略：首次提取**
- 3-4個核心關鍵字
- 關鍵字長度應盡量縮短
- 按搜尋價值排序"""
    elif attempt == 2:
        # Second attempt: Broader, 2-3 keywords
        strategy = """
**策略：放寬搜尋**
- 2-3個更通用的關鍵字
- 使用上層概念或同義詞
- 移除過於具體的限定詞"""
    else:
        # Third attempt: Most essential 1-2 keywords
        strategy = """
**策略：最寬鬆搜尋**
- 只保留1-2個最核心的名詞
- 使用最通用的術語
- 完全移除形容詞和限定詞"""
    
    return f"""作為搜尋專家，請分析以下問題並提取最有效的搜尋關鍵字：

{strategy}

**分析要點：**
- 識別討論的主要話題和子話題
- 提取專業術語、品牌名稱、型號等
- 保留時間、地點等限定條件
- 考慮搜尋意圖（資訊型、交易型、導航型）

**輸出要求：**
- 使用空白隔開，不要有雙引號
- 移除輔助文字，例如什麼、是誰、名稱這類不會出現在搜尋內容中的文字
- 移除指定中興公司的文字，因為所有資料都是中興公司的資料
- 主要使用繁體中文

**問題內容：**
{question}

**輸出格式：只輸出關鍵字，不需要其他說明**"""


def extract_keywords(question: str, attempt: int = 1, user_name: str = "system") -> dict:
    """
    Extract search keywords from a question using AI.
    
    Args:
        question: User's question
        attempt: Retry attempt number (1-3)
        user_name: User name for tracking
        
    Returns:
        dict with 'success', 'keywords', 'error' keys
    """
    prompt = _build_keyword_prompt(question, attempt)
    if not prompt:
        return {'success': False, 'keywords': '', 'error': 'Empty question'}
    
    result = _call_oss_api(prompt, user_name)
    
    if result['success']:
        # Clean up the keywords response
        keywords = result['content'].strip()
        # Remove quotes and extra formatting
        keywords = keywords.replace('"', '').replace("'", '')
        # Limit to reasonable length
        keywords = ' '.join(keywords.split()[:10])
        
        return {
            'success': True,
            'keywords': keywords,
            'metrics': result['metrics'],
            'error': None
        }
    
    return {
        'success': False,
        'keywords': '',
        'error': result['error']
    }


def search_with_keywords(keywords: str, indices: str = "*", size: int = 10) -> dict:
    """
    Search OpenSearch using extracted keywords.
    
    Args:
        keywords: Space-separated keywords
        indices: Index pattern to search
        size: Number of results to return
        
    Returns:
        dict with 'success', 'results', 'total', 'error' keys
    """
    if not keywords:
        return {'success': False, 'results': [], 'total': 0, 'error': 'No keywords'}
    
    try:
        response = services.search(
            query=keywords,
            indices=indices,
            size=size,
            include_content=True  # Include content for context building
        )
        
        if 'error' in response:
            return {
                'success': False,
                'results': [],
                'total': 0,
                'error': response['error']
            }
        
        hits = response.get('hits', {})
        total = hits.get('total', {})
        if isinstance(total, dict):
            total_value = total.get('value', 0)
        else:
            total_value = total
        
        results = []
        for hit in hits.get('hits', []):
            source = hit.get('_source', {})
            results.append({
                'index': hit.get('_index', ''),
                'id': hit.get('_id', ''),
                'score': hit.get('_score', 0),
                'title': source.get('title', ''),
                'content': source.get('content', '')[:2000],  # Limit content length
                'path': source.get('path', {}).get('real', '') if isinstance(source.get('path'), dict) else source.get('path', ''),
                'dt': source.get('dt', ''),
                'poster': source.get('poster', ''),
                'url': source.get('url', ''),
            })
        
        return {
            'success': True,
            'results': results,
            'total': total_value,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            'success': False,
            'results': [],
            'total': 0,
            'error': str(e)
        }


def build_context(search_results: list, max_docs: int = 5) -> str:
    """
    Build context string from search results for AI.
    
    Args:
        search_results: List of search result dicts
        max_docs: Maximum number of documents to include
        
    Returns:
        Formatted context string
    """
    if not search_results:
        return ""
    
    context_parts = []
    for i, result in enumerate(search_results[:max_docs], 1):
        title = result.get('title', '無標題')
        content = result.get('content', '')[:1000]  # Limit each doc
        path = result.get('path', '')
        poster = result.get('poster', '')
        dt = result.get('dt', '')
        
        doc_context = f"""### 文檔 {i}: {title}
- **來源**: {path}
- **作者**: {poster}
- **日期**: {dt}
- **內容摘要**: {content}
"""
        context_parts.append(doc_context)
    
    return "\n".join(context_parts)


def _build_answer_prompt(question: str, context: str) -> str:
    """
    Build prompt for AI answer generation.
    
    Args:
        question: User's original question
        context: Search results context
        
    Returns:
        Formatted prompt string
    """
    question = (question or "").strip()
    context = (context or "").strip()
    
    if context:
        return f"""基於以下搜尋結果回答問題，請以 Markdown 格式回應，包含適當的標題、表格、清單等格式：

**搜尋問題**：{question}

**相關文檔**（按相關性排序，僅為中興公司內部蒐集的資料，前幾筆資料綜整）：
---
{context}
---

請以 Markdown 格式提供完整分析，包含：
1. **摘要回答** - 直接回答問題的核心內容
2. **詳細說明** - 基於搜尋結果的詳細分析
3. **參考來源** - 以表格形式列出引用的文檔來源
4. **信心程度** - 評估答案的可信度（高/中/低）

格式要求：
- 使用適當的 Markdown 標題（#, ##, ###）
- 重要內容使用**粗體**或*斜體*強調
- 清單使用 - 或數字編號
- 如有數據，請使用表格格式 | 欄位 | 內容 |
- 程式碼或專業術語使用 `程式碼` 格式"""
    
    # No context available - answer based on question alone
    return f"""無法從資料庫中找到與問題直接相關的文檔。請根據您的知識嘗試回答以下問題，並明確說明這是基於一般知識而非公司內部資料：

**問題**：{question}

請以 Markdown 格式回應，並在開頭加上提示說明未找到相關內部文檔。"""


def generate_answer(question: str, context: str, user_name: str = "system") -> dict:
    """
    Generate AI answer based on question and search context.
    
    Args:
        question: User's original question
        context: Search results context
        user_name: User name for tracking
        
    Returns:
        dict with 'success', 'answer', 'metrics', 'error' keys
    """
    prompt = _build_answer_prompt(question, context)
    result = _call_oss_api(prompt, user_name)
    
    if result['success']:
        return {
            'success': True,
            'answer': result['content'],
            'metrics': result['metrics'],
            'request_id': result.get('request_id', 'unknown'),
            'error': None
        }
    
    return {
        'success': False,
        'answer': '',
        'metrics': {},
        'error': result['error']
    }


def ask_ai(question: str, user, indices: str = "*", max_retries: int = 3) -> dict:
    """
    Main entry point: Question → Keywords → Search → Answer
    
    This function orchestrates the entire AI-powered search flow:
    1. Extract keywords from the question using AI
    2. Search OpenSearch with the keywords
    3. If no results, retry with adjusted keywords (up to max_retries times)
    4. Build context from search results
    5. Generate AI answer based on context
    
    Args:
        question: User's question
        user: Django User object
        indices: Index pattern to search (default: all)
        max_retries: Maximum keyword extraction retries (default: 3)
        
    Returns:
        dict with:
        - success: bool
        - answer: str (Markdown formatted)
        - keywords_used: str
        - search_count: int
        - retry_count: int
        - sources: list of source dicts
        - metrics: dict with token usage
        - error: str or None
    """
    user_name = getattr(user, 'username', 'anonymous')
    if hasattr(user, 'profile') and hasattr(user.profile, 'emp_name'):
        user_name = user.profile.emp_name
    
    keywords_used = ""
    search_results = []
    retry_count = 0
    total_metrics = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    
    # Step 1 & 2: Extract keywords and search with retry logic
    for attempt in range(1, max_retries + 1):
        retry_count = attempt - 1
        
        # Extract keywords
        keyword_result = extract_keywords(question, attempt, user_name)
        if not keyword_result['success']:
            logger.warning(f"Keyword extraction failed on attempt {attempt}: {keyword_result['error']}")
            continue
        
        keywords_used = keyword_result['keywords']
        logger.info(f"Attempt {attempt}: Keywords = '{keywords_used}'")
        
        # Accumulate metrics
        if keyword_result.get('metrics'):
            for key in total_metrics:
                total_metrics[key] += keyword_result['metrics'].get(key, 0)
        
        # Search with keywords
        search_result = search_with_keywords(keywords_used, indices, size=100)
        
        if search_result['success'] and search_result['total'] > 0:
            search_results = search_result['results']
            logger.info(f"Found {search_result['total']} results on attempt {attempt}")
            break
        
        logger.info(f"No results on attempt {attempt}, retrying with adjusted keywords...")
    
    # Step 3: Build context from search results
    context = build_context(search_results, max_docs=20)
    
    # Step 4: Generate answer
    answer_result = generate_answer(question, context, user_name)
    
    if answer_result.get('metrics'):
        for key in total_metrics:
            total_metrics[key] += answer_result['metrics'].get(key, 0)
    
    # Build source list for response
    sources = []
    for result in search_results[:100]:
        sources.append({
            'id': result.get('id', ''),
            'title': result.get('title', ''),
            'path': result.get('path', ''),
            'index': result.get('index', ''),
            'score': result.get('score', 0),
            'content': result.get('content', '')[:200],  # Short snippet for preview
            'dt': result.get('dt', ''),
            'poster': result.get('poster', ''),
            'url': result.get('url', ''),
        })
    
    if answer_result['success']:
        return {
            'success': True,
            'answer': answer_result['answer'],
            'keywords_used': keywords_used,
            'search_count': len(search_results),
            'retry_count': retry_count,
            'sources': sources,
            'metrics': total_metrics,
            'error': None
        }
    
    return {
        'success': False,
        'answer': f"抱歉，無法生成回答。錯誤：{answer_result['error']}",
        'keywords_used': keywords_used,
        'search_count': len(search_results),
        'retry_count': retry_count,
        'sources': sources,
        'metrics': total_metrics,
        'error': answer_result['error']
    }
