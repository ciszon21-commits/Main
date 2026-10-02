# 階段開發計畫

更新日期：2026-10-02。正式版本 0.8.7。目前完成範圍與證據見 [PROJECT_STATUS](PROJECT_STATUS.md)；知識入口見 [KNOWLEDGE_INDEX](KNOWLEDGE_INDEX.md)。依驗收門檻追蹤，不估算沒有依據的總工程百分比。

## 主線與依賴

L0 盤點 → L1 氣象／時間／資料 → L2 太陽／幾何 → L3 熱舒適 → L4 圖表 → L5 工具／維護 → 後續引擎整合。

日射可靠性、V1 UI 與發布／部署是橫向工作，隨每批功能持續驗收。依賴需要的資料／單位工具可提前做，不把目錄分類當作僵硬的開發順序。先完成 Ladybug，Eddy3D CFD 保持暫緩。

| 階段 | 目前狀態 | 已完成範圍 | 下一個交付／出口門檻 |
| --- | --- | --- | --- |
| L0 環境與完整目錄 | 已完成指定盤點 | 122 入口：119 元件、3 ValueList；參數、身分、SHA 與狀態 | 維持目錄與實際安裝一致；安裝變更時重新盤點 |
| L1 氣象、時間與資料 | 進行中；目前最高優先 | EPW、Construct Location、STAT、DDY、Analysis Period、Calculate HOY、HOY to DateTime 共 7 項 | Location 解構 → Apply Analysis Period → 資料／單位 → 設計日與剩餘氣象工具；逐項原生比較及面板驗收 |
| L2 太陽與幾何 | 部分完成 | Incident Radiation 獨立功能；Cumulative Sky Matrix 作後端 | SunPath → Direct Sun Hours／Sky Mask → Solar Envelope／剩餘幾何；幾何、單位、遮蔭及結果對齊 |
| L3 熱舒適 | 待開發 | 未接入 PMV、Adaptive、UTCI、PET、MRT 等 | 原生模型、輸入單位、適用條件、數值與錯誤路徑逐項驗收 |
| L4 圖表與呈現 | 待開發 | 現有 KPI／原生日射色樣不是完整原生圖表接入 | Psychrometric、Wind Rose／Profile、Hourly／Monthly 等；資料、圖例、標籤、縮放一致 |
| L5 工具與維護 | 待開發；部分依賴可提前 | 目錄已列資料、矩陣、網格、圖例、視圖、版本與預設選單 | 逐項驗證；下載、文件／視圖改變及版本同步須明示副作用；ValueList 驗選項與傳遞 |
| R1 日射可靠性 | 持續驗收 | 原生回歸、單位、混合幾何與遮蔭、GH 清理、4096 格平面、失敗保留結果 | 複雜大型模型、外部求解器崩潰注入及更多錯誤情境；隔離測試文件／程序 |
| U1 第一版介面 | 已交付基礎；完整驗收進行中 | 單一工作平台／六模組／六階段、主題色／圖示、Advanced、Validation、KPI、色樣、比較／匯出；當前主題 320／480 影像 | 完整 Dock、深色切換、鍵盤、picker／dialog；新功能沿用設計系統；非同步 runner 另驗證 |
| X1 平台與部署 | 進行中 | 單一平台導覽、保留模組狀態、完成資料轉移、當次方案快照／比較、JSON、版本化發布／載入 | 持久方案庫匯入、相容性、依賴與跨機安裝；公司部署尚未驗收 |
| E1 額外模擬引擎 | 延後 | Eddy3D metadata 前期盤點；CFD、採光、能耗、碳排未成為已驗證 Hub 工作流程 | Ladybug 里程碑後，個別盤點 Honeybee／Eddy3D／OpenStudio／EnergyPlus 等依賴，再做真實求解與跨引擎契約 |
| U2 第二版大型互動 UI | 功能完成後規劃 | 尚未實作；技術架構與完整互動範圍未定 | 主要功能與 V1 品質門檻驗收後，定義大型視覺互動、viewport 與方案探索，再開始實作 |

## 下一批工作的明確順序

1. **B01：LB-003 Deconstruct Location。** 重用已完成 Location 資料，增加解構操作，保留原生經緯度、時區與海拔。
2. **B02：LB-015 Apply Analysis Period。** 將已完成期間明確套用到原生 DataCollection；跨年／跨夜／次小時依型別邊界處理，不偷偷四捨五入。
3. **B03／B04：DataCollection、Header、DataType 與單位工具。** 先建立可攜契約和原生往返，再接入 Construct／Deconstruct Data、Data Type、Unit Converter。
4. **B05／B06：設計日與剩餘氣象工具。** 完成原生輸出／IDF、檔案與副作用邊界，逐項收斂 L1。
5. L1 完成後推進 L2，再依序完成 L3–L5。每批同步執行相應的日射／現有功能回歸、UI 檢查、目錄與知識更新。

詳細批次、依賴與驗收見 [LADYBUG_DEVELOPMENT_PLAN](LADYBUG_DEVELOPMENT_PLAN.md)。以上是順序與出口條件；尚未做估時或指定未確認的交付日期。

## 第一版／第二版界線

V1 持續使用 Rhino／Eto 與現有模擬核心，改善資訊架構、排版、主題色、圖示及操作流程。0.8.7 是介面交付，沒有新增功能覆蓋；目前仍為 **8 項獨立整合、1 項後端、113 項待接入**。

V2 在主要功能完成並驗收後才展開大型視覺互動介面；保留 request → preflight → adapter → result。完整 Ladybug 完成與否以 122 個入口逐項驗收狀態為準，不能以分類畫面或已安裝元件代替。
