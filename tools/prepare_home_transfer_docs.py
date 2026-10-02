"""Record the exact unfinished release state before a project-only transfer."""
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime, timezone

root = Path(__file__).resolve().parents[1]
docs = root / 'docs'
evidence = docs / 'evidence'


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')


def load(name):
    return json.loads(read(evidence / name))


def prepend(path, marker, text):
    current = read(path)
    if marker not in current:
        write(path, text + '\n\n' + current)


loaded = load('release_0101_loaded.json')
names = ['platform_0101_runtime.json', 'sunpath_0101_runtime.json', 'sunpath_0101_text.json',
         'sunpath_0101_transfer.json', 'workspace_0101_runtime.json', 'sunhours_0101_runtime.json']
counts = {n: load(n)['passed'] for n in names}
total = sum(counts.values()) + sum(len(loaded[k]) for k in ['location_cases', 'climate_cases', 'time_cases'])
assert total == 154
assert len(load('ui_0101/capture.json')['shots']) == 44
assert len(load('ui_0101/viewport_capture.json')['paths']) == 2
assert '<AssemblyVersion>0.10.2.0</AssemblyVersion>' in read(root / 'src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj')
for version in ['0.9.2', '0.10.1']:
    release = root / 'artifacts/releases' / version
    manifest = json.loads(read(release / 'release_manifest.json'))
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((release / name).read_bytes()).hexdigest().lower() == digest.lower(), (version, name)

release = root / 'artifacts/releases/0.10.2'
build_files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in release.iterdir()
               if p.suffix in ('.dll', '.rhp', '.json') and p.name != 'release_manifest.json'}
manifest = {'version': '0.10.2', 'plugin': 'EnvironmentalHub.Plugin.rhp',
            'plugin_id': 'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f',
            'acceptance': 'BUILD_ONLY; native load/runtime/UI replay pending', 'files': build_files,
            'registered': False, 'home_runtime': 'NOT_TESTED'}
