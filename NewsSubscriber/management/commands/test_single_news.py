"""
測試單一Google News URL，查看可以提取什麼資訊
"""
from django.core.management.base import BaseCommand
import requests
import urllib3
import ssl
import os
from bs4 import BeautifulSoup
import re

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局禁用SSL驗證
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

os.environ['PYTHONHTTPSVERIFY'] = '0'


class Command(BaseCommand):
    help = '測試單一Google News URL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='要測試的Google News URL',
        )

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write("測試Google News URL資訊提取")
        self.stdout.write("="*80)

        test_url = options.get('url')

        if not test_url:
            self.stdout.write("\n請提供Google News URL:")
            self.stdout.write("python manage.py test_single_news --url \"https://news.google.com/rss/articles/...\"")
            return

        self.stdout.write(f"\n測試URL:")
        self.stdout.write(f"  {test_url}\n")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            }

            self.stdout.write("【步驟1】發送請求...")
            session = requests.Session()
            session.verify = False

            response = session.get(
                test_url,
                headers=headers,
                allow_redirects=True,
                timeout=20
            )

            self.stdout.write(f"  狀態碼: {response.status_code}")
            self.stdout.write(f"  最終URL: {response.url[:80]}...")
            self.stdout.write(f"  重定向次數: {len(response.history)}\n")

            self.stdout.write("【步驟2】解析HTML內容...")
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')

            self.stdout.write(f"  HTML長度: {len(content)} 字元\n")

            # 提取標題
            self.stdout.write("【步驟3】尋找標題...")
            title_tag = soup.find('title')
            if title_tag:
                self.stdout.write(f"  標題: {title_tag.get_text().strip()}\n")
            else:
                self.stdout.write("  ✗ 未找到標題\n")

            # 尋找meta description (可能包含摘要)
            self.stdout.write("【步驟4】尋找meta description...")
            meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                       soup.find('meta', attrs={'property': 'og:description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content']
                self.stdout.write(f"  找到描述: {description[:200]}...\n")
            else:
                self.stdout.write("  ✗ 未找到meta description\n")

            # 尋找文章內容區域
            self.stdout.write("【步驟5】尋找文章內容...")

            # 方法1: 尋找article標籤
            article = soup.find('article')
            if article:
                self.stdout.write("  ✓ 找到<article>標籤")
                paragraphs = article.find_all('p')
                self.stdout.write(f"    包含 {len(paragraphs)} 個段落")
                if paragraphs:
                    first_para = paragraphs[0].get_text().strip()
                    self.stdout.write(f"    第一段: {first_para[:150]}...\n")
            else:
                self.stdout.write("  ✗ 未找到<article>標籤")

            # 方法2: 查找所有段落
            all_paragraphs = soup.find_all('p')
            self.stdout.write(f"  總共找到 {len(all_paragraphs)} 個<p>標籤")

            if all_paragraphs:
                self.stdout.write("\n  前3個段落內容:")
                for i, p in enumerate(all_paragraphs[:3], 1):
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        self.stdout.write(f"    {i}. {text[:100]}...")

            # 尋找所有連結
            self.stdout.write("\n【步驟6】尋找外部連結...")
            external_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and 'google.com' not in href:
                    external_links.append(href)

            if external_links:
                self.stdout.write(f"  找到 {len(external_links)} 個外部連結")
                self.stdout.write("  前5個外部連結:")
                for i, link in enumerate(external_links[:5], 1):
                    self.stdout.write(f"    {i}. {link[:80]}...")
            else:
                self.stdout.write("  ✗ 未找到外部連結")

            # 檢查特定的Google News結構
            self.stdout.write("\n【步驟7】檢查Google News特定結構...")

            # c-wiz標籤
            c_wiz = soup.find('c-wiz')
            if c_wiz:
                self.stdout.write("  ✓ 找到<c-wiz>標籤")
                if c_wiz.get('data-n-au'):
                    self.stdout.write(f"    data-n-au: {c_wiz['data-n-au']}")
            else:
                self.stdout.write("  ✗ 未找到<c-wiz>標籤")

            # 保存HTML到檔案以便檢查
            self.stdout.write("\n【步驟8】保存HTML內容...")
            debug_file = 'debug_google_news.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stdout.write(f"  HTML已保存到: {debug_file}")
            self.stdout.write("  您可以打開此檔案查看完整HTML結構")

            session.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n錯誤: {e}"))
            import traceback
            self.stdout.write(f"\n{traceback.format_exc()}")

        self.stdout.write("\n" + "="*80)
