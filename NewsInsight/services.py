import io
import base64
import feedparser
import urllib.parse
import urllib.request
import urllib.error
import time
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import rjieba
import pandas as pd
import matplotlib
# Use non-interactive backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import os

logger = logging.getLogger(__name__)

class GoogleNewsService:
    @staticmethod
    def search_news(keywords, start_date=None, end_date=None):
        """
        搜尋 Google News
        """
        # 為了突破 100 篇限制，我們將日期範圍切分為 30 天的區塊進行多次請求
        if not end_date:
            end_dt = datetime.now()
        else:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
        if not start_date:
            # 若無指定起始日期，預設往前推 6 個月以獲取大量資料
            start_dt = end_dt - timedelta(days=180)
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        results = []
        links_seen = set()
        network_error = False
        
        current_start = start_dt
        chunk_days = 30 # 每 30 天查詢一次
        
        while current_start <= end_dt:
            current_end = current_start + timedelta(days=chunk_days)
            if current_end > end_dt:
                current_end = end_dt
                
            q_start = current_start.strftime("%Y-%m-%d")
            q_end = (current_end + timedelta(days=1)).strftime("%Y-%m-%d") # Google News before 包含當天不包含隔天
            
            query_parts = [keywords, f"after:{q_start}", f"before:{q_end}"]
            search_query = " ".join(query_parts)
            encoded_query = urllib.parse.quote(search_query)
            
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            
            feed = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 不限制於 60 秒，容許時間超過 5 分鐘，這裡設定為 10 分鐘 (600 秒)
                    # 並且計算抓取花費的時間
                    start_fetch = time.time()
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=600) as response:
                        feed_data = response.read()
                    fetch_duration = time.time() - start_fetch
                    
                    feed = feedparser.parse(feed_data)
                    
                    success_msg = f"✅ Fetch success [{q_start} to {q_end}], took {fetch_duration:.2f} seconds."
                    print(success_msg)
                    logger.info(success_msg)
                    
                    break  # 成功取得資料，跳出重試迴圈
                except urllib.error.HTTPError as e:
                    if e.code in [403, 429]:
                        error_msg = f"🚨 [Blocked] 被 Google 阻擋! HTTP Status {e.code} [{q_start} to {q_end}], attempt {attempt + 1}"
                    else:
                        error_msg = f"[Network Warning] HTTP Error {e.code} [{q_start} to {q_end}], attempt {attempt + 1}: {e}"
                    print(error_msg)
                    logger.warning(error_msg)
                    if attempt < max_retries - 1:
                        time.sleep(3)
                except Exception as e:
                    error_msg = f"[Network Warning] Fetching news error [{q_start} to {q_end}], attempt {attempt + 1}: {e}"
                    print(error_msg)
                    logger.warning(error_msg)
                    if attempt < max_retries - 1:
                        time.sleep(3)  # 等待 3 秒後重試
            
            if not feed or not hasattr(feed, 'entries'):
                # 如果重試後仍失敗，則跳過目前區段
                fail_msg = f"❌ [Network Error] 網路速度過慢或連線異常，無法取得 {q_start} 到 {q_end} 的新聞資料。已經自動跳過此區段。"
                print(fail_msg)
                logger.error(fail_msg)
                network_error = True
                
                if current_start == end_dt:
                    break
                current_start = current_end + timedelta(days=1)
                continue
            
            for entry in feed.entries:
                if entry.link in links_seen:
                    continue
                links_seen.add(entry.link)
                
                title = entry.title
                source = ""
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                    
                pub_date_str = entry.published
                try:
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                except Exception:
                    pub_date = datetime.now()
                    
                summary = ""
                if hasattr(entry, 'summary'):
                    soup = BeautifulSoup(entry.summary, "html.parser")
                    summary = soup.get_text(separator=' ', strip=True)
                    
                results.append({
                    'title': title,
                    'link': entry.link,
                    'source': source if source else getattr(entry, 'source', {}).get('title', 'Unknown'),
                    'pub_date': pub_date,
                    'summary': summary
                })
                
            if current_start == end_dt:
                break
            current_start = current_end + timedelta(days=1)
            
        return results, network_error

