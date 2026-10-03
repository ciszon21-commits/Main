from pathlib import Path
root = Path(__file__).resolve().parents[2]
section = "## 2026-10-03 · 0.10.5 原生操作補驗與 MCP 修正\n\n外掛維持 0.10.5。本輪修正 MCP 探測器漏判「正常輸出後附加執行例外」，**12 項工具測試通過**；另在新隔離空白 Rhino 通過 **7 項額外原生操作**（停靠保護 3、基本鍵盤 3、Eto 存檔取消 1）。原驗證程序已有 608 物件，未在其中操作。完整 168 項求解／平台回歸與 44 張圖屬前輪歷史，本輪未重跑。\n\n唯讀檢查 161 份有回應的 transport，列出 21 個含錯誤的呼叫（包含已知失敗重試），歷史 receipts 不改寫。完整停靠版面、深色、全鍵盤／成功 picker 與正式匯出對話框仍待驗收，桌面影像擷取逾時；V02 未正式交付，V03 未啟動。正式 **0.9.2／9、1、112**，候選 10／1／111。\n\n[本輪範圍](HOME_UI_VALIDATION_0105.md) · [補驗證據](evidence/native_ui_0105/acceptance.json)；以下保留前輪版本化範圍。\n\n"
files = ['PROJECT_STATUS.md','KNOWLEDGE_INDEX.md','BUILD_AND_RUN.md','ROADMAP.md','L2_VISUAL_PLAN.md','SUN_HOURS_MODULE.md','HOME_CONTINUE_PROMPT.md','HOME_TRANSFER.md','DEVELOPMENT_LOG.md']
for name in files:
    path = root / 'docs' / name
    text = path.read_text(encoding='utf-8')
    assert not text.startswith(section.splitlines()[0])
    path.write_text(section + text,encoding='utf-8',newline='\n')
path = root / 'README.md'
text = path.read_text(encoding='utf-8')
path.write_text(section.replace('(HOME_UI_', '(docs/HOME_UI_').replace('(evidence/', '(docs/evidence/') + text,encoding='utf-8',newline='\n')
