import feedparser
from django.conf import settings
from django.utils import timezone
from django.db import IntegrityError
from datetime import datetime, timedelta
from NewsSubscriber.models import Topic, NewsItem, DailySummary
import time
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from difflib import SequenceMatcher
import requests
from bs4 import BeautifulSoup
from NewsSubscriber.oss import ask_oss
import urllib3
import ssl
import os
import re

# 禁用SSL警告（企業環境中使用自簽證書）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局禁用SSL驗證
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''


def fetch_news_for_topic(topic):
    """為特定主題擷取新聞"""
    try:
        keywords = topic.keywords.all()
        if not keywords.exists():
            return {
                'success': False,
                'message': f'主題「{topic.name}」沒有關鍵字',
                'news_count': 0
            }

        # 收集新聞
        all_news = []

        # 從Google News收集新聞
        for keyword in keywords:
            news_items = _fetch_google_news(keyword.word, topic)
            all_news.extend(news_items)
            time.sleep(1)  # 避免請求過快

        # 去重
        unique_news = _deduplicate_news(all_news, topic)

        if not unique_news:
            return {
                'success': False,
                'message': '沒有收集到新聞',
                'news_count': 0
            }

        # 儲存新聞
        saved_news = _save_news(unique_news, topic)

        # 生成每日摘要
        today = timezone.now().date()
        if saved_news and not DailySummary.objects.filter(topic=topic, date=today).exists():
            daily_summary_html = _generate_daily_summary(saved_news, topic)

            if daily_summary_html:
                try:
                    DailySummary.objects.create(
                        topic=topic,
                        summary=daily_summary_html,
                        date=today,
                        news_count=len(saved_news)
                    )
                except IntegrityError:
                    pass  # 今天已有摘要

        return {
            'success': True,
            'message': '新聞擷取成功',
            'news_count': len(saved_news)
        }

    except Exception as e:
        return {
            'success': False,
            'message': str(e),
            'news_count': 0
        }


def _fetch_google_news(keyword, topic):
    """從Google News抓取新聞"""
    try:
        query = quote(keyword)
        rss_url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

        feed = feedparser.parse(rss_url)

        news_items = []
        for entry in feed.entries:
            try:
                title = entry.title.strip()

                # 過濾掉MSN的新聞
                if 'MSN' in title:
                    continue

                # 解析日期
                published_date = _parse_date(entry)
                if not published_date:
                    continue

                # 提取來源
                source = _extract_source(entry)

                news_items.append({
                    'title': title,
                    'url': entry.link.strip(),
                    'date': published_date,
                    'source': source,
                    'topic': topic
                })
            except Exception:
                continue

        return news_items

    except Exception:
        return []


def _parse_date(entry):
    """解析發布日期"""
    try:
        if hasattr(entry, 'published'):
            return parsedate_to_datetime(entry.published)
    except Exception:
        pass

    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            import calendar
            timestamp = calendar.timegm(entry.published_parsed)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except Exception:
        pass

    return timezone.now()


def _extract_source(entry):
    """從entry中提取新聞來源"""
    title = entry.get('title', '')
    if ' - ' in title:
        parts = title.rsplit(' - ', 1)
        if len(parts) == 2:
            return parts[1].strip()

    if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
        return entry.source.title

    return "Google News"


def _deduplicate_news(news_list, topic):
    """去除重複的新聞"""
    if not news_list:
        return []

    unique_news = []
    seen_urls = set()
    seen_titles = []

    for news in news_list:
        # 檢查URL是否重複
        if news['url'] in seen_urls:
            continue

        # 檢查標題相似度
        is_duplicate = False
        for seen_title in seen_titles:
            similarity = SequenceMatcher(None, news['title'], seen_title).ratio()
            if similarity > 0.85:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_news.append(news)
            seen_urls.add(news['url'])
            seen_titles.append(news['title'])

    return unique_news


def _save_news(news_list, topic):
    """儲存新聞"""
    saved_news = []

    for news in news_list:
        try:
            # 檢查是否已存在
            if NewsItem.objects.filter(url=news['url']).exists():
                news_item = NewsItem.objects.get(url=news['url'])
            else:
                # 建立新新聞記錄
                news_item = NewsItem.objects.create(
                    topic=topic,
                    title=news['title'],
                    date=news['date'],
                    url=news['url'],
                    source=news['source'],
                    content="",
                    summary=""
                )

            # 加入列表供每日摘要使用
            saved_news.append({
                'title': news['title'],
                'url': news['url'],
                'source': news['source'],
                'date': news['date']
            })

        except Exception:
            continue

    return saved_news


def _generate_daily_summary(news_list, topic):
    """基於新聞標題生成每日整合摘要"""
    try:
        # 準備新聞標題資料
        news_titles = []
        for i, news in enumerate(news_list, 1):
            news_titles.append(f"{i}. 【{news['source']}】{news['title']}")
            news_titles.append(f"   時間: {news['date'].strftime('%Y-%m-%d %H:%M')}")
            news_titles.append(f"   連結: {news['url']}")
            news_titles.append("")

        titles_text = "\n".join(news_titles)

        # 建立提示詞
        prompt = f"""你是一位專業的新聞分析師。請根據以下「{topic.name}」主題的新聞標題，生成一份今日新聞整合報告。

【嚴格限制 - 必須遵守】
1. 只能使用下方提供的新聞標題
2. 絕對不可以添加、編造或引用任何未提供的新聞
3. 所有新聞連結必須完全使用下方提供的URL，不可修改
4. 不可以生成任何額外的新聞項目
5. 每則新聞只有標題，請根據標題內容提供簡短說明（1-2句話）

【輸出格式要求】
1. 使用繁體中文
2. 使用 HTML 格式（不需要<!DOCTYPE>、<html>、<body>等標籤）
3. 包含兩個部分：

第一部分 - 今日重點：
- 用 <h2> 標題「今日重點」
- 根據新聞標題，用 <ul><li> 格式條列3-5個重要趨勢或發展
- 這部分不包含連結，只是重點摘述

第二部分 - 重要新聞：
- 用 <h2> 標題「重要新聞」
- 依序列出下方提供的所有新聞標題
- 每則新聞使用以下HTML結構：
  <div style="margin-bottom: 20px; padding: 15px; border-left: 3px solid #3498db; background-color: #f8f9fa;">
    <h3 style="margin: 0 0 10px 0;">
      <a href="[使用下方提供的完整URL]" target="_blank" style="color: #2980b9; text-decoration: none;">[新聞標題]</a>
    </h3>
    <p style="margin: 5px 0; color: #7f8c8d; font-size: 0.9em;">來源：[來源] | 時間：[時間]</p>
    <p style="margin: 10px 0 0 0;">[根據標題內容提供1-2句話的簡短說明]</p>
  </div>

【今日新聞資料 - 共{len(news_list)}則】
{titles_text}

請嚴格按照上述要求生成HTML內容：
"""

        response = ask_oss(prompt, tag='每日摘要')
        summary = response.content.strip()

        # 移除可能的markdown代碼塊標記
        summary = re.sub(r'^```html\n', '', summary)
        summary = re.sub(r'\n```$', '', summary)
        summary = re.sub(r'^```\n', '', summary)
        summary = re.sub(r'\n```$', '', summary)

        return summary

    except Exception:
        return None
