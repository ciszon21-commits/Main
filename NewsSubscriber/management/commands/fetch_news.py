import feedparser
import google.generativeai as genai
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

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

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

            # 儲存新聞並抓取內容和摘要
            self.stdout.write(f"\n【步驟 3】儲存新聞並抓取內容摘要...")
            news_with_summaries = self._save_and_fetch_content(unique_news, topic, model)
            self.stdout.write(f"  成功處理 {len(news_with_summaries)} 則新聞")

            # 生成每日整合摘要
            if news_with_summaries:
                self.stdout.write(f"\n【步驟 4】生成每日整合摘要...")
                daily_summary_html = self._generate_daily_summary(news_with_summaries, topic, model)

                if daily_summary_html:
                    # 儲存摘要
                    try:
                        daily_summary = DailySummary.objects.create(
                            topic=topic,
                            summary=daily_summary_html,
                            date=today,
                            news_count=len(news_with_summaries)
                        )
                        self.stdout.write(f"  ✅ 每日摘要已生成並儲存")

                        # 發送郵件給訂閱者
                        self.stdout.write(f"\n【步驟 5】發送郵件給訂閱者...")
                        self._send_emails(topic, daily_summary_html, news_with_summaries)
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
                    # 解析日期
                    published_date = self._parse_date(entry)
                    if not published_date:
                        continue

                    # 提取來源
                    source = self._extract_source(entry)

                    news_items.append({
                        'title': entry.title.strip(),
                        'url': entry.link.strip(),
                        'date': published_date,
                        'source': source,
                        'topic': topic
                    })
                except Exception as e:
                    self.stderr.write(f"    解析項目時錯誤: {e}")
                    continue

            self.stdout.write(f"  收集到 {len(news_items)} 則新聞")
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

    def _fetch_article_content(self, url):
        """抓取新聞內容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 移除不需要的元素
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                tag.decompose()

            # 嘗試找到文章主要內容
            article = soup.find('article') or soup.find('div', class_=re.compile('article|content|post'))

            if article:
                paragraphs = article.find_all(['p', 'h1', 'h2', 'h3'])
            else:
                paragraphs = soup.find_all('p')

            # 提取文字
            content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

            # 限制長度
            if len(content) > 3000:
                content = content[:3000] + "..."

            return content if content else "無法抓取內容"

        except Exception as e:
            return f"抓取失敗: {str(e)[:100]}"

    def _generate_news_summary(self, title, content, model):
        """使用Gemini為單則新聞生成摘要"""
        try:
            prompt = f"""
請為以下新聞生成一個簡短的摘要（2-3句話，約80-120字）。
使用繁體中文，重點說明新聞的核心內容和重要性。

新聞標題：{title}

新聞內容：
{content[:1500]}

請直接輸出摘要，不要其他說明：
"""
            response = model.generate_content(prompt)
            summary = response.text.strip()
            return summary if summary else "摘要生成失敗"

        except Exception as e:
            return f"摘要生成失敗: {str(e)[:50]}"

    def _save_and_fetch_content(self, news_list, topic, model):
        """儲存新聞並抓取內容和生成摘要"""
        news_with_summaries = []

        for i, news in enumerate(news_list, 1):
            try:
                # 檢查是否已存在
                if NewsItem.objects.filter(url=news['url']).exists():
                    self.stdout.write(f"    [{i}/{len(news_list)}] 已存在，跳過: {news['title'][:40]}")
                    # 從資料庫讀取
                    news_item = NewsItem.objects.get(url=news['url'])
                    if news_item.summary:
                        news_with_summaries.append({
                            'title': news_item.title,
                            'url': news_item.url,
                            'source': news_item.source,
                            'date': news_item.date,
                            'summary': news_item.summary
                        })
                    continue

                self.stdout.write(f"    [{i}/{len(news_list)}] 處理: {news['title'][:40]}")

                # 抓取內容
                content = self._fetch_article_content(news['url'])
                time.sleep(1)  # 避免請求過快

                # 生成摘要
                if content and not content.startswith("抓取失敗") and not content.startswith("無法抓取"):
                    summary = self._generate_news_summary(news['title'], content, model)
                    time.sleep(1)  # API限流
                else:
                    summary = "無法生成摘要"

                # 儲存到資料庫
                news_item = NewsItem.objects.create(
                    topic=topic,
                    title=news['title'],
                    date=news['date'],
                    url=news['url'],
                    source=news['source'],
                    content=content[:5000] if content else "",  # 限制儲存長度
                    summary=summary
                )

                news_with_summaries.append({
                    'title': news['title'],
                    'url': news['url'],
                    'source': news['source'],
                    'date': news['date'],
                    'summary': summary
                })

            except Exception as e:
                self.stderr.write(f"    處理新聞時發生錯誤: {e}")
                continue

        return news_with_summaries

    def _generate_daily_summary(self, news_list, topic, model):
        """生成每日整合摘要"""
        try:
            # 準備新聞摘要資料
            news_summaries = []
            for i, news in enumerate(news_list, 1):
                news_summaries.append(f"{i}. 【{news['source']}】{news['title']}")
                news_summaries.append(f"   時間: {news['date'].strftime('%Y-%m-%d %H:%M')}")
                news_summaries.append(f"   連結: {news['url']}")
                news_summaries.append(f"   摘要: {news['summary']}")
                news_summaries.append("")

            summaries_text = "\n".join(news_summaries)

            # 建立提示詞
            prompt = f"""
你是一位專業的新聞分析師。請根據以下「{topic.name}」主題的新聞及其摘要，生成一份專業的今日新聞整合報告。

要求：
1. 使用繁體中文
2. 使用 HTML 格式，適合電子郵件發送
3. HTML 格式要求：
   - 使用適當的 HTML 標籤（h2, h3, p, ul, li, a 等）
   - 包含基本的內聯 CSS 樣式
   - 新聞連結使用 <a> 標籤，target="_blank"
4. 結構要求：
   - 第一部分：「今日重點」- 條列3-5個最重要的新聞趨勢或發展（使用 <ul><li> 格式）
   - 第二部分：「重要新聞」- 列出所有新聞，每則包含：
     * 新聞標題（含連結）
     * 來源和時間
     * 摘要說明
5. 風格：專業、簡潔、易讀

今日新聞資料（共{len(news_list)}則）：
{summaries_text}

請生成 HTML 格式的整合摘要（不需要完整的 HTML 文檔結構，只需要內容部分）：
"""

            response = model.generate_content(prompt)
            summary = response.text.strip()

            # 移除可能的markdown代碼塊標記
            summary = re.sub(r'^```html\n', '', summary)
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
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[subscription.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                sent_count += 1
                self.stdout.write(f"  ✅ 已發送郵件給 {subscription.user.username} ({subscription.email})")

            except Exception as e:
                self.stderr.write(f"  ❌ 發送郵件給 {subscription.user.username} 失敗: {e}")

        self.stdout.write(f"  郵件發送完成: {sent_count}/{subscriptions.count()}")
