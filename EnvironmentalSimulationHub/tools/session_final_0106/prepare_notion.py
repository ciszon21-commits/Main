import json, hashlib, re
from pathlib import Path
root=Path(__file__).resolve().parents[2]; ev=root/'docs/evidence/session_final_0106'
def sha(path): return hashlib.sha256((root/path).read_bytes()).hexdigest()
def notion_md(path):
    text=(root/path).read_text(encoding='utf-8').split('\n',1)[1].lstrip()
    text=re.sub(r'\[([^\]]+)\]\((?!https?://)([^)]+)\)',lambda m:m[1]+'（`'+m[2]+'`）',text)
    lines=text.splitlines(); out=[]; i=0; literal=False
    while i<len(lines):
        line=lines[i]
        if line.startswith('```'): literal=not literal
        if not literal and line.startswith('|') and i+1<len(lines) and re.match(r'^\|[\s:|\-]+$',lines[i+1]):
            rows=[line]; i+=2
            while i<len(lines) and lines[i].startswith('|'): rows.append(lines[i]); i+=1
            out.append('<table fit-page-width="true" header-row="true">')
            for j,row in enumerate(rows):
                out.append('<tr'+(' color="gray_bg"' if j==0 else '')+'>')
                out.extend('<td>'+cell.strip()+'</td>' for cell in row.strip('|').split('|'))
                out.append('</tr>')
            out.append('</table>'); continue
        out.append(line); i+=1
    return '\n'.join(out)
summary=(ev/'summary.txt').read_text(encoding='utf-8')
def props(code,title,path,category,topic,stage,status):
    return {'紀錄編號':code,'紀錄名稱':title,'分類':category,'主題':topic,'階段':stage,'狀態':status,'優先序':'P0' if code.startswith('VER') else 'P1','摘要':summary if code.startswith('VER') else '開發里程碑、資料保留流程、真實日照案例與驗收狀態；詳細資料、重點整理、視覺化精華互相連結，只在實際進度後更新。','來源路徑':path,'適用版本':'0.10.6 候選；正式 0.9.2','驗證層級':json.dumps(['文件整理','原生數值','原生操作','正式載入'] if code.startswith('VER') else ['文件整理'],ensure_ascii=False),'date:更新日期:start':'2026-10-03','date:更新日期:is_datetime':0}
pages=[]
for code,title,path,category,topic,stage,status in [('VER-HOME-0106-01','0.10.6 候選｜停靠資料保留與正式結果匯出','docs/HOME_VALIDATION_0106.md','驗證紀錄','版本與維護','L2','已驗證'),('KB-003','視覺化精華｜開發里程碑、流程與案例','docs/DEVELOPMENT_HIGHLIGHTS.md','知識管理','圖表與視覺化','X1','採用中')]:
    content=notion_md(path)+'\n---\n## 來源與維護\n本機來源：`'+path+'`；SHA-256：`'+sha(path)+'`。\n本機路徑供追溯，不是雲端下載連結。正式覆蓋未增加，未建立背景自動同步。\n目前狀態：<mention-page url="https://app.notion.com/p/3ec1956a9b0e81aca858fefd1fae1c4c"/>；L2 計畫：<mention-page url="https://app.notion.com/p/3ed1956a9b0e81459fefcccd2370acaa"/>。'
    pages.append({'properties':props(code,title,path,category,topic,stage,status),'content':content})
mappings=[('3ec1956a-9b0e-81ac-a858-fefd1fae1c4c','docs/PROJECT_STATUS.md'),('3ec1956a-9b0e-81db-9006-c5c42befece5','docs/KNOWLEDGE_INDEX.md'),('3ec1956a-9b0e-81bf-bdae-eb999326ce85','docs/evidence/ladybug_feature_catalog.json'),('3ec1956a-9b0e-8183-bf5c-f58832a3a7b5','docs/BUILD_AND_RUN.md'),('3ec1956a-9b0e-816b-9d9f-d42013648423','docs/ROADMAP.md'),('3ed1956a-9b0e-8145-9fef-cccd2370acaa','docs/L2_VISUAL_PLAN.md'),('3ec1956a-9b0e-81e2-8398-c5ae704cf7c9','docs/PROJECT_STATUS.md'),('3ec1956a-9b0e-813e-8c23-d6b139442afe','docs/ROADMAP.md')]
payload={'pages':pages,'summary':summary,'mappings':[{'id':id,'source':p,'sha256':sha(p)} for id,p in mappings]}
(ev/'notion_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(payload,ensure_ascii=True))
