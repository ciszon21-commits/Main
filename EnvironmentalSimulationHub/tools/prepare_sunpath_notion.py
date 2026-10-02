"""Prepare source-captured current documents; this tool does not mutate Notion."""
import re,json,hashlib,ast
from pathlib import Path
root=Path(__file__).resolve().parents[1]
tree=ast.parse((root/'artifacts/prepare_notion_knowledge.py').read_text(encoding='utf-8'))
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['esc','table','markdown']]
ns={'re':re};exec(compile(ast.Module(body=functions,type_ignores=[]),'<notion-markdown>','exec'),ns)
def capture(path):
 p=root/path;s=ns['markdown'](p.read_text(encoding='utf-8'));digest=hashlib.sha256(p.read_bytes()).hexdigest()
 # Avoid automatic web links for local filenames in Notion prose.
 s=re.sub(r'(?<![`\w/])([A-Z][A-Z0-9_]+\.md)(?!`)',lambda m:'`'+m[0]+'`',s)
 return {'source':path,'sha256':digest,'content':s+'\n\n---\n## 來源與維護\n- 正式基準：0.9.0／2026-10-02；32 SunPath＋60 既有＋14 平台，106 項原生檢查。\n- 本機來源：`'+path+'`；路徑僅供追溯，不是雲端下載連結。\n- 來源 SHA-256：`'+digest+'`。\n- 歷史版本證據保留原範圍，跨機同仁試用未驗收。'}
paths={'status':'docs/PROJECT_STATUS.md','KB-002':'docs/KNOWLEDGE_INDEX.md','PLAN-000':'docs/ROADMAP.md','PLAN-001':'docs/LADYBUG_DEVELOPMENT_PLAN.md','plan':'docs/L2_VISUAL_PLAN.md','OPS-001':'docs/BUILD_AND_RUN.md','OPS-002':'docs/QUICK_START.md','OPS-003':'docs/PILOT_ACCEPTANCE.md','REV-001':'docs/DEVELOPMENT_REVIEW_2026-10-01.md','UI-001':'docs/UI_UX_STANDARD.md','UI-002':'docs/PLATFORM_UI.md','TECH-001':'docs/ARCHITECTURE.md','REF-001':'docs/REFERENCE_INDEX.md'}
data={k:capture(v) for k,v in paths.items()}
data['sunpath']=capture('docs/SUNPATH_MODULE.md')
data['catalog_sha256']=hashlib.sha256((root/'docs/evidence/ladybug_feature_catalog.json').read_bytes()).hexdigest()
data['roadmap_sha256']=data['PLAN-000']['sha256']
data['acceptance']=capture('docs/evidence/sunpath_090_acceptance.json')
data['manifest']=capture('docs/evidence/release_090_manifest.json')
destination=root/'artifacts/notion_sunpath_090.json';destination.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
print(destination)
