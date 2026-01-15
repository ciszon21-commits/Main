# Sino360 開發者說明文件

## 專案架構
Sino360 是一個 Django App，結構如下：
- `models.py`: 定義 `Project` (專案) 與 `Scene` (場景) 模型。
- `views.py`: 包含列表 (`ProjectListView`)、詳細頁 (`ProjectDetailView`) 與全景瀏覽 (`tour_view`) 的視圖。
- `urls.py`: 定義 URL 路由。
- `templates/site360/`: 前端模板，使用 Django Template Language。

## 技術細節
- **前端核心**: 使用 [Pannellum.js](https://pannellum.org/) 進行 360 全景渲染。
- **資料介接**: `views.project_tour_data` 負責將資料庫中的場景轉換為 Pannellum 所需的 JSON 格式。
- **依賴套件**:
    - `Django`
    - `Pillow` (圖片處裡)
    - `django-cors-headers` (若有跨域需求)

## 安裝與設定
1. 確保 `requirements.txt` 中的套件已安裝。
2. 在 `settings.py` 的 `INSTALLED_APPS` 加入 `'site360'`。
3. 執行 Migrations:
   ```bash
   python manage.py makemigrations site360
   python manage.py migrate
   ```

## 自定義開發
### 修改全景設定
若需調整初始視角或熱點邏輯，請修改 `views.py` 中的 `project_tour_data` 函式。目前預設在 `yaw=0` (前方) 與 `yaw=180` (後方) 加上跳轉熱點。

### 新增轉場效果
Pannellum 內建 `sceneFadeDuration` 參數 (目前設定為 1000ms)，可於 JSON config 中調整。

## 待辦事項
- 實作前端上傳介面 (目前僅支援 Admin 上傳)。
- 支援更複雜的熱點編輯器 (Hotspot Editor)。
