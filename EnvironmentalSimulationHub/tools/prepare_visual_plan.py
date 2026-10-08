"""Prepare local active-plan pointers and a Notion payload; no product changes."""
import hashlib
import json
import re
from pathlib import Path
from prepare_technical_assessment_notion import md_text

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/OPTIMIZED_VISUAL_PLAN_2026-10-03.md'
EV = ROOT / 'docs/evidence/visual_plan_20261003'
EV.mkdir(parents=True, exist_ok=True)
text = DOC.read_text(encoding='utf-8')
for old, new in {'後续':'後續','图例':'圖例','结果':'結果','实际':'實際','未来':'未來','删除':'刪除','预算':'預算'}.items():
    text = text.replace(old, new)
text = text.replace('共同單位、圖例範圍與相機。', '共同單位與相機；共同圖例範圍須透過原生支援且已驗證的圖例參數建立，不事後任意重塗原生網格。若無法合法對齊，保留各自原生色階並明示範圍。')
DOC.write_text(text, encoding='utf-8')
summary = '交付改為完整日照設計流程：共用設定→模型結果→天空遮蔽解讀→A／B比較→精簡匯出。先A日照視覺MVP23–40人日／5–8工作週，再B Solar Envelope13–23人日／3–5工作週；A＋B統一加25%為35–63人日。單人＋AI全時工程假設；122能力保留待辦，CFD／全量獨立頁面／大框架重寫後排。正式0.9.2／候選0.10.7，未新增求解驗證。'
header = '## 2026-10-03 · 目前採用：視覺優先與流程瘦身\n\n'+summary+'\n\n[完整優化計畫](OPTIMIZED_VISUAL_PLAN_2026-10-03.md)為活動排程依據；下方原計畫／估算保留作歷史範圍，遇順序差異以新計畫為準。\n\n'
paths = ['ROADMAP.md','L2_VISUAL_PLAN.md','LADYBUG_DEVELOPMENT_PLAN.md','KNOWLEDGE_INDEX.md','PROJECT_STATUS.md']
for name in paths:
    path = ROOT / 'docs' / name
    previous = path.read_text(encoding='utf-8-sig')
    if not previous.startswith(header):
        path.write_text(header+previous, encoding='utf-8')
graph = text.split('```mermaid\n', 1)[1].split('```', 1)[0]
highlight = header+'```mermaid\n'+graph+'```\n\n'
path = ROOT/'docs/DEVELOPMENT_HIGHLIGHTS.md'
previous = path.read_text(encoding='utf-8-sig')
if not previous.startswith(highlight):
    path.write_text(highlight+previous, encoding='utf-8')
model = {'basis':'one engineer + AI, full time; 8 h/day; 5 d/week; engineering judgment', 'reserve':0.25,
         'A':{'packages':{'A0':[3,6],'A1':[2,4],'A2':[5,8],'A3':[2,3],'A4':[3,5],'A5':[3,6]},'base':[18,32],'budget':[23,40]},
         'B':{'base':[10,18],'budget':[13,23]},'combined':{'base':[28,50],'budget':[35,63]},
         'excludes':['major runtime migration','all 122 independent UIs','CFD','external waiting'],
         'scope_change_not_measured_speedup':True}
(EV/'estimate_model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
files = ['docs/'+n for n in paths]+['docs/DEVELOPMENT_HIGHLIGHTS.md','docs/OPTIMIZED_VISUAL_PLAN_2026-10-03.md']
payload = {'summary':summary,'graph':graph,'source_hashes':{p:sha(ROOT/p) for p in files},
           'content':md_text(text.split('\n',1)[1].lstrip())+'\n\n## 本機來源\n`docs/OPTIMIZED_VISUAL_PLAN_2026-10-03.md`；SHA-256：`'+sha(DOC)+'`。\n本機路徑供追溯，非雲端下載連結。',
           'properties':{'紀錄編號':'PLAN-VISUAL-001','紀錄名稱':'優化版計畫｜視覺優先與日照流程瘦身','分類':'階段計畫','主題':'圖表與視覺化','階段':'L2','狀態':'採用中','優先序':'P0','摘要':summary,'來源路徑':'docs/OPTIMIZED_VISUAL_PLAN_2026-10-03.md','適用版本':'0.10.7 候選；正式 0.9.2','驗證層級':json.dumps(['文件整理'],ensure_ascii=False),'date:更新日期:start':'2026-10-03','date:更新日期:is_datetime':0}}
(EV/'notion_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
links = re.findall(r'\]\((?!https?://)([^)]+)\)',text)
assert all((DOC.parent/p).exists() for p in links)
assert [sum(v[i] for v in model['A']['packages'].values()) for i in range(2)] == model['A']['base']
(EV/'document_audit.json').write_text(json.dumps({'local_links':len(links),'all_links_exist':True,'estimate_arithmetic':True,'mermaid_count':text.count('```mermaid'),'source_hashes':payload['source_hashes'],'runtime_tests_run':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'payload':str(EV/'notion_payload.json'),'chars':len(payload['content']),'audit':'passed'},ensure_ascii=False))
