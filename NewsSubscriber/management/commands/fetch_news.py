import feedparser
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.db import IntegrityError
from datetime import datetime, timedelta
from NewsSubscriber.models import Topic, NewsItem, DailySummary, Subscription
import time
from email.utils import parsedate_to_datetime
from urllib.parse import quote
import re
from difflib import SequenceMatcher
import requests
from bs4 import BeautifulSoup
from NewsSubscriber.oss import ask_oss
import urllib3
import ssl
import os

# 禁用SSL警告（企業環境中使用自簽證書）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局禁用SSL驗證（適用於feedparser等套件）
# 注意：這會影響整個Python進程，僅用於企業內網環境
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# 設置環境變數以禁用SSL驗證
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

class Command(BaseCommand):
    help = 'Fetch news from Google News RSS and generate summaries using Gemini'

    def __init__(self):
        super().__init__()
        self.cutoff_time = timezone.now() - timedelta(hours=24)

    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write("新聞訂閱系統 - 資料抓取與摘要")
        self.stdout.write("="*60)
        self.stdout.write(f"開始時間: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Configure Gemini
        if not settings.GEMINI_API_KEY:
            self.stderr.write("Error: GEMINI_API_KEY is not set in settings.")
            return

        topics = Topic.objects.all()
        if not topics.exists():
            self.stdout.write("沒有任何主題，結束程式。")
            return

        today = timezone.now().date()

        for topic in topics:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"處理主題: {topic.name}")
            self.stdout.write(f"{'='*60}")

            # 檢查今天是否已有摘要
            if DailySummary.objects.filter(topic=topic, date=today).exists():
                self.stdout.write(f"  ⚠ 今天已有摘要，跳過此主題")
                continue

            keywords = topic.keywords.all()
            if not keywords.exists():
                self.stdout.write(f"  主題「{topic.name}」沒有關鍵字，跳過。")
                continue

            # 收集新聞
            all_news = []

            # 從Google News收集新聞
            for keyword in keywords:
                self.stdout.write(f"\n【步驟 1】搜尋關鍵字: {keyword.word}")
                news_items = self._fetch_google_news(keyword.word, topic)
                all_news.extend(news_items)
                time.sleep(1)  # 避免請求過快

            # 去重
            self.stdout.write(f"\n【步驟 2】去除重複新聞...")
            self.stdout.write(f"  合併前數量: {len(all_news)}")
            unique_news = self._deduplicate_news(all_news, topic)
            self.stdout.write(f"  去重後數量: {len(unique_news)}")

            if not unique_news:
                self.stdout.write(f"  沒有收集到新聞，跳過此主題")
                continue

            # 儲存新聞（只保存標題）
            self.stdout.write(f"\n【步驟 3】儲存新聞...")
            saved_news = self._save_and_fetch_content(unique_news, topic)
            self.stdout.write(f"  成功儲存 {len(saved_news)} 則新聞")

            # 基於新聞標題生成每日整合摘要
            if saved_news:
                self.stdout.write(f"\n【步驟 4】生成每日整合摘要（基於新聞標題）...")
                daily_summary_html = self._generate_daily_summary(saved_news, topic)

                if daily_summary_html:
                    # 儲存摘要
                    try:
                        daily_summary = DailySummary.objects.create(
                            topic=topic,
                            summary=daily_summary_html,
                            date=today,
                            news_count=len(saved_news)
                        )
                        self.stdout.write(f"  ✅ 每日摘要已生成並儲存")

                        # 發送郵件給訂閱者
                        self.stdout.write(f"\n【步驟 5】發送郵件給訂閱者...")
                        self._send_emails(topic, daily_summary_html, saved_news)
                    except IntegrityError:
                        self.stdout.write(f"  ⚠ 今天已有摘要（併發寫入），跳過")
                else:
                    self.stdout.write(f"  ⚠ 每日摘要生成失敗")

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"完成時間: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"{'='*60}")

    def _fetch_google_news(self, keyword, topic):
        """從Google News抓取新聞"""
        try:
            query = quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

            self.stdout.write(f"  抓取 RSS: {rss_url[:80]}...")
            feed = feedparser.parse(rss_url)

            news_items = []
            for entry in feed.entries:
                try:
                    title = entry.title.strip()

                    # 過濾掉MSN的新聞
                    if 'MSN' in title:
                        continue

                    # 解析日期
                    published_date = self._parse_date(entry)
                    if not published_date:
                        continue

                    # 提取來源
                    source = self._extract_source(entry)

                    news_items.append({
                        'title': title,
                        'url': entry.link.strip(),
                        'date': published_date,
                        'source': source,
                        'topic': topic
                    })
                except Exception as e:
                    self.stderr.write(f"    解析項目時錯誤: {e}")
                    continue

            self.stdout.write(f"  收集到 {len(news_items)} 則新聞（已過濾MSN）")
            return news_items

        except Exception as e:
            self.stderr.write(f"  抓取Google News時發生錯誤: {e}")
            return []

    def _parse_date(self, entry):
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

    def _extract_source(self, entry):
        """從entry中提取新聞來源"""
        title = entry.get('title', '')
        if ' - ' in title:
            parts = title.rsplit(' - ', 1)
            if len(parts) == 2:
                return parts[1].strip()

        if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
            return entry.source.title

        return "Google News"

    def _deduplicate_news(self, news_list, topic):
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
                similarity = self._calculate_similarity(news['title'], seen_title)
                if similarity > 0.85:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_news.append(news)
                seen_urls.add(news['url'])
                seen_titles.append(news['title'])

        return unique_news

    def _calculate_similarity(self, str1, str2):
        """計算兩個字串的相似度"""
        return SequenceMatcher(None, str1, str2).ratio()

    def _resolve_google_news_url(self, url):
        """解析Google News重定向URL，獲取實際新聞網址"""
        try:
            # 如果不是Google News的URL，直接返回
            if 'news.google.com' not in url:
                return url

            self.stdout.write(f"      [調試] 解析Google News URL...")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            session = requests.Session()
            session.verify = False

            # Google News的article頁面需要特殊處理
            # 我們需要訪問並解析HTML來找到真實的新聞源連結
            response = session.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=20
            )

            # 解析HTML內容
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')

            # 方法1: 尋找c-wiz標籤中的data-n-au屬性（Google News特定結構）
            # 這個屬性通常包含實際新聞源的URL
            c_wiz = soup.find('c-wiz')
            if c_wiz and c_wiz.get('data-n-au'):
                source_url = c_wiz['data-n-au']
                if source_url and not source_url.startswith('http'):
                    source_url = 'https://' + source_url
                if source_url and 'news.google.com' not in source_url:
                    self.stdout.write(f"      [調試] ✓ 從data-n-au找到: {source_url[:50]}...")
                    session.close()
                    return source_url

            # 方法2: 尋找包含實際URL的<a>標籤
            # Google News頁面會有一個指向原始文章的連結
            for link in soup.find_all('a', href=True):
                href = link['href']
                # 跳過Google內部連結
                if href.startswith('http') and 'google.com' not in href:
                    self.stdout.write(f"      [調試] ✓ 從<a>標籤找到: {href[:50]}...")
                    session.close()
                    return href
                # 處理相對URL形式: ./articles/...實際URL
                if href.startswith('./articles/'):
                    # 這種格式後面可能帶有實際URL
                    parts = href.split('?')
                    if len(parts) > 1:
                        for param in parts[1].split('&'):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                if key in ['url', 'link'] and value.startswith('http'):
                                    from urllib.parse import unquote
                                    decoded_url = unquote(value)
                                    self.stdout.write(f"      [調試] ✓ 從URL參數找到: {decoded_url[:50]}...")
                                    session.close()
                                    return decoded_url

            # 方法3: 檢查meta refresh
            meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
            if meta_refresh and meta_refresh.get('content'):
                content_attr = meta_refresh['content']
                if 'url=' in content_attr.lower():
                    redirect_url = content_attr.split('url=', 1)[1].strip()
                    if redirect_url and 'news.google.com' not in redirect_url:
                        self.stdout.write(f"      [調試] ✓ 從meta refresh找到: {redirect_url[:50]}...")
                        session.close()
                        return redirect_url

            # 方法4: 檢查所有script標籤中的URL模式
            import re
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # 尋找看起來像新聞網站的URL
                    url_patterns = re.findall(r'https?://(?!news\.google\.com)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}[^\s"\'<>]*', script.string)
                    for found_url in url_patterns:
                        # 過濾掉常見的非新聞URL
                        if not any(skip in found_url for skip in ['googleapis.com', 'gstatic.com', 'schema.org']):
                            self.stdout.write(f"      [調試] ✓ 從JavaScript找到: {found_url[:50]}...")
                            session.close()
                            return found_url

            self.stdout.write(f"      [調試] ✗ 無法解析，Google News可能改變了頁面結構")
            session.close()
            return url

        except requests.exceptions.Timeout:
            self.stdout.write(f"      [調試] ✗ 請求超時")
            return url
        except requests.exceptions.ConnectionError as e:
            self.stdout.write(f"      [調試] ✗ 連接錯誤: {str(e)[:50]}")
            return url
        except Exception as e:
            self.stdout.write(f"      [調試] ✗ 異常: {type(e).__name__}: {str(e)[:50]}")
            import traceback
            self.stdout.write(f"      [調試] 詳細錯誤: {traceback.format_exc()[:200]}")
            return url

    def _fetch_article_content(self, url):
        """抓取新聞內容"""
        try:
            # 先解析Google News重定向
            actual_url = self._resolve_google_news_url(url)

            # 如果重定向失敗，嘗試直接使用原始URL
            if actual_url == url and 'news.google.com' in url:
                # Google News URL無法直接抓取內容
                return "無法解析Google News重定向"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://news.google.com/'
            }

            # 禁用SSL驗證以避免證書問題（企業環境）
            response = requests.get(actual_url, headers=headers, timeout=15, verify=False, allow_redirects=True)
            response.raise_for_status()

            # 設置正確的編碼
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.content, 'html.parser')

            # 移除不需要的元素
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'form', 'button']):
                tag.decompose()

            # 嘗試多種方式找到文章主要內容
            article = None

            # 方法1: 尋找article標籤
            article = soup.find('article')

            # 方法2: 尋找常見的內容class
            if not article:
                article = soup.find('div', class_=re.compile('article|content|post|entry|story', re.I))

            # 方法3: 尋找main標籤
            if not article:
                article = soup.find('main')

            # 方法4: 尋找id包含content的div
            if not article:
                article = soup.find('div', id=re.compile('content|article|post', re.I))

            # 提取段落
            if article:
                paragraphs = article.find_all(['p', 'h2', 'h3'])
            else:
                # 如果都找不到，直接取所有段落
                paragraphs = soup.find_all('p')

            # 提取文字並過濾
            content_parts = []
            for p in paragraphs:
                text = p.get_text().strip()
                # 過濾太短的段落（可能是廣告或導航）
                if text and len(text) > 20:
                    content_parts.append(text)

            content = '\n'.join(content_parts)

            # 限制長度
            if len(content) > 3000:
                content = content[:3000] + "..."

            # 檢查是否有實際內容
            if len(content) < 100:
                return "無法抓取有效內容"

            return content

        except requests.exceptions.Timeout:
            return f"抓取超時: {url[:50]}"
        except requests.exceptions.TooManyRedirects:
            return f"重定向過多: {url[:50]}"
        except requests.exceptions.RequestException as e:
            return f"網路錯誤: {str(e)[:80]}"
        except Exception as e:
            return f"抓取失敗: {str(e)[:100]}"

    def _improve_rss_summary(self, title, rss_summary):
        """使用AI改寫RSS摘要，使其更簡潔清晰"""
        try:
            prompt = f"""請將以下Google News的標題改寫成更簡潔、易讀的今日重點摘要。

【重要指示】
- 使用繁體中文
- 保留核心資訊，去除冗餘內容
- 不要添加任何額外資訊或評論
- 不要提及「根據」、「摘要」等說明文字
- 直接輸出改寫後的內容

===== 新聞標題 =====
{title}

===== 請輸出改寫後的摘要 =====
"""
            response = ask_oss(prompt, tag='RSS摘要改寫')
            summary = response.content.strip()

            # 移除可能的說明文字
            summary = re.sub(r'^(摘要：|摘要:|Summary:|改寫：)\s*', '', summary)
            summary = re.sub(r'^根據.*?[，,]\s*', '', summary)

            return summary if summary else rss_summary[:200]

        except Exception as e:
            # 如果AI處理失敗，直接返回原RSS摘要的前200字
            return rss_summary[:200] if rss_summary else f"處理失敗: {str(e)[:50]}"

    def _save_and_fetch_content(self, news_list, topic):
        """儲存新聞（只保存標題，不生成個別摘要）"""
        saved_news = []

        for i, news in enumerate(news_list, 1):
            try:
                # 檢查是否已存在
                if NewsItem.objects.filter(url=news['url']).exists():
                    news_item = NewsItem.objects.get(url=news['url'])
                    self.stdout.write(f"    [{i}/{len(news_list)}] 已存在: {news['title'][:50]}")
                else:
                    # 建立新新聞記錄（只保存標題和基本資訊）
                    news_item = NewsItem.objects.create(
                        topic=topic,
                        title=news['title'],
                        date=news['date'],
                        url=news['url'],
                        source=news['source'],
                        content="",  # 不保存內容
                        summary=""   # 不生成個別摘要
                    )
                    self.stdout.write(f"    [{i}/{len(news_list)}] 新增: {news['title'][:50]}")

                # 加入列表供每日摘要使用
                saved_news.append({
                    'title': news['title'],
                    'url': news['url'],
                    'source': news['source'],
                    'date': news['date']
                })

            except Exception as e:
                self.stderr.write(f"    處理新聞時發生錯誤: {e}")
                continue

        return saved_news

    def _generate_daily_summary(self, news_list, topic):
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

        except Exception as e:
            self.stderr.write(f"  生成每日摘要時發生錯誤: {e}")
            return None

    def _send_emails(self, topic, summary_html, news_list):
        """發送郵件給訂閱者"""
        subscriptions = Subscription.objects.filter(
            topic=topic,
            is_active=True
        ).select_related('user')

        if not subscriptions.exists():
            self.stdout.write(f"  沒有訂閱者，跳過郵件發送")
            return

        sent_count = 0
        for subscription in subscriptions:
            try:
                subject = f"【{topic.name}】每日新聞摘要 - {timezone.now().strftime('%Y-%m-%d')}"

                html_message = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="font-family: 'Microsoft JhengHei', 'PingFang TC', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h1 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">📰 {topic.name} - 今日新聞摘要</h1>

        <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>日期：</strong>{timezone.now().strftime('%Y年%m月%d日')}</p>
            <p style="margin: 5px 0;"><strong>新聞數量：</strong>{len(news_list)} 則</p>
        </div>

        {summary_html}

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em;">
            <p>此郵件由新聞訂閱系統自動發送</p>
            <p>如需取消訂閱，請登入系統進行設定</p>
            <p>內網系統路徑: https://single.sinotech.com.tw/redirect/token/codev/news/</p>
        </div>
    </div>
</body>
</html>
"""

                send_mail(
                    subject=subject,
                    message=f"【{topic.name}】今日新聞摘要\n\n收集到 {len(news_list)} 則新聞。\n\n請使用支援HTML的郵件客戶端查看完整內容。",
                    from_email=settings.NOTIFY_EMAIL,
                    recipient_list=[subscription.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                sent_count += 1
                self.stdout.write(f"  ✅ 已發送郵件給 {subscription.user.username} ({subscription.email})")

            except Exception as e:
                self.stderr.write(f"  ❌ 發送郵件給 {subscription.user.username} 失敗: {e}")

        self.stdout.write(f"  郵件發送完成: {sent_count}/{subscriptions.count()}")
