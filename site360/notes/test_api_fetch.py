"""
================================================================================
API 連線測試腳本（根據對方提供的 JS 範例改寫）
================================================================================
流程（兩段式 Middleware 自動登入）：
    第一次 GET → Middleware 讀取 X-Platform-Username / X-Platform-Password
             → 伺服器回 302 並在 Set-Cookie 中帶入 sessionid
    第二次 GET → 帶著 sessionid Cookie 再次請求 → 取得 JSON 資料

執行方式：
    python site360/notes/test_api_fetch.py
================================================================================
"""

import json
import requests

# ── 設定區 ─────────────────────────────────────────────────────────────────────
BASE_URL  = "https://cmservice.sinotech.com.tw"
FORM_UID  = "1cbdc54d-d209-4132-b652-ef06ea125b2b"
API_TOKEN = "90f86588-8656-43fa-b2ed-39655d3755bb"
USERNAME  = "360paltfom"
PASSWORD  = "testapi0211"

API_URL = f"{BASE_URL}/HN/api/form-basic/{FORM_UID}/"
# ───────────────────────────────────────────────────────────────────────────────


def fetch_form_data():
    """
    兩段式 Middleware 自動登入流程：
    Step 1：帶帳密 Header 觸發 Middleware，取得 Session Cookie（預期 302）
    Step 2：帶 Cookie 重新請求，取得 JSON 資料（預期 200 + JSON）
    """

    # ── Step 1：觸發 Middleware 登入，不跟隨 Redirect ─────────────────────────
    print("=" * 60)
    print("Step 1：觸發 Middleware 自動登入")
    print(f"  URL: {API_URL}")

    step1_headers = {
        "Authorization": f"Token {API_TOKEN}",   # Token 格式（非 Bearer）
        "Accept": "application/json",
        "X-Platform-Username": USERNAME,          # 對方 Middleware 專用自訂 Header
        "X-Platform-Password": PASSWORD,          # 對方 Middleware 專用自訂 Header
    }

    resp1 = requests.get(
        API_URL,
        headers=step1_headers,
        allow_redirects=False,   # 不自動跟 302，手動處理 Redirect
        timeout=15,
    )

    print(f"  Status     : {resp1.status_code}")
    print(f"  Location   : {resp1.headers.get('location', '(none)')}")
    set_cookie_raw = resp1.headers.get("set-cookie", "")
    print(f"  Set-Cookie : {'有' if set_cookie_raw else '無'}")

    if resp1.status_code not in (302, 301):
        print(f"\n❌ Step 1 預期收到 302，但收到 {resp1.status_code}")
        print(f"  回應內容（前 500 字）：")
        print(resp1.text[:500])
        return None

    # 解析 Set-Cookie → 組成 Cookie Header 字串
    cookie_header = parse_cookies(set_cookie_raw)
    location = resp1.headers.get("location", "")
    redirect_url = f"{BASE_URL}{location}" if location.startswith("/") else location

    print(f"\n✅ Step 1 成功，取得 Session Cookie")
    print(f"  Redirect 到: {redirect_url}")

    # ── Step 2：帶 Cookie 取 JSON ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Step 2：帶 Session Cookie 取得資料")

    step2_headers = {
        "Authorization": f"Token {API_TOKEN}",
        "Accept": "application/json",
        "Cookie": cookie_header,
    }

    resp2 = requests.get(
        redirect_url,
        headers=step2_headers,
        allow_redirects=False,
        timeout=15,
    )

    content_type = resp2.headers.get("content-type", "")
    print(f"  Status       : {resp2.status_code}")
    print(f"  Content-Type : {content_type}")

    if "application/json" in content_type:
        data = resp2.json()

        # 寫入檔案（避免終端編碼問題）
        output_path = "site360/notes/api_result.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 成功取得 JSON！已儲存至 {output_path}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return data
    else:
        print(f"\n❌ Step 2 未收到 JSON，回應如下（前 500 字）：")
        print(resp2.text[:500])
        return None


def parse_cookies(set_cookie_raw: str) -> str:
    """
    將 Set-Cookie Header 的原始字串解析成 Cookie Header 字串。
    例：「sessionid=abc; Path=/」→「sessionid=abc」
    """
    if not set_cookie_raw:
        return ""

    import re
    parts = re.split(r",(?=[^;]+=)", set_cookie_raw)
    pairs = []
    for part in parts:
        first = part.split(";")[0].strip()
        if "=" in first:
            pairs.append(first)
    return "; ".join(pairs)


if __name__ == "__main__":
    result = fetch_form_data()

    print("\n" + "=" * 60)
    if result is None:
        print("❌ 資料取得失敗，請檢查以上輸出訊息。")
    else:
        print("✅ 完成！")
    print("=" * 60)
