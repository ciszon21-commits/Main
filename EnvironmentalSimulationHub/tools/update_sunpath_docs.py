"""Advance current documents/catalog only after versioned native acceptance."""
import json,re,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];docs=root/'docs'
assert json.loads((docs/'evidence/sunpath_090_runtime.json').read_text(encoding='utf-8'))['passed']==31
assert json.loads((docs/'evidence/workspace_090_runtime.json').read_text(encoding='utf-8'))['passed']==14
assert len(json.loads((docs/'evidence/ui_090/capture.json').read_text(encoding='utf-8'))['shots'])==30
def write(p,s):p.write_text(s,encoding='utf-8')
catalog_path=docs/'evidence/ladybug_feature_catalog.json';catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
entry=next(x for x in catalog['components'] if x['id']=='LB-057')
entry.update(hub_status='已接入並實測',integration_scope='0.9.0：太陽位置／向量、曲線／文字、地點／分鐘 HOY、北向角、模型尺度、中心、日弧及四投影。',pending_options=['data_','statement_','legend_par_','dl_saving_','north_ vector','vis_set UI'],evidence=['sunpath_090_runtime.json','sunpath_090_transfer.json'])
assert len(catalog['components'])==122 and sum(x['hub_status']=='已接入並實測' for x in catalog['components'])==9
write(catalog_path,json.dumps(catalog,ensure_ascii=False,indent=2))
p=docs/'LADYBUG_FEATURE_TABLE.md';s=p.read_text(encoding='utf-8');s='\n'.join(line.replace('待接入 Hub','已接入並實測（幾何第一批）') if '| LB SunPath |' in line else line for line in s.split('\n'))
s=s.replace('HOY to DateTime，仍未接入全部元件','HOY to DateTime，仍未接入全部元件')
s=s.replace('目前 0.7.2 Hub','目前 0.9.0 Hub').replace('與 HOY to DateTime','、HOY to DateTime 與 SunPath 幾何第一批')
if 'SunPath 支援邊界' not in s:s=s.replace('\n## ', '\nSunPath 支援邊界：9 項獨立／1 後端／112 待接入。LB-057 未含氣象著色、條件篩選、夏令時間及自訂圖例，見 [SUNPATH_MODULE.md](SUNPATH_MODULE.md)。\n\n## ',1)
write(p,s)
p=docs/'LADYBUG_FEATURE_TABLE.html';s=p.read_text(encoding='utf-8');data=json.dumps(catalog['components'],ensure_ascii=False).replace('<','\\u003c')
s,n=re.subn(r'const entries=.*?;const box=',lambda _:'const entries='+data+';const box=',s,count=1,flags=re.S);assert n==1
s=s.replace('<body>','<body><p>0.9.0：9 項獨立、1 項後端、112 待接入。SunPath 僅完成幾何第一批；氣象著色、條件篩選、夏令時間與自訂圖例尚未接入。<a href="SUNPATH_MODULE.md">支援範圍</a></p>',1)
write(p,s)
# Preserve the previous current-state document as a versioned snapshot.
history=docs/'history/PROJECT_STATUS_087.md'
if not history.exists():write(history,(docs/'PROJECT_STATUS.md').read_text(encoding='utf-8'))
p=docs/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8')
s=s.replace('正式版本 **0.8.7**；本輪單一工作平台已建置並在新 Rhino 程序驗收','正式版本 **0.9.0**；本輪加入 SunPath 幾何功能並在新 Rhino 程序驗收')
s=s.replace('8 項已接入並實測','9 項已接入並實測').replace('113 項','112 項').replace('1 個原生面板、6 個內部模組','1 個原生面板、7 個內部模組').replace('首頁、氣象、地點、STAT／DDY、時間、日射 |','首頁、氣象、地點、STAT／DDY、時間、日射、太陽路徑 |')
s=s.replace('八項功能位於','九項功能位於').replace('0.8.7 小範圍內部試用','0.9.0 小範圍內部試用').replace('正式二進位未變，試用包輸出改用使用者目錄','新版試用包與正式版二進位相同，試用包輸出改用使用者目錄')
s=s.replace('release_087_loaded.json、platform_087_runtime.json','release_090_loaded.json、platform_090_runtime.json').replace('| release_087_loaded.json |','| release_090_loaded.json |').replace('| release_087_loaded.json、weather_runtime_validation.json |','| release_090_loaded.json、weather_runtime_validation.json |')
s=s.replace('\n九項功能位於','\n| LB-057 · LB SunPath | EnvironmentalSunPath；位置、向量、曲線、文字與四投影；[支援邊界](SUNPATH_MODULE.md) | sunpath_090_runtime.json、sunpath_090_transfer.json |\n\n九項功能位於')
a=s.index('## 0.8.7 單一工作平台');b=s.index('## 已知限制',a)
section='''## 0.9.0 太陽路徑與单一工作平台

- SunPath 沿用六階段、中文、主題色與向量圖示；一般地點／日期／北向／半徑，進階時區／中心／投影／真太陽時。地點、EPW 與時間資料只能由完成結果明確傳入。
- 原生曲線、羅盤文字、太陽點與日照方向線；結果顯示高度角、方位角、地平線以下時刻、模型單位與時間制。定位或清除只處理本模組預覽。
- 只註冊 HubWorkspacePanel，七個內部模組／七個指令均導向同一面板，切換保留草稿、完成結果及比較方案。
- 新增 Core 契約與 Adapter；既有 Core／Adapter 求解檔案未修改。不能稱為全部 DLL 未變或完整 SunPath 選項完成。

| 驗證 | 結果 | 證據 |
| --- | --- | --- |
| 建置／正式載入 | 0 錯誤、0 警告；新專用 Rhino 程序載入 0.9.0，註冊路徑更新 | [載入](evidence/release_090_loaded.json)、[發布 manifest](evidence/release_090_manifest.json) |
| SunPath 原生／操作 | 31＋1 項；12 組原生角度、向量、曲線與文字比較，四投影／單位／失敗／資料轉移／owned preview | [模組驗證](evidence/sunpath_090_runtime.json)、[EPW 地點](evidence/sunpath_090_transfer.json) |
| 七模組整合 | 14 項；七指令、路由、六首頁入口、狀態保留、關閉重開 | [平台驗證](evidence/workspace_090_runtime.json) |
| 既有數值／流程 | 60 項，合計 106 項原生數值／操作；日射平均 1233.3471168086037 kWh/m² | [載入／數值](evidence/release_090_loaded.json)、[日射平台](evidence/platform_090_runtime.json) |
| 版面 | 30 張 320／480 px，當前淺色原生控制項離屏呈現 | [擷取範圍](evidence/ui_090/capture.json)、[SunPath 結果](evidence/ui_090/sunpath_results_320.png) |

完整 Dock、深色切換、鍵盤、原生 picker／file dialog、不同文件切換與大型分鐘取樣預覽效能仍需完整驗收。単一平台的 Dock 識別及關閉重開已實測；影像是離屏正式控制項，不能視為完整宿主驗收。歷史大型模型與全部舊單位案例未重跑。[0.8.7 快照](history/PROJECT_STATUS_087.md) 保留以前的驗收界線。

'''.replace('单一','單一').replace('単一','單一')
s=s[:a]+section+s[b:];s=s.replace('現在優先 L2 SunPath → Direct Sun Hours → Sky Mask → Solar Envelope','SunPath 幾何第一批已完成，下一優先 Direct Sun Hours → Sky Mask → Solar Envelope；SunPath 選項按依賴補齊')
write(p,s)
for filename in ['ROADMAP.md','LADYBUG_DEVELOPMENT_PLAN.md','QUICK_START.md','PILOT_ACCEPTANCE.md','BUILD_AND_RUN.md','KNOWLEDGE_INDEX.md']:
 p=docs/filename;s=p.read_text(encoding='utf-8')
 # These are current operational/plan documents, not historical receipts.
 s=s.replace('0.8.7','0.9.0').replace('Release087','Release090').replace('release_087_loaded','release_090_loaded')
 s=s.replace('8 項獨立','9 項獨立').replace('8 項獨立整合','9 項獨立整合').replace('113 項','112 項').replace('六模組','七模組')
 s=s.replace('0.9.0 改善 UI，沒有增加功能完成數。','0.9.0 增加 SunPath 幾何第一批，完整選項未全部接入。')
 s=s.replace('0.9.0 是介面交付，沒有新增功能覆蓋','0.9.0 增加 SunPath 幾何第一批')
 s=s.replace('HOY to DateTime。Cumulative','HOY to DateTime、SunPath 幾何第一批。Cumulative')
 s=s.replace('Incident Radiation 獨立功能；Cumulative','Incident Radiation 及 SunPath 幾何第一批；Cumulative').replace('Incident Radiation 已獨立驗證；其餘 SunPath、','Incident Radiation 及 SunPath 幾何第一批已驗證；其餘 ')
 s=s.replace('SunPath → Direct Sun Hours','SunPath 幾何第一批已完成 → Direct Sun Hours').replace('新功能仍待開發；不是本輪已完成內容。','SunPath 幾何第一批已完成；後三項與其餘 SunPath 選項仍待接入。')
 s=s.replace('**V01：LB-057 SunPath**，重用已有地點／時間，交付原生太陽位置、路徑、向量與必要條件資訊。','**V01：LB-057 SunPath 幾何第一批已交付**；原生位置、路徑、向量與條件資訊，未接入選項見 SUNPATH_MODULE.md。下一批 V02。')
 write(p,s)
