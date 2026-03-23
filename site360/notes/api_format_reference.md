# API 回傳格式與介接流程參考文件

> 紀錄日期：2026-03-12 (最新修訂)  
> 用途：與工管部平台 CMS API 介接文件，涵蓋認證、資料映射、媒體下載與自動化流程。

---

## 1. 認證與安全性 (Authentication)

系統採用分離式的認證管理：
*   **私密設定**：敏感憑證（Token, Username, Password）存放於 `site360/services/cms_secrets.py`。
*   **Version Control**：`cms_secrets.py` 已列入 `.gitignore` (或 `.git/info/exclude`)，確保不洩漏。另提供 `cms_secrets.example.py` 作為範本。
*   **API 認證**：呼叫 API 時使用兩段式 Middleware 登入流程。
*   **媒體認證**：下載圖片時直接使用 `Authorization: Token {API_TOKEN}` Header。

---

## 2. 核心資料結構

### 頂層與 `data` 物件
主要關注 `form_uid` (記錄來源) 與專案資訊。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `form_uid` | `string` | 外部表單唯一 ID，記錄於熱點的 `external_form_uid` 欄位 |
| `project_code` | `string` | 與 `tender_name` 組合為專案名稱 |
| `photos` | `array` | 全景圖清單，需搭配 `uuid` 下載 |
| `assessments` | `array` | 危害評估內容，將轉換為「未分配」的熱點 |

---

## 3. 媒體下載流程 (Media Sync)

**⚠️ 重要變更**：不可使用 `photos[].url` 直連，需使用 UUID 格式。

*   **下載網址**：`https://cmservice.sinotech.com.tw/auth/file/{photo_uuid}/`
*   **認證方式**：需帶入 `Authorization: Token {CMS_API_TOKEN}`。
*   **處理邏輯**：
    1. 抓取 `photos` 中的 `uuid`。
    2. 組成新網址並帶 Token 下載。
    3. 驗證 `Content-Type: image/jpeg`。
    4. 存入 Django 並關聯至 Scene。

---

## 4. 自動化建立邏輯 (Automated Logic)

### A. 專案 (Project)
*   **命名規則**：`{project_code}_{tender_code}_{tender_name}`。
*   **座標**：依據 `geo_bounds` 計算平均中心點。

### B. 場景 (Scene)
*   每張照片建立一個獨立場景 (Scene)。
*   標題：`{workitem} - {first_worklayer} ({index})`。

### C. 熱點 (Hotspots) - 危害評估
*   **分配狀態**：**未分配專案 (Unassigned)**。建立時 `scene=None`。
*   **對應規則**：
    *   `title` ← `survey_content`
    *   `description` ← 組合 `hazard_status` (危害狀態) 與 `safety_measure` (安全措施)
    *   `external_form_uid` ← 寫入 `data.form_uid`
    *   **忽略項**：暫時忽略 `category` 與自動危害類別映射。
*   **位置**：`pitch=0, yaw=0` (因為未放入場景)。

---

## 5. 介接流程階段 (Stages)

1.  **Stage 1: 接收轉跳**
    *   接收 `?form_uid=...` 並記錄。
2.  **Stage 2: API 抓取**
    *   背景執行兩段式 Middleware Auth。
    *   取得 JSON 資料（包含 Photos 與 Assessments）。
3.  **Stage 3: 資源建立**
    *   建立 Project。
    *   逐一由 `/auth/file/{uuid}/` 下載圖片並建立 Scene。
    *   逐一建立未分配的 Hotspots，並標註 `external_form_uid`。
4.  **Stage 4: 完成轉跳**
    *   **Redirect 目標**：`site360:project_detail` (專案詳情頁)。
    *   使用者可在詳情頁看到「資源清單」中標示「未放入場景」的熱點。

---

## 6. 注意事項
*   **環境部署**：Server 端需手動建立 `cms_secrets.py`。
*   **檔案清理**：若要重新整合，建議先刪除舊專案並清理相同 `external_form_uid` 的熱點。
