import json
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[2]
evidence = root / 'docs/evidence/webview_0108'
heading = '## 2026-10-05 · 0.10.8 日照圖像摘要與 WebView 探查'
summary = '''候選來源 0.10.8 新增中文日照分布圖、原生色樣、KPI／來源／目標／比較摘要與離線 HTML 匯出。只讀 WebView 在同一內部視圖惰性載入，預設由試驗 gate 阻擋初始化；C# 權威狀態與求解核心保留。

最終 Build 0 錯誤／0 警告；呈現契約 16、原有方案契約 42、隔離 Rhino 呈現／狀態 9 項通過，修正版 WebView 中文 DOM 已讀回。真正 320／480 CSS viewport 淺／深色四張已檢視，無水平溢出。這是歷史原生結果的呈現驗證，沒有本輪新求解。

原生 SDK 擷取、完整 Dock／原生深色／DPI／鍵盤／檔案及非同步失敗復原待驗收；MV-U0 部分完成。公司自建 Rhino 自動載入舊 0.10.1，探查改用獨立組件名稱，未替換公司註冊或正式部署。正式仍 0.9.2／9、1、112；候選 10、1、111，UI 工作不增加功能覆蓋。

[詳細驗證與下一步](WEBVIEW_RESULT_PROBE_0108.md) · [證據](evidence/webview_0108/acceptance.json) · [離線摘要](evidence/webview_0108/summary-light.html)。本輪失敗與限制另存；其他專案未修改，GitHub 未推送。'''
for name in ['PROJECT_STATUS.md', 'KNOWLEDGE_INDEX.md', 'DEVELOPMENT_HIGHLIGHTS.md', 'DEVELOPMENT_LOG.md', 'UI_UX_STANDARD.md', 'WEBVIEW_UI_STRATEGY_2026-10-05.md']:
    path = root / 'docs' / name
    text = path.read_text(encoding='utf-8')
    assert heading not in text, 'Do not duplicate delivery update'
    extra = '\n\n```mermaid\nflowchart LR\n A[完成原生結果] --> B[只讀摘要與離線 HTML]\n B --> C[16 呈現＋9 原生狀態檢查]\n B --> D[320／480 CSS 淺深色 4 張]\n C --> E[WebView 宿主門檻待驗收]\n D --> E\n E --> F[通過後才解除試驗 gate]\n```' if name == 'DEVELOPMENT_HIGHLIGHTS.md' else ''
    path.write_text(heading + '\n\n' + summary + extra + '\n\n' + text, encoding='utf-8')
plan = root / 'docs/MULTI_VISUAL_MVP_PLAN_2026-10-05.md'
plan.write_text(plan.read_text(encoding='utf-8') + '\n\n## 8. 實作進度 · 0.10.8／2026-10-05\n\nMV-U0 已開始：日照只讀摘要、離線 HTML 與惰性 WebView 接層已實作；16 呈現、9 隔離原生狀態及 4 個真實 CSS viewport 檢查通過。完整宿主與失敗復原未閉合，預設試驗 gate 保留；不是全介面遷移或新增求解驗收。詳見 [0.10.8 範圍](WEBVIEW_RESULT_PROBE_0108.md)。其他 MVP 工作包、正式覆蓋與原始估算不變。\n', encoding='utf-8')
def read(path): return json.loads((evidence / path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
sources = [p.relative_to(root).as_posix() for p in (root / 'src/EnvironmentalHub.Plugin').glob('SunHours*.cs')]
sources += ['src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj', 'samples/archive_0107/legacy_comparison.json']
manifest = {name: sha(root / name) for name in sources}
manifest.update({p.relative_to(root).as_posix(): sha(p) for p in (root / 'artifacts/company-build/0.10.8').glob('*') if p.suffix in ('.rhp', '.dll')})
receipt = {'date': '2026-10-05', 'candidate': '0.10.8', 'formal': '0.9.2', 'formal_coverage': [9,1,112], 'candidate_coverage': [10,1,111],
           'build': {'errors': 0, 'warnings': 0, 'target': 'net8.0-windows', 'sdk': '10.0.400'},
           'presentation': read('presentation_checks.json'), 'archive_contract_passed': 42,
           'native_presentation': read('fixed/native_start.json'), 'native_dom': read('fixed/pump.json'),
           'html_visual': read('browser-verified/verification.json'), 'images_reviewed': True,
           'native_capture': 'UNVERIFIED; task pending, test Form hidden', 'production_plugin_deployment': 'NOT_PERFORMED',
           'cleanup': read('fixed/cleanup.json'), 'close_slot': 'REFUSED_ADOPTED; no force-close',
           'new_solver_run': False, 'core_and_adapters_modified': False, 'source_binary_sha256': manifest,
           'open_gates': ['real registered Dock narrow/wide/rebuild', 'native theme and DPI', 'keyboard and focus', 'HTML SaveFileDialog success/cancel', 'async initialization/browser failure recovery', 'cross-machine pilot'],
           'failure_evidence': 'All failed transports and invalid captures preserved separately; browser-verified only contains accepted HTML captures', 'notion_sync': 'PENDING'}
(evidence / 'acceptance.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'candidate': '0.10.8', 'presentation': 16, 'native_presentation': len(receipt['native_presentation']['checks']), 'html_captures': 4, 'notion': 'PENDING'}))