class NewsAnalyzer:
    FONT_PATH = "C:\\Windows\\Fonts\\msjh.ttc"
    
    @staticmethod
    def _segment_words(texts, topic_words="", stop_words=""):
        topics = [w.strip() for w in topic_words.replace('，', ',').split(',') if w.strip()]

        stops = set([w.strip() for w in stop_words.replace('，', ',').split(',') if w.strip()])
        default_stops = {'的', '了', '和', '與', '在', '是', '也', '有', '就', '都', '而', '及', '不', '會', '為', '以', '對', '於', '等', '之', '指出', '表示', '報導'}
        stops = stops.union(default_stops)

        all_words = []
        for text in texts:
            words = rjieba.cut(text, hmm=True)
            # rjieba 不支援 add_word，以後處理方式重組被拆散的主題詞
            if topics:
                result = []
                i = 0
                while i < len(words):
                    matched = False
                    for topic in sorted(topics, key=len, reverse=True):
                        # 嘗試以連續 token 組合是否能形成主題詞
                        combined = ''
                        j = i
                        while j < len(words) and len(combined) < len(topic):
                            combined += words[j]
                            j += 1
                            if combined == topic:
                                result.append(topic)
                                i = j
                                matched = True
                                break
                        if matched:
                            break
                    if not matched:
                        result.append(words[i])
                        i += 1
                words = result
            filtered = [w for w in words if w not in stops and len(w.strip()) > 1]
            all_words.extend(filtered)

        return all_words
        
    @classmethod
    def generate_wordcloud_base64(cls, texts, topic_words="", stop_words="", colormap='viridis'):
        words = cls._segment_words(texts, topic_words, stop_words)
        if not words:
            return None
            
        # Get unique words and their frequencies, then construct a freq dict
        # Actually WordCloud handles duplicates naturally by creating a freq dict internally 
        # when we pass text_joined. But if user wants "words non-repeat", collocations=False helps.
        text_joined = " ".join(words)
        font_p = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        # Windows 微軟正黑體 if not fallback to default. Adjust path depending on env.
        font_path = cls.FONT_PATH if os.path.exists(cls.FONT_PATH) else font_p
        
        wc = WordCloud(
            font_path=font_path,
            width=800,
            height=400,
            background_color='white',
            max_words=200,
            colormap=colormap,
            collocations=False # 避免重複片語出現
        )
        wc.generate(text_joined)
        
        img_buffer = io.BytesIO()
        wc.to_image().save(img_buffer, format='PNG')
        return base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
    @classmethod
    def generate_frequency_chart_base64(cls, texts, topic_words="", stop_words="", top_n=10):
        words = cls._segment_words(texts, topic_words, stop_words)
        if not words:
            return None
            
        word_counts = Counter(words)
        common_words = word_counts.most_common(top_n)
        
        if not common_words:
            return None
            
        labels, counts = zip(*common_words)
        
        plt.figure(figsize=(10, 6))
        
        # 設定支援中文的字體
        if os.path.exists(cls.FONT_PATH):
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        plt.bar(labels, counts, color='skyblue')
        plt.title('高頻關鍵字分佈 (Top 10)')
        plt.xlabel('關鍵字')
        plt.ylabel('出現次數')
        plt.xticks(rotation=45)
        
        # 顯示數量
        for i, v in enumerate(counts):
            plt.text(i, v + 0.1, str(v), ha='center')
            
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        plt.close()
        
        return base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
    @classmethod
    def generate_frequency_data(cls, texts, topic_words="", stop_words="", top_n=10):
        words = cls._segment_words(texts, topic_words, stop_words)
        if not words:
            return None
            
        word_counts = Counter(words)
        common_words = word_counts.most_common(top_n)
        
        if not common_words:
            return None
            
        labels, counts = zip(*common_words)
        return {"labels": list(labels), "values": list(counts)}

    @classmethod
    def generate_timeline_data(cls, articles):
        if not articles:
            return None
            
        df = pd.DataFrame(articles)
        df['year_month'] = df['pub_date'].dt.to_period('M')
        monthly_counts = df.groupby('year_month').size()
        
        if monthly_counts.empty:
            return None
            
        x_labels = monthly_counts.index.astype(str).tolist()
        y_values = monthly_counts.values.tolist()
        
        return {"labels": x_labels, "values": y_values}
        
    @classmethod
    def generate_timeline_chart_base64(cls, articles):
        if not articles:
            return None
            
        # 建立 DataFrame 並轉成 年-月 格式統計
        df = pd.DataFrame(articles)
        df['year_month'] = df['pub_date'].dt.to_period('M')
        monthly_counts = df.groupby('year_month').size()
        
        if monthly_counts.empty:
            return None
            
        plt.figure(figsize=(10, 6))
        
        if os.path.exists(cls.FONT_PATH):
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 轉回字串作為 x 軸
        x_labels = monthly_counts.index.astype(str)
        y_values = monthly_counts.values
        
        plt.plot(x_labels, y_values, marker='o', linestyle='-', color='coral')
        plt.title('新聞量時間軸變化趨勢')
        plt.xlabel('發布月份')
        plt.ylabel('新聞篇數')
        plt.xticks(rotation=45)
        
        # 顯示節點數量
        for i, v in enumerate(y_values):
            plt.text(i, v + 0.2, str(v), ha='center', va='bottom')
            
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        plt.close()
        
        return base64.b64encode(img_buffer.getvalue()).decode('utf-8')