p=docs/'L2_VISUAL_PLAN.md';s=p.read_text(encoding='utf-8').replace('以下新功能均未接入，正式功能數仍為 8 獨立、1 後端、113 待接入。','V01 SunPath 幾何第一批已在 0.9.0 接入並實測；正式功能數為 9 獨立、1 後端、112 待接入。未完成選項見 [SUNPATH_MODULE.md](SUNPATH_MODULE.md)，V02 為下一個交付。').replace('| V01 |','| V01 · 幾何第一批已交付 |');write(p,s)
p=docs/'QUICK_START.md';s=p.read_text(encoding='utf-8');s+='''
## 先快速檢視太陽路徑

輸入 EnvironmentalSunPath，在同一面板確認版本 0.9.0。設定所在地點／UTC 時區；亦可使用已完成的 EPW 地點。預設日期 6/21 12:00、半徑 20 m、北向 0°，按「檢核並建立太陽路徑」，在結果選時刻、檢視角度並定位預覽。先讀 SUNPATH_MODULE.md 的時間制、北向與支援邊界；此流程不需要 Radiance 求解，但仍需要原生 Ladybug／GH Python 環境。更換文件或單位後用「綁定目前文件／重設中心」。
''';write(p,s)
p=docs/'PILOT_ACCEPTANCE.md';s=p.read_text(encoding='utf-8');s+='\n0.9.0 新試用項：EnvironmentalSunPath 正確出現在同一平台；完成地點／時間傳入、角度／單位讀取、定位與只清除預覽；錯誤輸入保留前次結果。跨機原生功能與無協助操作仍待同仁實測。\n';write(p,s)
p=docs/'KNOWLEDGE_INDEX.md';s=p.read_text(encoding='utf-8').replace('186 筆紀錄','188 筆紀錄');s+='\nSunPath 操作、第一批支援邊界及驗證來源：[SUNPATH_MODULE.md](SUNPATH_MODULE.md)。新版接受證據：[sunpath_090_acceptance.json](evidence/sunpath_090_acceptance.json)。歷史版本文件與 receipts 不更動。\n';write(p,s)
p=docs/'DEVELOPMENT_LOG.md';s=p.read_text(encoding='utf-8');s+='\n## 2026-10-02 · 0.9.0 SunPath 幾何第一批\n\n新增原生 LB SunPath 契約／Adapter／中文內部模組，7 指令在同一 Dock；32 SunPath＋60 既有＋14 平台，共 106 原生數值／操作檢查；30 張當前淺色影像。9 獨立／1 後端／112 待接入。新增完整選項邊界，下一項 Direct Sun Hours。原生檔案未修改；Core／Adapter 新增檔案而非整個 DLL 不變。跨機／完整 UI 仍待驗收。\n';write(p,s)
for filename in ['ARCHITECTURE.md','UI_UX_STANDARD.md','PLATFORM_UI.md','REFERENCE_INDEX.md','DEVELOPMENT_REVIEW_2026-10-01.md']:
 p=docs/filename;s=p.read_text(encoding='utf-8');s+='\n## 2026-10-02 更新 · 0.9.0\n\n目前為 9 獨立功能、1 後端、112 待接入；SunPath 幾何第一批透過新增契約與原生 Adapter 接入第七個內部模組。原有求解檔案保留。32＋60＋14 共 106 項原生檢查；30 張目前淺色 320／480 px 離屏影像。SunPath 未含氣象著色／條件／夏令時間／圖例等完整選項，見 [SUNPATH_MODULE.md](SUNPATH_MODULE.md)。下一項 Direct Sun Hours；跨機、完整 Dock／theme／keyboard／dialogs 驗收未閉合。本文前段版本記錄保留原驗收範圍，最新狀態以 PROJECT_STATUS.md 為準。\n';write(p,s)
p=root/'README.md';s=p.read_text(encoding='utf-8').replace('0.8.7','0.9.0').replace('Release087','Release090');s+='\n0.9.0 adds EnvironmentalSunPath within the same workspace: original geometric SunPath, positions/vectors, four projections and safe owned preview. See docs/SUNPATH_MODULE.md for supported/deferred options and 106 native checks. Coverage: 9 standalone, 1 backend, 112 pending.\n';write(p,s)
print('Updated current catalog and documents: 9 / 1 / 112')
