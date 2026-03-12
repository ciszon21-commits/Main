# API 回傳格式參考文件

> 紀錄日期：2026-03-06  
> 用途：與外部平台 API 介接前，了解對方回傳資料格式

---

## 頂層結構

```json
{
  "success": true,
  "data": { ... }
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `success` | `boolean` | 請求是否成功 |
| `data` | `object` | 實際資料本體 |

---

## `data` 物件

| 欄位 | 類型 | 範例值 | 說明 |
|------|------|--------|------|
| `form_uid` | `string (UUID)` | `"1cbdc54d-..."` | 表單唯一識別碼 |
| `project_code` | `string` | `"6732D"` | 專案代碼 |
| `tender_code` | `string` | `"第七標"` | 標段代碼 |
| `tender_name` | `string` | `"機場捷運 A7..."` | 標段完整名稱 |
| `doc_date` | `string (YYYY-MM-DD)` | `"2026-01-22"` | 文件日期 |
| `geo_bounds` | `object` | 見下方 | 地理座標資訊 |
| `photos` | `array[object]` | 見下方 | 照片清單 |
| `workitem` | `string` | `"人行天橋工程"` | 工項名稱 |
| `first_worklayer` | `string` | `"空橋鋼構、電梯鋼構組立"` | 第一層工作層（以`、`分隔多個） |
| `second_worklayer` | `string` | `"準備作業;組立作業"` | 第二層工作層（以`;`分隔多個） |
| `assessments` | `array[object]` | 見下方 | 危害評估清單 |

---

## `geo_bounds` 物件

`type` 欄位決定座標結構，共有以下四種類型：

| `type` 值 | 說明 |
|-----------|------|
| `"單點"` | 單一座標點 |
| `"圓形"` | 圓形範圍（中心點 + 半徑） |
| `"方形"` | 矩形範圍（北南東西邊界） |
| `"多邊形"` | 多邊形範圍（多個頂點座標） |

---

### 類型一：單點

```json
{
  "type": "單點",
  "lat": 25.041182158293317,
  "lng": 121.38568062884192
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `type` | `string` | `"單點"` |
| `lat` | `float` | 緯度（WGS84） |
| `lng` | `float` | 經度（WGS84） |

---

### 類型二：圓形

```json
{
  "type": "圓形",
  "center": [25.040610172786625, 121.38583927235068],
  "radius": 17.591478381105365
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `type` | `string` | `"圓形"` |
| `center` | `array[float, float]` | 圓心座標，格式為 `[緯度, 經度]` |
| `radius` | `float` | 半徑，單位：**公尺（m）** |

---

### 類型三：方形

```json
{
  "type": "方形",
  "north": 25.041349585520205,
  "south": 25.03637039668394,
  "east": 121.51580926686786,
  "west": 121.50859905192603
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `type` | `string` | `"方形"` |
| `north` | `float` | 北邊界緯度 |
| `south` | `float` | 南邊界緯度 |
| `east` | `float` | 東邊界經度 |
| `west` | `float` | 西邊界經度 |

---

### 類型四：多邊形

```json
{
  "type": "多邊形",
  "points": [
    [25.04243875613282, 121.51975771790741],
    [25.030612957637736, 121.51186081582826],
    [25.032791479863022, 121.5255945585746]
  ]
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `type` | `string` | `"多邊形"` |
| `points` | `array[array[float, float]]` | 頂點座標陣列，每個元素格式為 `[緯度, 經度]`，至少 3 個頂點 |

---

## `photos[]` 陣列元素

```json
{
  "uuid": "c82a4097-fb64-4c16-ab41-18aad5b8fd6d",
  "name": "20260122_145506_806.jpg",
  "type": "image/jpeg",
  "url": "/media/2026/01/22/C82A4097-FB64-4C16-AB41-18AAD5B8FD6D.jpg",
  "uid": "C82A4097-FB64-4C16-AB41-18AAD5B8FD6D",
  "ext": "jpg",
  "source_archive": null
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `uuid` | `string (UUID)` | 照片唯一識別碼（**小寫**） |
| `name` | `string` | 原始檔名 |
| `type` | `string (MIME)` | MIME 類型，如 `"image/jpeg"` |
| `url` | `string` | 照片**相對路徑**，存取時需加上 Base URL |
| `uid` | `string` | 照片 UUID（**大寫**格式） |
| `ext` | `string` | 副檔名，如 `"jpg"` |
| `source_archive` | `string \| null` | 來源壓縮檔，無則為 `null` |

> ⚠️ **注意**：`uuid`（小寫）與 `uid`（大寫）代表同一張照片，需注意大小寫差異。

---

## `assessments[]` 陣列元素（危害評估）

```json
{
  "uuid": "012a601e-a7d9-47d6-befb-ae0bb693f1e5",
  "category": "environment",
  "survey_content": "熱危害",
  "hazard_status": "與高溫、低溫之接觸(中暑或熱衰竭)",
  "safety_measure": "1. 作業前...\n2. 在高溫時段...",
  "sort_order": 0
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `uuid` | `string (UUID)` | 評估項目唯一識別碼 |
| `category` | `string` | 危害類別（已知值：`"environment"` = 環境類） |
| `survey_content` | `string` | 危害調查內容，如 `"熱危害"` |
| `hazard_status` | `string` | 危害狀態描述 |
| `safety_measure` | `string (Markdown)` | 安全措施，內容為 **Markdown 格式**（含 `\n` 換行） |
| `sort_order` | `integer` | 排序順序（從 `0` 開始） |

---

## 注意事項

1. **照片 URL 為相對路徑**，介接時需拼接平台 Base URL：
   ```
   https://your-domain.com/media/2026/01/22/C82A4097-FB64-4C16-AB41-18AAD5B8FD6D.jpg
   ```

2. **`second_worklayer`** 使用 `;` 分隔，**`first_worklayer`** 使用 `、`（頓號）分隔，解析時需分別處理。

3. **`safety_measure`** 為 Markdown 格式，前端顯示前需先做渲染。

4. **`assessments`** 為陣列，一份表單可能包含**多筆**危害評估，需迭代處理。

---

## 完整範例 JSON

```json
{
  "success": true,
  "data": {
    "form_uid": "1cbdc54d-d209-4132-b652-ef06ea125b2b",
    "project_code": "6732D",
    "tender_code": "第七標",
    "tender_name": "機場捷運 A7 站地區區段徵收公共工程第七標廣場地下停車場工程",
    "doc_date": "2026-01-22",
    "geo_bounds": {
      "type": "單點",
      "lat": 25.041182158293317,
      "lng": 121.38568062884192
    },
    "photos": [
      {
        "uuid": "c82a4097-fb64-4c16-ab41-18aad5b8fd6d",
        "name": "20260122_145506_806.jpg",
        "type": "image/jpeg",
        "url": "/media/2026/01/22/C82A4097-FB64-4C16-AB41-18AAD5B8FD6D.jpg",
        "uid": "C82A4097-FB64-4C16-AB41-18AAD5B8FD6D",
        "ext": "jpg",
        "source_archive": null
      }
    ],
    "workitem": "人行天橋工程",
    "first_worklayer": "空橋鋼構、電梯鋼構組立",
    "second_worklayer": "準備作業;組立作業",
    "assessments": [
      {
        "uuid": "012a601e-a7d9-47d6-befb-ae0bb693f1e5",
        "category": "environment",
        "survey_content": "熱危害",
        "hazard_status": "與高溫、低溫之接觸(中暑或熱衰竭)",
        "safety_measure": "1. 作業前於工作區設置遮陽棚並布置陰影休息區，勞工須每30分鐘補水250ml...\n2. 在高溫時段（10:00-15:00）暫停高強度工作...",
        "sort_order": 0
      }
    ]
  }
}
```

---

## 預計介接流程分析

整個介接流程可以分為 **四個主要階段**：

### 階段一：接收轉跳與身分驗證 (Receive & Authenticate)
當使用者在對方平台點擊 Button 轉跳到我們的平台時，流程如下：
1. **接收參數**：對方轉跳過來時，網址（如 `GET` 參數）理應會帶著 `form_uid`（例如：`?form_uid=1cbdc54d-...`）。
2. **呼叫對方 API**：我們的 Backend (Django) 接收到請求後，使用對方提供的資訊，在後台發起一個 API 請求去拉取完整表單資料。
   * **Endpoint**: `https://cmservice.sinotech.com.tw/HN/api/form-basic/{FORM_UID}/`
   * **Auth**: 根據對方提供的 `API_TOKEN`、`USERNAME`、`PASSWORD`，判斷是使用 Basic Authentication 或是 Header 帶入 Bearer Token。

### 階段二：解析資料與資料庫對應 (Data Parsing & Mapping)
成功取得 JSON 資料後，我們需要將對方的資料欄位映射到我們 360 系統的資料模型 (Models) 中：

* **專案層級 (Project)**
  * `name`: `project_code` + `tender_code` + `tender_name` (例: "6732D_第七標_機場捷運...")
  * `description`: 可組合 `workitem`, `first_worklayer`, `doc_date` 等表單資訊
  * `latitude` / `longitude`: 根據 `geo_bounds.type` 決定：
    1. `"單點"`：直接取 `lat`、`lng`
    2. `"圓形"`：取 `center` 陣列的 `[0]`, `[1]`
    3. `"方形"`：取四個點位 `north`、`south`、`east`、`west` 計算平均值 `((north+south)/2, (east+west)/2)`
    4. `"多邊形"`：取 `points` 陣列中所有點的經度與緯度平均值
* **場景層級 (Scene)**
  * **當有多張照片時，會建立多個 Scene，但危害評估熱點只統一加在「第一張照片」對應的 Scene 上**。
  * `title`: `workitem` + " - " + `first_worklayer`
  * `image`: 將 `photos[i].url` 下載後存入
* **熱點層級 (Hotspot)** (只加在首張 Scene)
  * `title`: `assessments[i].survey_content`
  * `description`: 組合 `hazard_status` 與 `safety_measure`
  * `pitch` / `yaw`: 自動給定預設值。為了避免重疊，可以在建立時根據 index 稍微偏移（例如第一個 `yaw=0`, 第二個 `yaw=30`...）。
  * 取 `assessments[i].category` 作為危害類別：
    * 檢查系統的 `HazardType` 是否有包含此名稱。
    * **若無，則自動新增該 `HazardType`。**
    * 接著將該 `HazardType` 關聯至 `Hotspot` 的 `hazard_types` (ManyToManyField)。

### 階段三：自動化建立流程演算法 (Automated Creation Logic)
在 Backend 進行的業務邏輯處理：

1. **Get or Create 專案 (Project)**
   * 根據 `project_code` 或 `tender_code` 查詢資料庫。如果專案已存在則取得該實例；若不存在，則自動新建一個 360 Project。
2. **下載與處理圖片 (Process Photos)**
   * 針對 `data.photos` 陣列進行迭代。
   * **圖片下載**：使用腳本組合完整網址發起 Request 下載圖片實體檔案。
   * （建議：這段使用背景任務 (如 Celery) 或是先快速建立草稿狀態）。
3. **建立 360 場景 (Create Scenes)**
   * 將下載好的圖片存入。
   * 在資料庫中新建「場景實例」，並將經緯度 `geo_bounds` 寫入該場景，讓照片可以在地圖上正確定位。
4. **自動建立危害評估熱點 (Create Hazard Hotspots)**
   * 讀取 `data.assessments`。
   * 將 `survey_content`、`hazard_status`、`safety_measure` 結合起來，在剛剛建立的場景中，自動生成（或附加）相關的 Info Hotspots 或 Hazard 標記。

### 階段四：前端呈現 (Frontend Rendering)
1. 後台自動建立完成後，Django 回傳一個 Redirect，將使用者的瀏覽器導向我們平台該 Project 或該 Scene 的 360 檢視頁面。
2. 使用者一進來，就能直接看到對方傳來的圖片已經變成 360 全景，並且畫面上已經帶有對應的危害評估熱點。

---

### 開發前需釐清事項

1. **Authentication Mode**：確認呼叫 API 時的 Header 驗證方式。
2. **圖片格式**：確認傳來的圖片是否都是 2:1 的 360 等距柱狀投影圖 (Equirectangular)。
3. **單點 VS 多點照片**：若提供單點範圍卻有多張照片，是否預設堆疊在同個座標。
4. **背景處理機制**：若高畫質照片多，考慮轉跳當下非同步處理以免 Timeout。
