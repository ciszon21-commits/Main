import argparse
import concurrent.futures
import time
import requests
from urllib.parse import urljoin

# 測試網址清單
ENDPOINTS = [
    '/lunch/',                    # 日曆首頁
    '/lunch/list/',               # 訂單列表
    '/lunch/restaurants/',        # 餐廳列表
    '/lunch/statistics/',         # 訂單統計
]

def fetch_url(url, timeout=5):
    """發送單次請求並記錄時間與狀態碼"""
    start_time = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        duration = time.time() - start_time
        return {
            'status': response.status_code,
            'duration': duration,
            'url': url,
            'error': None
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'status': None,
            'duration': duration,
            'url': url,
            'error': str(e)
        }

def run_stress_test(base_url, total_requests, max_workers):
    """執行壓力測試"""
    print(f"=== 開始壓力測試 ===")
    print(f"目標網站: {base_url}")
    print(f"總請求數: {total_requests}")
    print(f"併發執行緒(Concurrent Users): {max_workers}")
    print(f"===================\n")

    urls_to_test = [urljoin(base_url, endpoint) for endpoint in ENDPOINTS]
    
    # 建立請求任務清單 (平均分配不同端點)
    tasks = []
    for i in range(total_requests):
        tasks.append(urls_to_test[i % len(urls_to_test)])

    results = []
    success_count = 0
    fail_count = 0
    start_test_time = time.time()

    # 使用 ThreadPoolExecutor 進行併發請求
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任務
        future_to_url = {executor.submit(fetch_url, url): url for url in tasks}
        
        # 收集結果，並顯示進度
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url), 1):
            res = future.result()
            results.append(res)
            
            if res['status'] == 200:
                success_count += 1
            else:
                fail_count += 1

            if i % (total_requests // 10 if total_requests >= 10 else 1) == 0:
                print(f"進度: {i}/{total_requests} (成功: {success_count}, 失敗: {fail_count})")

    total_time = time.time() - start_test_time
    
    # 計算統計數據
    durations = [r['duration'] for r in results if r['status'] == 200]
    
    print("\n=== 測試結果報告 ===")
    print(f"總花費時間: {total_time:.2f} 秒")
    print(f"RPS (Requests Per Second): {total_requests / total_time:.2f} 請求/秒")
    print(f"成功請求: {success_count}")
    print(f"失敗請求: {fail_count}")
    
    if durations:
        print(f"\n--- 回應時間統計 (成功請求) ---")
        print(f"平均回應時間: {sum(durations) / len(durations):.4f} 秒")
        print(f"最快回應時間: {min(durations):.4f} 秒")
        print(f"最慢回應時間: {max(durations):.4f} 秒")
        
    if fail_count > 0:
        print("\n--- 錯誤範例 ---")
        errors = [r for r in results if r['status'] != 200][:5]
        for err in errors:
            if err['error']:
                print(f"[{err['url']}] 錯誤: {err['error']}")
            else:
                print(f"[{err['url']}] 狀態碼: {err['status']}")
    print("===================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="便當訂購系統簡易壓力測試腳本")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8000", help="目標網站的 Base URL (預設: http://127.0.0.1:8000)")
    parser.add_argument("-n", "--requests", type=int, default=100, help="總共要發送的請求數量 (預設: 100)")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="同時併發的執行緒數量 (預設: 10)")
    
    args = parser.parse_args()
    
    run_stress_test(args.url, args.requests, args.concurrency)
