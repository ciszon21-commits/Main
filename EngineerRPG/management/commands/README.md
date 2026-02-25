# 資料庫初始化 Commands 使用說明

## 快速開始

### 在生產環境中初始化資料庫

```bash
# 1. 執行資料庫遷移
python manage.py migrate

# 2. 初始化所有資料（一鍵完成）
python manage.py init_all_data

# 3. 驗證資料
python verify_init_data.py
```

## 可用的 Commands

### 統一初始化（推薦）

```bash
# 初始化所有資料（職業、技能樹、裝備、題庫、課程）
python manage.py init_all_data

# 清除所有資料後重建
python manage.py init_all_data --clear
```

### 個別初始化

```bash
# 初始化題庫（119題，4個分類）
python manage.py init_questions
python manage.py init_questions --clear  # 清除後重建

# 初始化課程（6個課程）
python manage.py init_courses
python manage.py init_courses --clear  # 清除後重建

# 初始化技能樹（36個技能節點）
python manage.py init_skill_tree_v2

# 初始化裝備（13個裝備）
python manage.py populate_equipment_v2

# 初始化職業（3個職業）
python manage.py init_rpg_data
```

### 匯出資料（維護用）

```bash
# 匯出題庫資料
python manage.py export_questions

# 匯出課程資料
python manage.py export_courses
```

## 初始化的資料

| 資料類型 | 數量 | 說明 |
|---------|------|------|
| 職業 | 3個 | 土木戰士、機電法師、職安僧侶 |
| 技能節點 | 36個 | 共同必修7個、職業核心15個、進階選修14個 |
| 裝備 | 13個 | 頭盔3個、盔甲3個、靴子3個、工具4個 |
| 題目分類 | 4個 | 品質管理、工務行政、施工管理、職安衛 |
| 題目 | 119題 | A級14題、B級61題、C級44題 |
| 課程 | 6個 | 包含新進訓練、PMIS課程、監造計畫等 |

## 驗證工具

```bash
# 驗證所有資料是否正確初始化
python verify_init_data.py

# 檢查資料庫內容
python check_db_data.py
```

## 維護說明

### 更新題庫

1. 在 Django Admin 中修改題目
2. 執行匯出：`python manage.py export_questions`
3. 提交 `EngineerRPG/management/commands/init_questions_data.py` 到版本控制

### 更新課程

1. 在 Django Admin 中修改課程
2. 執行匯出：`python manage.py export_courses`
3. 提交 `EngineerRPG/management/commands/init_courses_data.py` 到版本控制

## 檔案位置

- Commands: `EngineerRPG/management/commands/`
- 資料檔案: `EngineerRPG/management/commands/init_*_data.py`
- 驗證工具: 專案根目錄的 `verify_init_data.py` 和 `check_db_data.py`