write(release / 'release_manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
write(evidence / 'release_0102_build_manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

status = {'recorded_at': datetime.now(timezone.utc).isoformat(),
          'last_accepted_release': '0.9.2', 'registered_source_candidate': '0.10.1',
          'source_candidate_native_checks': total, 'source_candidate_native_evidence': counts,
          'source_candidate_ui_captures': 44, 'source_candidate_real_viewport_captures': 2,
          'source_candidate_ui_accepted': False,
          'source_candidate_ui_defects': ['SunHours legend swatches stretched; numeric h labels pushed offscreen',
                                         'SunHours numeric inputs displaced by shared DynamicLayout columns'],
          'current_source_version': '0.10.2', 'build_errors': 0, 'build_warnings': 0,
          'current_source_native_load': 'NOT_TESTED', 'current_source_ui_replay': 'NOT_TESTED',
          'formal_coverage': {'standalone': 9, 'backend': 1, 'pending': 112},
          'candidate_coverage': {'standalone': 10, 'backend': 1, 'pending': 111},
          'notion': {'last_verified_records': 190, 'last_synced_version': '0.9.2', 'handoff_sync': 'PENDING'},
          'heartbeat': 'NOT_CREATED: creation was cancelled',
          'transfer': 'Project-only snapshot preparation; destination/home runtime not yet verified'}
write(evidence / 'handoff_20261002_status.json', json.dumps(status, ensure_ascii=False, indent=2) + '\n')

history = docs / 'history/PROJECT_STATUS_092.md'
if not history.exists():
    write(history, read(docs / 'PROJECT_STATUS.md'))

summary = '''## 2026-10-02 · 家用移轉交接狀態

正式已交付基準仍為 **0.9.2（9 獨立／1 後端／112 待正式接入）**。日照時數 LB-061 已加入第八個內部模組；0.10.1 候選的 45 項新功能及 109 項其他原生／平台檢查合計 **154 項通過**，候選接入數為 10／1／111。44 張離屏 UI 與 2 張真正 3D 圖已擷取，但窄版色樣／數值欄位排版缺陷尚未正式驗收。

**目前程式碼為 0.10.2**：已分離圖例、參數與說明的欄寬，Build 0 錯誤／0 警告；**尚未註冊、載入或完成原生與 UI 複驗**。因使用者要求安全轉回家用電腦，停止新增功能，先整理並打包。0.10.1 的結果不能代替 0.10.2 或家用機驗收。

[安全移轉／交接](HOME_TRANSFER.md) · [回家後接續指令](HOME_CONTINUE_PROMPT.md) · [日照時數候選範圍](SUN_HOURS_MODULE.md) · [交接證據](evidence/handoff_20261002_status.json)

Notion 最後已同步仍為 190 筆／0.9.2；本輪候選及交接待同步。定時回報建立曾取消，尚無本專案已啟用 heartbeat。以下 0.9.2 表格保留正式基準與原驗收範圍。'''
prepend(docs / 'PROJECT_STATUS.md', '家用移轉交接狀態', summary)
prepend(root / 'README.md', 'HOME_TRANSFER.md', '''# 家用電腦開發交接 · 2026-10-02

先讀 [安全移轉](docs/HOME_TRANSFER.md) 與 [接續指令](docs/HOME_CONTINUE_PROMPT.md)。來源目前為 0.10.2，僅建置通過；0.10.1 原生 154 項通過但 UI 未完成驗收。正式基準仍是下文 0.9.2。快照包含未提交新程式碼，沒有父儲存庫其他專案的 Git 歷史、憑證或 Rhino 安裝環境。''')
prepend(docs / 'KNOWLEDGE_INDEX.md', 'HOME_TRANSFER.md', '''## 目前交接入口

[HOME_TRANSFER.md](HOME_TRANSFER.md) 是家用安全接收與版本狀態入口；[HOME_CONTINUE_PROMPT.md](HOME_CONTINUE_PROMPT.md) 可交给家用 Codex。[SUN_HOURS_MODULE.md](SUN_HOURS_MODULE.md) 記錄候選日照時數範圍。0.10.2 僅建置，原生 154 項屬 0.10.1；以下歷史索引不能視為新版本已驗收。''')
prepend(docs / 'BUILD_AND_RUN.md', 'HOME_TRANSFER.md', '''## 家用開發優先讀此

依 [HOME_TRANSFER.md](HOME_TRANSFER.md) 做唯讀環境檢查、建置至新 home-build 資料夾。不要直接重播原機 *_calls.json、匯入 registry backup 或執行下文的原機升版腳本。0.10.2 僅完成 Build，跨機及原生/UI 複驗待完成。''')
for name in ['ROADMAP.md', 'LADYBUG_DEVELOPMENT_PLAN.md', 'L2_VISUAL_PLAN.md']:
    prepend(docs / name, '家用移轉前交接', '''## 2026-10-02 家用移轉前交接

V02 Direct Sun Hours 已在 0.10.1 候選接入並完成原生比較；窄版 UI 有缺陷。0.10.2 已修正並建置，但尚未原生／視覺複驗。先完成 [安全移轉及新機驗收](HOME_TRANSFER.md)，再交付 V02、更新正式功能目錄／Notion；之後才開始 V03 Sky Mask。下面原計畫保留功能、依賴與原驗收門檻。''')

write(docs / 'SUN_HOURS_MODULE.md', '''# 日照時數 · LB-061 候選開發紀錄

2026-10-02。0.10.1 原生驗證通過，窄版 UI 尚未交付；0.10.2 排版修正只有 Build。家用接續見 [HOME_TRANSFER.md](HOME_TRANSFER.md)。

## 已接入範圍

原生 LB Direct Sun Hours 1.10.0，透過原生 SunPath 重算完成的地點／HOY／北向／時間制；不由外部任意向量取代。分析 Brep／Mesh、外部遮蔭、網格 m、感測點偏移 m、自遮蔭、CPU 及每小時步數。輸入檢核、夜間／錯誤處理、前次結果保留、原生面色樣、h 的最小／最大／平均／格點數、專案目標、session 方案、比較與 JSON 匯出。僅註冊既有 HubWorkspacePanel，第八個內部模組與 EnvironmentalSunHours 指令。

每小時步數支援 1、2、3、4、5、6、10、12、15、20、30、60；先檢查完整非閏年分钟 HOY 序列，再由原生 SunPath 排除夜間。單一樣本依明確步數加權，期間端點作取樣樣本計數，不把端點數冒充曆時長度；不支援不相容的稀疏或不規則序列。Brep 依間距網格化；Mesh 依既有面取樣，不細分。全夜間來源拒絕，不能編造零時數。

## 數據與視埠

保留原生 mesh colors、values、points；預覽沿法線 0.002 m 顯示偏移避免共面閃爍，匯出保留未位移原生網格及獨立 Presentation 設定。顯示網格開關、只暫時隱藏帶有 Hub owner userstring 的其他預覽；退出／清除還原。使用者同名物件不視為 Hub 預覽，不隱藏或刪除。更換文件／單位會阻止不相容請求。

比較只有相同 SunSource SHA、原生 SunPath／SunHours 元件 SHA 才显示平均差值；其他方案顯示條件不一致。格點平均不是面積加權，不等於性能改善。最多 20 個不重名 session 方案；關閉 Rhino 前須匯出。目標區間是包含邊界的使用者設定，不是日照法規合規。

## 已驗證及待複驗

- 0.10.1：13 組獨立 stock 比較＋15 類無效輸入＋17 項 UI／owned preview 操作，共 45 項；與其他模組合計 154。
- 原生比較含全遮蔭、局部遮蔭、夜間過濾、半小時／單一四分之一小時、北向、真太陽時、南半球、Mesh 面朝向及 mm／m 單位。
- 44 張原生控制項離屏擷取並不等於全部 UI 通過：結果色樣、h 標籤與數值欄位窄版有缺陷。0.10.2 已用巢狀獨立欄位列修正，尚待新機重新擷取／檢視。
- 2 張真正 3D 視埠已檢視。臺北 06–18 時範例 256 格，7–13 h，平均 9.08203125 h；第二張暫時隱藏 canopy 供 QA，並非新增使用者模型可見性控制。不是正式案場或法規成果。

證據：`evidence/sunhours_0101_runtime.json`、`evidence/ui_0101/capture.json`、`evidence/ui_0101/viewport_capture.json`、`evidence/release_0102_build_manifest.json`。新機 receipts 必須新增，不覆寫歷史。

## 未完成

完整原生 int_mtx、自訂 legend/title 介面、持久方案匯入、可靠取消／百分比進度，以及完整 Dock／深色／鍵盤／原生對話框／跨機驗收。求解仍同步於 Rhino UI，先用短期間和粗網格試算。Direct Sun Hours 不需要 Radiance；日射模組仍需 Radiance。原生 ghuser 不打包也不修改。
''')

catalog_path = evidence / 'ladybug_feature_catalog.json'
catalog = json.loads(read(catalog_path))
entry = next(e for e in catalog['components'] if e['id'] == 'LB-061')
entry.update(candidate_version='0.10.1', candidate_source_version='0.10.2',
             candidate_status='已接入／原生實測通過；正式 UI 與新版本複驗待完成',
             candidate_evidence=['sunhours_0101_runtime.json', 'handoff_20261002_status.json'],
             candidate_scope='幾何／遮蔭、原生 SunPath 來源、時間步數、網格、原生面色樣、h 統計、專案目標、預覽定位／可見性、session 比較及 JSON；int_mtx／自訂 legend/title 待接入。')
assert len(catalog['components']) == 122
assert sum(e['hub_status'] == '已接入並實測' for e in catalog['components']) == 9
write(catalog_path, json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
table = docs / 'LADYBUG_FEATURE_TABLE.md'
s = read(table)
s = '\n'.join(line.replace('待接入 Hub', '候選已接入／原生實測；待正式 UI 驗收') if '| LB-061 |' in line else line for line in s.split('\n'))
write(table, s)
prepend(table, '候選交接註記', '''候選交接註記（2026-10-02）：正式 9／1／112 保留；LB-061 在 0.10.1 候選已原生實測，0.10.2 只有排版修正 Build，待正式 UI／新機驗收。[完整候選範圍](SUN_HOURS_MODULE.md)。''')
html = docs / 'LADYBUG_FEATURE_TABLE.html'
s = read(html)
data = json.dumps(catalog['components'], ensure_ascii=False).replace('<', '\\u003c')
s, n = re.subn(r'const entries=.*?;const box=', lambda _: 'const entries=' + data + ';const box=', s, count=1, flags=re.S)
assert n == 1
needle = "if(e.preset_items.length)"
addition = "if(e.candidate_status){detail.append(text('h3','候選開發狀態'),text('p',e.candidate_status+' · '+e.candidate_version+'；目前程式碼 '+e.candidate_source_version+' 僅建置，未完成新版本驗收。'),text('p',e.candidate_scope))}"
if addition not in s:
    s = s.replace(needle, addition + needle)
if 'id="handoff-status"' not in s:
    s = s.replace('</header>', '<p id="handoff-status">LB-061 候選已在 0.10.1 原生實測；0.10.2 窄版排版修正仅建置，正式交付狀態未增加。<a href="HOME_TRANSFER.md">家用開發交接</a></p></header>', 1)
write(html, s)

for filename, note in [
    ('UI_UX_STANDARD.md', '0.10.1 SunHours 的色樣／欄位共用欄寬缺陷，再次確認寬說明文字不能與多欄數值共用 DynamicLayout。0.10.2 以獨立 nested field grids 修正，僅 Build，待 320／480 px 與完整宿主 QA。'),
    ('NOTION_KNOWLEDGE.md', 'Notion 最後完成同步仍為上述 190 筆／0.9.2；0.10.1 候選、0.10.2 Build 與家用交接尚未同步。家用連線後更新固定 ID，保留歷史與資料庫。'),
    ('DEVELOPMENT_LOG.md', '新增 LB-061 候選 Core／Adapter／中文內部模組與 UI-only preview owner。0.10.1 原生 154 項通過、44 UI＋2 3D 擷取；窄版圖例／數值欄位缺陷未驗收。0.10.2 修正／Build 0 錯誤 0 警告，尚未載入複驗。使用者要求先整理再安全移轉家用電腦，停止新增功能，專案快照保留未提交來源；無跨機通過宣稱。')]:
    p = docs / filename
    marker = '## 2026-10-02 · 家用移轉交接'
    if marker not in read(p):
        write(p, read(p) + '\n\n' + marker + '\n\n' + note + '\n')

# Keep the new handoff language in Traditional Chinese.
for p in [docs / 'HOME_TRANSFER.md', docs / 'HOME_CONTINUE_PROMPT.md', docs / 'SUN_HOURS_MODULE.md', docs / 'KNOWLEDGE_INDEX.md', html]:
    s = read(p)
    for a, b in {'路径': '路徑', '改写': '改寫', '複验': '複驗', '优先': '優先', '实际': '實際',
                 '分钟': '分鐘', '显示': '顯示', '交给': '交給', '仅建置': '僅建置'}.items():
        s = s.replace(a, b)
    write(p, s)
print(json.dumps({'handoff': 'documented', 'source': '0.10.2 BUILD_ONLY', 'native_prior_candidate': total,
                  'formal_functions': 9, 'candidate_functions': 10, 'catalog_entries': 122,
                  'existing_release_hashes': 'PASS'}, ensure_ascii=False))
