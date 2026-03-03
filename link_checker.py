import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

def is_same_domain(url, base_url):
    """檢查是否為同一個網域"""
    return urlparse(url).netloc == urlparse(base_url).netloc

def get_all_links(url, soup, base_url):
    """從頁面中獲取所有內部與外部連結"""
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        
        # 忽略錨點和 javascript
        if href.startswith('#') or href.startswith('javascript:'):
            continue
            
        full_url = urljoin(url, href)
        links.add(full_url)
    return list(links)

def test_links(start_url, max_depth=2, timeout=5):
    """開始進行連結測試"""
    print(f"=== 開啟連結與跳轉測試 ===")
    print(f"起始網址: {start_url}")
    print(f"最大檢查深度: {max_depth}")
    print(f"========================\n")

    visited = set()
    to_visit = [(start_url, 0, start_url)]  # (url, depth, source_url)
    
    results = []
    dead_links = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    })

    while to_visit:
        current_url, depth, source_url = to_visit.pop(0)

        # 已經被檢查過就跳過
        if current_url in visited:
            continue
            
        visited.add(current_url)
        
        # 標示出處
        print(f"[{depth}] 檢查: {current_url} ", end="", flush=True)

        try:
            # 必須處理 redirect 來得知最終頁面
            response = session.get(current_url, timeout=timeout, allow_redirects=True)
            status_code = response.status_code
            
            # 若發生重定向，記錄歷史
            is_redirected = len(response.history) > 0
            
            if status_code == 200:
                print(f"[OK]")
            else:
                print(f"[死連結 - 狀態碼 {status_code}]")
                dead_links.append((current_url, status_code, source_url))

            if is_redirected:
                # 印出重定向路徑
                path = " -> ".join([f"[{r.status_code}] {r.url}" for r in response.history])
                print(f"    跳轉: {path} -> [{status_code}] {response.url}")

            # 如果這個網站屬於同一個 domain，且深度允許，剖析 HTML 取得新連結
            if status_code == 200 and depth < max_depth and is_same_domain(current_url, start_url):
                # 只有 HTML 才需要 parse (避免 parse 圖片或 PDF)
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    new_links = get_all_links(current_url, soup, start_url)
                    
                    for link in new_links:
                        if link not in visited:
                            # 避免重複加入
                            if not any(link == x[0] for x in to_visit):
                                to_visit.append((link, depth + 1, current_url))
                                
        except requests.exceptions.RequestException as e:
            print(f"[錯誤 - {type(e).__name__}]")
            dead_links.append((current_url, str(e), source_url))

    print("\n=== 測試報告 ===")
    print(f"總共檢查了 {len(visited)} 個連結")
    
    if dead_links:
        print(f"\n發現 {len(dead_links)} 個死連結或錯誤：")
        for url, reason, source in dead_links:
            print(f"- 網址: {url}")
            print(f"  來源頁面: {source}")
            print(f"  原因/狀態: {reason}")
            print("-" * 30)
    else:
        print("\n太棒了！沒有發現任何死連結！")

    print("\n測試結束")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="網頁連結與跳轉測試腳本")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8000/lunch/", help="起始網址 (預設: http://127.0.0.1:8000/lunch/)")
    parser.add_argument("-d", "--depth", type=int, default=2, help="檢查的遞迴深度 (預設: 2)")
    
    args = parser.parse_args()
    
    test_links(args.url, args.depth)
