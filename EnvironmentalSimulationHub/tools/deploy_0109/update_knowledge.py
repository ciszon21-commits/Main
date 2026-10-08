"""Record this verified company deployment without promoting function acceptance."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
docs = root / 'docs'
heading = '## 2026-10-05 · 公司已部署 0.10.9／重複 ID 修正'
entry = heading + '''

公司新專用 Rhino 已實際載入 **0.10.9.0**。修正 HKLM／HKCU 兩筆既有外掛路徑，消除舊 0.10.1 覆蓋與再次載入同 ID 的觸發原因；保留 GUID、舊版及第一份備份。15 項原生檢查通過，包含兩次新日照求解（256 點無遮蔭 13 h、遮蔭 8–13 h／平均 9.57421875 h）、A/B、新版 HTML、失敗保留、模組切換與實際停靠／浮動狀態。另有本輪 42 方案、15 MCP 工具檢查。

新版報告頁由「匯出圖像摘要 HTML…」使用，WebView 預設 gate 保留。原生窄版擷取未通過宿主型別假設，完整 Dock 版面／主題／DPI／鍵盤與檔案對話框仍待驗收；MCP 曾提前斷線，後續同程序版本及原生紀錄已讀回。有效測試物件清空，面板已關閉；未強制結束工作階段。

[部署、操作與回復](COMPANY_DEPLOYMENT_0109.md) · [最終證據](evidence/deploy_0109/deployment_verified.json) · [本輪真實日照摘要](evidence/deploy_0109/current-summary.html)。正式功能基準 **0.9.2／9、1、112**；已部署候選 **0.10.9／10、1、111**，不增加功能覆蓋。本輪沒有 GitHub 推送或跨機試用驗收。下一步維持指定時刻陰影、風花圖／常用圖表及提前 Eddy3D 引擎關卡。

'''
for name in ['PROJECT_STATUS.md', 'KNOWLEDGE_INDEX.md', 'DEVELOPMENT_HIGHLIGHTS.md', 'MULTI_VISUAL_MVP_PLAN_2026-10-05.md']:
    path = docs / name
    current = path.read_text(encoding='utf-8-sig')
    if heading not in current:
        path.write_text(entry + current, encoding='utf-8')

short = '公司部署註記（2026-10-05）：0.10.9.0 已載入，15 原生日照／狀態檢查通過；HTML 成果可用，完整原生 UI／內嵌 WebView 待驗收。正式 9／1／112 不變。[部署與回復](COMPANY_DEPLOYMENT_0109.md)。\n\n'
path = docs / 'LADYBUG_FEATURE_TABLE.md'
current = path.read_text(encoding='utf-8-sig')
if short not in current:
    path.write_text(short + current, encoding='utf-8')
catalog_path = docs / 'evidence/ladybug_feature_catalog.json'
catalog = json.loads(catalog_path.read_text(encoding='utf-8-sig'))
before_statuses = [item['hub_status'] for item in catalog['components']]
catalog['company_deployment'] = {
    'date': '2026-10-05', 'version': '0.10.9.0',
    'scope': 'Candidate deployed; 15 native checks; formal component states unchanged',
    'evidence': 'docs/evidence/deploy_0109/deployment_verified.json',
    'webview_default': 'Disabled', 'native_visual_acceptance': 'Pending'
}
assert len(before_statuses) == 122
assert [item['hub_status'] for item in catalog['components']] == before_statuses
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
path = docs / 'LADYBUG_FEATURE_TABLE.html'
current = path.read_text(encoding='utf-8-sig')
note = '<p id="company-deploy-0109">公司已部署 0.10.9.0：15 原生日照／狀態檢查通過；HTML 成果可用，完整宿主 UI 待驗收。正式功能 9／1／112 不變。<a href="COMPANY_DEPLOYMENT_0109.md">部署與回復</a></p>'
if 'id="company-deploy-0109"' not in current:
    assert '<main>' in current
    path.write_text(current.replace('<main>', '<main>' + note, 1), encoding='utf-8')
path = docs / 'QUICK_START.md'
current = path.read_text(encoding='utf-8-sig')
note = '公司本機更新（2026-10-05）：已部署候選 **0.10.9**，可執行 `EnvironmentalHub`／`EnvironmentalSunHours`，完成日照後使用「匯出圖像摘要 HTML…」。[新版操作與回復](COMPANY_DEPLOYMENT_0109.md)。下方保留 0.9.2 跨機內部試用包說明，未將本機載入視為同仁跨機驗收。\n\n'
if note not in current:
    path.write_text(note + current, encoding='utf-8')
maps = [('3ec1956a-9b0e-80e4-8a34-f1c44b6d532d','COMPANY_DEPLOYMENT_0109.md'),
        ('3ec1956a-9b0e-81ac-a858-fefd1fae1c4c','PROJECT_STATUS.md'),
        ('3ee1956a-9b0e-8157-996c-d7e88c4d2cf3','DEVELOPMENT_HIGHLIGHTS.md'),
        ('3ee1956a-9b0e-8111-88ba-cca59252fbcb','MULTI_VISUAL_MVP_PLAN_2026-10-05.md')]
payload = []
for page_id, name in maps:
    sha = hashlib.sha256((docs/name).read_bytes()).hexdigest()
    content = entry.split('[部署、操作與回復]')[0]
    content += '正式功能基準 **0.9.2／9、1、112**；已部署候選 **0.10.9／10、1、111**，功能覆蓋不變。詳細部署、失敗與回復來源：`docs/COMPANY_DEPLOYMENT_0109.md`；證據：`docs/evidence/deploy_0109/deployment_verified.json`。本輪沒有 GitHub 推送或跨機試用驗收。下一步維持指定時刻陰影、風花圖／常用圖表與 Eddy3D 引擎關卡。\n'
    content += f'本輪地端來源：`docs/{name}`；SHA-256：`{sha}`。\n\n'
    payload.append({'id':page_id,'source':'docs/'+name,'sha256':sha,'content':content})
(docs/'evidence/deploy_0109/notion_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'updated_pages':len(maps),'catalog_entries':122,'coverage_changed':False}))
