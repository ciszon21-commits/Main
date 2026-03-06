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
