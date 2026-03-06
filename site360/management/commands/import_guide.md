# 360 平台資料匯入操作說明

> 作者收到以下資料後，請依序執行下方步驟。

---

## 你會收到的資料

| 檔案 / 資料夾 | 說明 |
|---|---|
| `危害類型定義.xlsx` | 危害類型主資料 |
| `360預設資料庫整理.xlsx` | 預設熱點主資料 |
| `台北勞檢/` | 圖片資料夾 |
| `桃園勞檢/` | 圖片資料夾 |
| `職安署/` | 圖片資料夾 |

請將上述 Excel 與圖片資料夾放在同一個上層目錄，例如：

```
C:\import_data\
├── 危害類型定義.xlsx
├── 360預設資料庫整理.xlsx
├── 台北勞檢\
├── 桃園勞檢\
└── 職安署\
```

---

## STEP 1 — 匯入危害類型（HazardType）

開啟 `site360/management/commands/import_hazard_types.py`，
修改頂部路徑變數：

```python
DEFAULT_EXCEL_PATH = r"C:\import_data\危害類型定義.xlsx"
```

執行：

```bash
python manage.py import_hazard_types --dry-run   # 預覽確認
python manage.py import_hazard_types             # 正式匯入
```

預期結果：`🎉 匯入完成！新增: 22 筆`

---

## STEP 2 — 匯入預設熱點圖片與資料（PresetHotspot）

開啟 `site360/management/commands/import_preset_hotspots.py`，
修改頂部路徑變數：

```python
DEFAULT_EXCEL_PATH   = r"C:\import_data\360預設資料庫整理.xlsx"
DEFAULT_IMAGES_ROOT  = r"C:\import_data"   # 圖片資料夾的上層目錄
```

執行：

```bash
python manage.py import_preset_hotspots --dry-run   # 預覽確認
python manage.py import_preset_hotspots             # 正式匯入
```

預期結果：`🎉 匯入完成！資料庫：新增 99 筆 | 圖片：複製成功 99 張`

> ⚠️ 執行完成後，圖片會被複製到 `media/site360/preset_hotspots/` 目錄下。
> 部分危害類型若為組合型（如「被撞、物體飛落」），關聯欄位會留空，屬正常現象。

---

## STEP 3 — 將 PresetHotspot 寫入 Hotspot（資源庫）

此步驟不需修改路徑，直接執行：

```bash
python manage.py import_preset_to_hotspot --dry-run   # 預覽確認
python manage.py import_preset_to_hotspot             # 正式匯入
```

預期結果：`🎉 匯入完成！新增：99 筆`

> **規則說明：**
> - 有圖片的 PresetHotspot → Hotspot 類型設為 `image_hover`（懸浮圖片）
> - 重複執行安全（已存在的資料不會再新增，除非加 `--overwrite`）
> - 圖片**不會重複複製**，Hotspot 與 PresetHotspot 共用同一個實體檔案

---

## 完整執行流程（快速參考）

```bash
# STEP 1
python manage.py import_hazard_types

# STEP 2
python manage.py import_preset_hotspots

# STEP 3
python manage.py import_preset_to_hotspot
```

---

## 驗證

完成後可至 Django Admin 確認資料：

| 路徑 | 確認項目 |
|---|---|
| `/admin/site360/hazardtype/` | 22 筆危害類型 |
| `/admin/site360/presethotspot/` | 99 筆預設熱點（含圖片縮圖） |
| `/admin/site360/hotspot/` | 99 筆 Hotspot（scene=None，type=image_hover） |
