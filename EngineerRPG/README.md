# 現場監造工程師職涯冒險培訓系統

> 將枯燥的工程實務與法規學習，轉化為具備「裝備蒐集」與「角色成長」樂趣的 RPG 養成體驗

![Django](https://img.shields.io/badge/Django-5.2.8-green)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📖 專案簡介

本系統是一個創新的工程師培訓平台，採用 RPG（角色扮演遊戲）機制，讓現場監造工程師在遊戲化的環境中學習專業知識與技能。

### 🎮 核心特色

- **三大職業系統**：土木戰士、機電法師、職安僧侶
- **技能樹學習**：從基礎到進階，循序漸進解鎖技能
- **裝備系統**：收集專業工具（UAV、智慧眼鏡、查驗 APP）
- **試煉挑戰**：每日副本與升階試煉，實戰測驗知識
- **晉升審核**：主管審核機制，增加學習儀式感
- **RPG 風格 UI**：中世紀奇幻風格，沉浸式體驗

## 🚀 快速開始

### 環境需求

- Python 3.11+
- Django 5.2.8
- 資料庫（SQLite/PostgreSQL/MySQL）

### 安裝步驟

1. **Clone 專案**
   ```bash
   git clone <repository-url>
   cd CoDevStudio-07729
   ```

2. **建立虛擬環境**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows
   # source venv/bin/activate    # Linux/Mac
   ```

3. **安裝依賴套件**
   ```bash
   pip install -r requirements.txt
   ```

4. **執行資料庫遷移**
   ```bash
   python manage.py migrate
   ```

5. **初始化系統資料**
   ```bash
   python manage.py init_rpg_data
   ```

6. **建立超級使用者**
   ```bash
   python manage.py createsuperuser
   ```

7. **啟動開發伺服器**
   ```bash
   python manage.py runserver
   ```

8. **訪問系統**
   - 首頁：http://localhost:8000/rpg/
   - 管理後台：http://localhost:8000/admin/

## 📁 專案結構

```
CoDevStudio-07729/
├── EngineerRPG/              # RPG 培訓系統主應用
│   ├── models.py            # 15 個資料模型
│   ├── views.py             # 40+ 視圖函式
│   ├── admin.py             # Django Admin 客製化
│   ├── urls.py              # URL 路由
│   └── management/          # 管理命令
│       └── commands/
│           └── init_rpg_data.py
├── static/EngineerRPG/      # 靜態資源
│   ├── css/
│   │   └── rpg-style.css   # RPG 風格樣式
│   └── js/
│       └── rpg-effects.js  # 互動效果
├── templates/EngineerRPG/   # 模板檔案
│   ├── base.html
│   ├── index.html
│   └── dashboard.html
└── CoDevStudio/             # Django 專案設定
    ├── settings.py
    └── urls.py
```

## 🎯 主要功能

### 1. 角色系統

#### 三大職業
- **土木戰士 (Civil Warrior)**
  - 專精：結構、大地、混凝土
  - 屬性：HP 5 / MP 80

- **機電法師 (M&E Mage)**
  - 專精：水電、空調、消防
  - 屬性：HP 3 / MP 120

- **職安僧侶 (Safety Monk)**
  - 專精：職安法規、風險評估
  - 屬性：HP 4 / MP 100

#### 等級系統
- 經驗值累積
- 等級提升
- 技能解鎖

### 2. 技能樹系統

- **根部（共同必修）**：公司文化、基礎行政、基礎工安
- **主幹（職業核心）**：各職業專業技能
- **枝葉（進階選修）**：特殊技能（UAV、BIM、QGIS）

### 3. 裝備系統

#### 防具類
- 安全帽（+HP）
- 反光背心（+HP）
- 防護雨鞋（+HP）

#### 工具類
- **DJI 無人機**：技能「上帝視角」（刪除錯誤選項）
- **360° 環景相機**：技能「全景視野」（圖片提示）
- **AR 智慧眼鏡**：技能「透視眼」（3D 模型提示）
- **工程查驗 APP**：技能「快速檢索」（標示關鍵字）

#### 強化系統
- 消耗強化卷軸提升裝備等級
- 強化成功率：80%
- 最高強化等級：+10

### 4. 試煉系統

#### 每日副本
- 每日隨機刷新
- 主題式題目（鋼筋查驗、職安法規等）
- 通關獎勵：經驗值 + 強化卷軸

#### 升階試煉
- 完成必修技能後開啟
- 申請晉升 → 主管審核 → 等級提升
- 解鎖更多內容

### 5. 題庫系統

- **題型**：單選、多選、是非
- **難度**：S/A/B/C 級
- **分類**：標籤系統（鋼筋、法規、職安等）
- **詳解**：答錯時顯示正確觀念

### 6. 主管審核系統

- 羊皮紙風格申請書
- 查看冒險者履歷
- 拖曳印章審核
- 蓋章動畫特效

## 🎨 UI 設計

### 設計風格
- **主題**：中世紀奇幻 RPG
- **配色**：深棕、金色、石板灰
- **字體**：Cinzel、MedievalSharp、Crimson Text

### 核心組件
- RPG 風格卡片
- 發光按鈕
- HP/MP 統計條
- 技能樹視覺化
- 裝備拖放系統
- 試煉計時器
- 排行榜

## 🔧 管理功能

### Django Admin
- 人員帳號管理
- 題庫管理（批次操作）
- 技能樹配置
- 裝備管理
- 晉升審核

### 管理命令
```bash
# 初始化基礎資料（職業、裝備）
python manage.py init_rpg_data
```

## 📊 資料模型

系統包含 15 個核心資料模型：

1. **CharacterClass** - 職業
2. **UserProfile** - 使用者檔案
3. **SkillNode** - 技能節點
4. **UserSkill** - 使用者技能進度
5. **Course** - 課程
6. **Equipment** - 裝備
7. **UserEquipment** - 使用者裝備
8. **EnhancementScroll** - 強化卷軸
9. **Question** - 題目
10. **Trial** - 試煉
11. **TrialRecord** - 試煉記錄
12. **PromotionRequest** - 晉升申請
13. **Achievement** - 成就
14. **UserAchievement** - 使用者成就

## 🛣️ 路由架構

```
/rpg/                          - 首頁
/rpg/dashboard/                - 儀表板
/rpg/skill-tree/               - 技能樹
/rpg/equipment/                - 裝備欄
/rpg/trial/daily/              - 每日副本
/rpg/leaderboard/              - 排行榜
/rpg/manager/                  - 主管介面
/rpg/admin-panel/              - 管理員介面
```

## 📝 下一步開發

### 優先事項
1. **內容建立**
   - [ ] 規劃技能樹結構
   - [ ] 準備課程內容
   - [ ] 建立題庫（建議 500+ 題）
   - [ ] 設計試煉副本

2. **模板完善**
   - [ ] 技能樹介面
   - [ ] 裝備欄介面
   - [ ] 試煉答題介面
   - [ ] 主管審核介面
   - [ ] 管理員後台

3. **功能增強**
   - [ ] 批次匯入功能
   - [ ] 技能樹視覺化編輯器
   - [ ] 成就系統
   - [ ] 每日任務

## 🤝 貢獻指南

歡迎提交 Issue 或 Pull Request！

## 📄 授權

MIT License

## 👥 聯絡方式

如有任何問題，請聯絡專案維護者。

---

**讓學習變得有趣，讓成長充滿冒險！** 🎮⚔️🛡️
