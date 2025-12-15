"""
測試Google News重定向功能
"""
from django.core.management.base import BaseCommand
import requests
import urllib3
import ssl
import os

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局禁用SSL驗證
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

os.environ['PYTHONHTTPSVERIFY'] = '0'


class Command(BaseCommand):
    help = '測試Google News URL重定向'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='要測試的Google News URL',
        )

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write("Google News URL重定向測試")
        self.stdout.write("="*80)

        test_url = options.get('url')

        if not test_url:
            self.stdout.write("\n請提供Google News URL:")
            self.stdout.write("python manage.py test_news_redirect --url \"https://news.google.com/rss/articles/...\"")
            return

        self.stdout.write(f"\n原始URL:")
        self.stdout.write(f"  {test_url}\n")

        # 測試重定向
        self.stdout.write("【測試1】使用GET請求跟隨重定向...")

        try:
            from bs4 import BeautifulSoup
            import re
            from urllib.parse import unquote

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            }

            session = requests.Session()
            session.verify = False

            response = session.get(
                test_url,
                headers=headers,
                allow_redirects=True,
                timeout=20
            )

            status_code = response.status_code
            redirects = len(response.history)
            final_url = response.url

            self.stdout.write(f"\n【HTTP重定向結果】")
            self.stdout.write(f"  HTTP狀態碼: {status_code}")
            self.stdout.write(f"  重定向次數: {redirects}")
            self.stdout.write(f"  最終URL: {final_url[:80]}...\n")

            # 判斷HTTP重定向是否成功
            if final_url != test_url and 'news.google.com' not in final_url:
                self.stdout.write(self.style.SUCCESS("  ✓ HTTP重定向成功！"))
                session.close()
                return

            # HTTP重定向失敗，嘗試解析HTML
            self.stdout.write(self.style.WARNING("  ✗ HTTP未重定向到新聞源，嘗試解析HTML...\n"))

            self.stdout.write("【測試2】解析Google News頁面HTML...")

            content = response.text
            soup = BeautifulSoup(content, 'html.parser')

            found_urls = []

            # 方法1: c-wiz標籤
            c_wiz = soup.find('c-wiz')
            if c_wiz and c_wiz.get('data-n-au'):
                source_url = c_wiz['data-n-au']
                if not source_url.startswith('http'):
                    source_url = 'https://' + source_url
                found_urls.append(('c-wiz data-n-au屬性', source_url))

            # 方法2: 外部連結
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and 'google.com' not in href:
                    found_urls.append(('<a>標籤', href))
                    break  # 只取第一個

            # 方法3: URL參數
            for link in soup.find_all('a', href=True):
                href = link['href']
                if './articles/' in href and '?' in href:
                    parts = href.split('?')
                    if len(parts) > 1:
                        for param in parts[1].split('&'):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                if key in ['url', 'link'] and value.startswith('http'):
                                    decoded_url = unquote(value)
                                    found_urls.append(('URL參數', decoded_url))
                                    break
                    break

            # 方法4: meta refresh
            meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
            if meta_refresh and meta_refresh.get('content'):
                content_attr = meta_refresh['content']
                if 'url=' in content_attr.lower():
                    redirect_url = content_attr.split('url=', 1)[1].strip()
                    if 'news.google.com' not in redirect_url:
                        found_urls.append(('meta refresh', redirect_url))

            # 方法5: JavaScript中的URL
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    url_patterns = re.findall(r'https?://(?!news\.google\.com)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}[^\s"\'<>]*', script.string)
                    for found_url in url_patterns:
                        if not any(skip in found_url for skip in ['googleapis.com', 'gstatic.com', 'schema.org']):
                            found_urls.append(('JavaScript', found_url))
                            break
                    if found_urls and found_urls[-1][0] == 'JavaScript':
                        break

            self.stdout.write(f"\n【HTML解析結果】")
            if found_urls:
                self.stdout.write(self.style.SUCCESS(f"  ✓ 找到 {len(found_urls)} 個可能的新聞源URL:\n"))
                for i, (method, url) in enumerate(found_urls, 1):
                    self.stdout.write(f"  {i}. 方法: {method}")
                    self.stdout.write(f"     URL: {url[:80]}...")
                    if len(url) > 80:
                        self.stdout.write(f"          {url[80:]}")
                    self.stdout.write("")
            else:
                self.stdout.write(self.style.ERROR("  ✗ 無法從HTML中找到新聞源URL"))
                self.stdout.write(f"\n【調試資訊】HTML內容前500字元:")
                self.stdout.write(content[:500])

            session.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ 錯誤: {e}"))
            import traceback
            self.stdout.write(f"\n詳細錯誤:\n{traceback.format_exc()}")

        self.stdout.write("\n" + "="*80)
