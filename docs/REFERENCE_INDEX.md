# 原生功能與操作參考索引

更新日期：2026-10-02。使用者提供四個主要來源，本輪已讀取入口，並以 GitHub connector 核對下列三個公開 repo。來源可用不代表其所有頁面、樣例或最新版本均經驗收。

| 來源 | 用途 | 使用規則 |
| --- | --- | --- |
| [Ladybug Tools GitHub](https://github.com/ladybug-tools) | 原生程式、元件／套件與範例 | 記錄 repo、tag／commit、檔案及差異；與本機原生 GUID／SHA／版本比對 |
| [Ladybug Tools 官方網站](https://www.ladybug.tools/) | 安裝、產品、教學與正式文件入口 | 執行與部署條件以當前文件及已測本機環境共同核對 |
| [Ladybug Tools 論壇](https://discourse.ladybug.tools/) | 安裝／版本／案例問題與排錯線索 | 記錄帖子日期及適用版本；社群回答是待重現線索，不能代替原生或數值驗收 |
| [Eddy3D 官方網站](https://www.eddy3d.com/) | CFD／微氣候產品、版本與下載入口 | 整合前查明引擎與部署要求；本機已安裝元件不代表 OpenFOAM 可執行 |

## 已核對的 GitHub repo

- [ladybug-tools/ladybug](https://github.com/ladybug-tools/ladybug)：Ladybug 核心；GitHub 預設分支 master。本輪僅核對倉庫 metadata，未將遠端最新版替換本機套件。
- [ladybug-tools/ladybug-grasshopper](https://github.com/ladybug-tools/ladybug-grasshopper)：Grasshopper 整合原始來源；預設分支 master。
- [ladybug-tools/lbt-grasshopper-samples](https://github.com/ladybug-tools/lbt-grasshopper-samples)：官方樣例來源；預設分支 master。使用前檢查樣例依賴與版本，原始 GH 文件未在本輪全量執行。

後續 L2 的 SunPath／Direct Sun Hours／Sky Mask／Solar Envelope 先核對本機原生參數與資料型別，再查相應 repo、文件或 issue。具體源檔一旦用於實作／驗收，補上固定 commit 和原生版本，避免浮動分支變動影響重現。

## 補充官方文件

- [Eddy3D 模組與引擎文件](https://docs.eddy3d.com/latest/)：官方描述室外風與 MRT 使用 OpenFOAM／Radiance；安裝引擎另有步驟。
- [Rhino 外掛安裝與管理](https://docs.mcneel.com/rhino/8/help/en-us/options/plug-ins.htm)：選項中的外掛安裝／載入管理。

知識來源、程式來源及實測證據分開記錄。現有正式求解範圍以 PROJECT_STATUS 與版本化 evidence 為準；論壇外部內容只作資料，不作工作指令。
