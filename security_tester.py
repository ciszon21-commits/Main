import requests
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urljoin
import os
import django
import sys

# 初始化 Django 環境 (僅用於輔助取得測試資料，如合法的餐廳 ID)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()
from LunchOrder.models import Restaurant, MenuItem

BASE_URL = 'http://127.0.0.1:8000'

def get_csrf_token(session, url):
    """獲取 CSRF Token"""
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if csrf_input:
            return csrf_input['value']
    except requests.RequestException:
        pass
    return None

def test_sql_injection_in_url(session, url_path):
    """測試 URL 參數的 SQL 注入防護 (基本的 error-based 檢查)"""
    print(f"\n--- [測試] SQL Injection (URL 參數) ---")
    test_payloads = ["'", "\"", "1' OR '1'='1", "1; DROP TABLE users"]
    
    url = urljoin(BASE_URL, url_path)
    safe = True
    for payload in test_payloads:
        test_url = f"{url}?year={payload}&month={payload}"
        try:
            response = session.get(test_url, timeout=5)
            # Django 遇到錯誤的數字參數通常會回傳 200 (跳回預設值) 或 404/400
            # 若回傳 500 表示後端沒有 catch 錯誤，可能存在風險或未處理的異常
            if response.status_code == 500:
                print(f"⚠️ 潛在風險: 使用 Payload {payload} 觸發了 500 Internal Server Error (URL: {test_url})")
                safe = False
        except requests.RequestException as e:
            print(f"❌ 請求失敗: {e}")
            safe = False
            
    if safe:
        print("✅ 通過: URL 參數看起來對基本 SQL Injection 免疫 (無 500 報錯)")

def test_xss_in_form(session, r_id, m_id):
    """測試表單提交的 XSS (Cross-Site Scripting) 防護"""
    from datetime import datetime, timedelta
    print(f"\n--- [測試] XSS Attack (表單欄位) ---")
    
    # 為了成功拿到表單，我們必須指定一個未來的日期，因為今天的 11:00 可能已經過了
    order_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    
    test_url = urljoin(BASE_URL, f'/lunch/create/?date={order_date}&restaurant_id={r_id}')
    csrf_token = get_csrf_token(session, test_url)
    
    if not csrf_token:
        print("❌ 無法取得 CSRF Token, 跳過 XSS 測試")
        return

    xss_payload = "<script>alert('XSS')</script><b>Test</b>"
    data = {
        'csrfmiddlewaretoken': csrf_token,
        'menu_item': str(m_id), 
        'quantity': '1',
        'employee_name': xss_payload,  # 嘗試注入腳本
        'notes': xss_payload # 嘗試注入腳本
    }
    
    try:
        response = session.post(test_url, data=data, allow_redirects=True)
        # 如果訂單建立成功，我們去列表頁檢查是否被 escape
        list_url = urljoin(BASE_URL, '/lunch/list/')
        list_response = session.get(list_url)
        
        # 檢查原生的 script tag 是否出現在 HTML 中（沒有被 escape）
        if "<script>alert('XSS')</script>" in list_response.text:
            print("❌ 危險: 發現未過濾的 XSS Payload 在訂單列表中！")
        else:
            print("✅ 通過: 輸入被 Django 模板安全過濾或轉義 (Sanitized)")
            
    except requests.RequestException as e:
        print(f"❌ 請求失敗: {e}")

def test_missing_csrf(session, r_id):
    """測試未攜帶 CSRF Token 的 POST 請求是否被阻擋"""
    print(f"\n--- [測試] CSRF Protection (跨站請求偽造) ---")
    api_url = urljoin(BASE_URL, '/lunch/api/set-schedule/')
    
    data = {
        'date': '2030-01-01',
        'restaurant_id': str(r_id),
        'action': ''
    }
    
    try:
        # 不帶 CSRF token 送出 POST
        response = session.post(api_url, data=data)
        if response.status_code == 403:  # 403 Forbidden
            print("✅ 通過: 缺少 CSRF Token 的 POST 請求被伺服器成功阻擋 (403 Forbidden)")
        elif response.status_code == 200 or response.status_code == 302:
             print("❌ 危險: 缺少 CSRF Token 的請求竟被接受！")
        else:
            print(f"⚠️ 注意: 回傳了非預期的狀態碼 {response.status_code}")
    except requests.RequestException as e:
         print(f"❌ 請求失敗: {e}")

def run_security_tests():
    print("========== 啟動網頁資訊安全基礎測試 ==========")
    session = requests.Session()
    
    r = Restaurant.objects.filter(is_active=True).first()
    m = MenuItem.objects.filter(restaurant=r, is_available=True).first() if r else None
    
    if not r or not m:
         print("❌ 無法取得測試資料，請確定資料庫有餐廳與菜單。")
         return
    
    r_id = r.id
    m_id = m.id
    
    # 1. 測試 SQL Injection (透過 GET URL 參數)
    # 我們拿 order_list 這個有吃 year/month 參數的頁面來試
    test_sql_injection_in_url(session, '/lunch/list/')
    
    # 2. 測試 CSRF 防護
    test_missing_csrf(session, r_id)
    
    # 3. 測試 XSS (透過在員工姓名與備註塞入惡意腳本)
    test_xss_in_form(session, r_id, m_id)

    print("\n========== 測試結束 ==========")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="網頁資訊安全簡易測試腳本")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8000", help="網站 Base URL")
    args = parser.parse_args()
    BASE_URL = args.url.rstrip('/')
    run_security_tests()
