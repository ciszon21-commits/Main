"""
檢查Google News RSS feed的所有可用欄位
"""
from django.core.management.base import BaseCommand
import feedparser
from urllib.parse import quote
import json


class Command(BaseCommand):
    help = '檢查Google News RSS feed中有哪些欄位可用'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keyword',
            type=str,
            default='AI',
            help='搜尋關鍵字（預設: AI）',
        )

    def handle(self, *args, **options):
        keyword = options.get('keyword', 'AI')

        self.stdout.write("="*80)
        self.stdout.write(f"檢查Google News RSS Feed 欄位")
        self.stdout.write("="*80)

        query = quote(keyword)
        rss_url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

        self.stdout.write(f"\nRSS URL: {rss_url}\n")

        try:
            feed = feedparser.parse(rss_url)

            self.stdout.write(f"找到 {len(feed.entries)} 則新聞\n")

            if feed.entries:
                # 檢查第一則新聞的所有欄位
                entry = feed.entries[0]

                self.stdout.write("="*80)
                self.stdout.write("第一則新聞的所有欄位:")
                self.stdout.write("="*80)

                # 顯示所有可用的屬性
                for attr in dir(entry):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(entry, attr)
                            # 只顯示數據屬性，跳過方法
                            if not callable(value):
                                self.stdout.write(f"\n【{attr}】")
                                if isinstance(value, (str, int, float, bool)):
                                    self.stdout.write(f"  {value}")
                                elif isinstance(value, dict):
                                    self.stdout.write(f"  {json.dumps(value, indent=2, ensure_ascii=False)}")
                                elif isinstance(value, list):
                                    for i, item in enumerate(value):
                                        self.stdout.write(f"  [{i}] {item}")
                                else:
                                    self.stdout.write(f"  類型: {type(value).__name__}")
                                    self.stdout.write(f"  值: {str(value)[:200]}")
                        except Exception as e:
                            self.stdout.write(f"\n【{attr}】")
                            self.stdout.write(f"  錯誤: {e}")

                # 特別檢查是否有source相關欄位
                self.stdout.write("\n" + "="*80)
                self.stdout.write("檢查 source 相關欄位:")
                self.stdout.write("="*80)

                if hasattr(entry, 'source'):
                    self.stdout.write(f"\nentry.source 存在:")
                    source = entry.source
                    if hasattr(source, 'href'):
                        self.stdout.write(f"  source.href: {source.href}")
                    if hasattr(source, 'title'):
                        self.stdout.write(f"  source.title: {source.title}")
                    self.stdout.write(f"  完整內容: {source}")
                else:
                    self.stdout.write("\n✗ entry.source 不存在")

                # 檢查links列表
                if hasattr(entry, 'links'):
                    self.stdout.write(f"\nentry.links 包含 {len(entry.links)} 個連結:")
                    for i, link in enumerate(entry.links):
                        self.stdout.write(f"\n  連結 {i+1}:")
                        if hasattr(link, 'href'):
                            self.stdout.write(f"    href: {link.href}")
                        if hasattr(link, 'rel'):
                            self.stdout.write(f"    rel: {link.rel}")
                        if hasattr(link, 'type'):
                            self.stdout.write(f"    type: {link.type}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n錯誤: {e}"))
            import traceback
            self.stdout.write(f"\n{traceback.format_exc()}")

        self.stdout.write("\n" + "="*80)
