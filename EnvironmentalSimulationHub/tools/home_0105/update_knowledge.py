import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
proof = json.loads((root / 'docs/evidence/home_0105/acceptance.json').read_text(encoding='utf-8'))
assert proof['native_checks'] == 168 and proof['core_checks'] == 25
summary = '''0.10.5 已修正工作平台首次開啟的浮動寬度：外框至少 500、實測內容 490；只處理 Rhino 已註冊的本平台實例。手動縮窄、關閉重開及模組切換保留使用者尺寸，較寬視窗不縮小；一般 Eto 視窗不被調整。168 項原生／平台（既有 161＋寬度 7）、Core 25、MCP 工具 8、輸出回讀 3 項通過，建置 0 錯誤／0 警告。

新版 44 張 320／480 淺色離屏圖與 2 張真正視埠已檢視，requested／actual width 全數相符。0.10.4 曾把測試用一般視窗加寬，窄版擷取失效；該候選保留失敗證據、不交付。完整原生 Dock、深色、鍵盤及 picker／檔案對話框仍待驗收；使用者原本開啟的 Rhino 仍載入 0.10.3，候選載入路徑已更新，新程序可使用 0.10.5。

正式仍為 **0.9.2／9、1、112**，候選 10／1／111；先完成 V02 UI 門檻，再交付及開始 V03 Sky Mask。此次 UI 修正不增加功能覆蓋數。 [驗證範圍](HOME_VALIDATION_0105.md) · [彙總 receipt](evidence/home_0105/acceptance.json) · [雙端同步 receipt](evidence/notion_home_0105_sync_2026-10-03.json)。
'''
for path in ['README.md', 'docs/PROJECT_STATUS.md', 'docs/KNOWLEDGE_INDEX.md',
             'docs/BUILD_AND_RUN.md', 'docs/ROADMAP.md', 'docs/L2_VISUAL_PLAN.md',
             'docs/HOME_TRANSFER.md', 'docs/HOME_CONTINUE_PROMPT.md', 'docs/SUN_HOURS_MODULE.md']:
    target = root / path
    text = target.read_text(encoding='utf-8')
    assert '## 2026-10-03 · 目前候選 0.10.5' not in text
    section = summary
    if path == 'README.md':
        section = section.replace('(HOME_VALIDATION_', '(docs/HOME_VALIDATION_').replace('(evidence/', '(docs/evidence/')
    target.write_text('## 2026-10-03 · 目前候選 0.10.5\n\n' + section + '\n以下保留前一候選與正式歷史範圍。\n\n' + text, encoding='utf-8', newline='\n')
log = root / 'docs/DEVELOPMENT_LOG.md'
log.write_text('## 2026-10-03 · 0.10.5 浮動寬度修正與宿主範圍限制\n\n' + summary + '\n只修改 HubWorkspacePanel 與版本；Core／Adapter 原始碼不變。首次 0.10.4 宿主先載入舊候選，出現外掛 ID 已被使用；後續明確備份並更新本平台單一 HKCU FileName，沒有重設 Rhino 工作區。0.10.4 原生 167 項通過但 320 擷取实际 484，拒絕作為窄版驗收；0.10.5 新增真正註冊實例限制與一般視窗排除檢查。Git 遠端驗證仍需本機登入，本輪不宣稱已推送。\n\n' + log.read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
notion = root / 'docs/NOTION_KNOWLEDGE.md'
notion.write_text('## 目前同步 · 0.10.5／2026-10-03\n\n本輪沿用既有 8 筆固定紀錄，新增驗證編號 `VER-HOME-0105-01`，正式覆蓋數不变。實際同步、來源 SHA 及讀回結果以 [本輪 receipt](evidence/notion_home_0105_sync_2026-10-03.json) 為準；0.10.3 及更早同步 receipts 保持歷史範圍。\n\n' + notion.read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
