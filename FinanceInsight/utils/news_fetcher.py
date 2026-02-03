import feedparser
from django.conf import settings
from django.utils import timezone
from django.db import IntegrityError
from datetime import datetime, timedelta
from FinanceInsight.models import NewsCategory, FinancialNews, DailyNewsSummary
import time
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from difflib import SequenceMatcher
import re
import ssl
import os
import urllib3
from NewsSubscriber.oss import ask_oss

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Keyword configuration for categories
CATEGORY_KEYWORDS = {
    'TW_FINANCE': ['台灣股市', '台積電', '金管會', '外資買賣超', '台股指數'],
    'US_FINANCE': ['美股', 'Fed', 'NASDAQ', '道瓊工業指數', '標普500'],
    'INDUSTRY': ['半導體產業', 'AI供應鏈', '電動車趨勢', '綠能產業'],
    'GLOBAL': ['全球經濟', '匯率走勢', '原油價格', '歐洲央行', '日本央行'],
}

def fetch_and_summarize_news():
    """Main entry point to fetch news for all categories and generate summaries."""
    results = {}
    
    for code, keywords in CATEGORY_KEYWORDS.items():
        try:
            category = NewsCategory.objects.get(code=code)
            print(f"Fetching news for category: {category.name}")
            
            # Fetch news
            all_news = []
            for keyword in keywords:
                items = _fetch_google_news(keyword, category)
                all_news.extend(items)
                time.sleep(1)
            
            # Deduplicate
            unique_news = _deduplicate_news(all_news)
            
            if unique_news:
                # Save to DB
                saved_news = _save_news(unique_news, category)
                
                # Generate Summary
                _generate_daily_summary(saved_news, category)
                
                results[code] = len(saved_news)
            else:
                results[code] = 0
                
        except NewsCategory.DoesNotExist:
            print(f"Category {code} not found, skipping.")
            continue
        except Exception as e:
            print(f"Error processing {code}: {e}")
            continue
            
    return results

def _fetch_google_news(keyword, category):
    try:
        query = quote(keyword)
        rss_url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(rss_url)
        
        items = []
        for entry in feed.entries:
            try:
                title = entry.title.strip()
                if 'MSN' in title: continue
                
                pub_date = _parse_date(entry)
                source = _extract_source(entry)
                
                items.append({
                    'title': title,
                    'url': entry.link.strip(),
                    'published_at': pub_date,
                    'source': source,
                    'content': entry.get('summary', ''),
                    'category': category
                })
            except Exception:
                continue
        return items
    except Exception:
        return []

def _parse_date(entry):
    try:
        if hasattr(entry, 'published'):
            return parsedate_to_datetime(entry.published)
    except:
        pass
    return timezone.now()

def _extract_source(entry):
    if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
        return entry.source.title
    title = entry.get('title', '')
    if ' - ' in title:
        return title.rsplit(' - ', 1)[1].strip()
    return "Google News"

def _deduplicate_news(news_list):
    if not news_list: return []
    unique = []
    seen_urls = set()
    seen_titles = []
    
    for news in news_list:
        if news['url'] in seen_urls: continue
        
        is_dup = False
        for t in seen_titles:
            if SequenceMatcher(None, news['title'], t).ratio() > 0.85:
                is_dup = True
                break
        
        if not is_dup:
            unique.append(news)
            seen_urls.add(news['url'])
            seen_titles.append(news['title'])
    return unique

def _save_news(news_list, category):
    saved = []
    # Only keep latest 20 items per category per run to avoid spam
    for news in news_list[:20]:
        try:
            # Check if URL exists (simple check)
            if not FinancialNews.objects.filter(source_url=news['url']).exists():
                obj = FinancialNews.objects.create(
                    category=category,
                    title=news['title'],
                    source=news['source'],
                    source_url=news['url'],
                    content=news['content'],
                    published_at=news['published_at']
                )
                saved.append(obj)
        except Exception as e:
            print(f"Error saving news: {e}")
            continue
    return saved

def _generate_daily_summary(news_objs, category):
    today = timezone.now().date()
    
    # Check if summary exists for today
    if DailyNewsSummary.objects.filter(category=category, date=today).exists():
        print(f"Summary for {category.name} today already exists.")
        return

    if not news_objs:
        return

    # Prepare text for AI
    titles_text = "\n".join([f"{i+1}. {n.title} (來源: {n.source})" for i, n in enumerate(news_objs)])
    
    prompt = f"""請擔任專業財經分析師，根據以下「{category.name}」今日新聞，生成摘要與總結。

【輸入新聞】
{titles_text}

【輸出要求】
1. 摘要：整合今日重要新聞內容，約 100-150 字。
2. 總結：分析市場趨勢或重要影響，給予簡短評論或觀察，約 50-100 字。
3. 輸出格式：請直接輸出兩段文字，第一段為摘要，第二段為總結，中間用 "|||" 分隔。
"""

    try:
        response = ask_oss(prompt, tag='財經摘要')
        content = response.content.strip()
        
        if "|||" in content:
            summary, conclusion = content.split("|||", 1)
        else:
            # Fallback if AI didn't follow format
            summary = content
            conclusion = "（AI 未能生成明確總結）"

        DailyNewsSummary.objects.create(
            category=category,
            date=today,
            summary=summary.strip(),
            conclusion=conclusion.strip(),
            news_count=len(news_objs)
        )
        print(f"Generated summary for {category.name}")
        
    except Exception as e:
        print(f"AI summary failed: {e}")
