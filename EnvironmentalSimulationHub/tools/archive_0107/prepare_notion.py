import json, hashlib, re
from pathlib import Path
root=Path(__file__).resolve().parents[2]; ev=root/'docs/evidence/archive_0107'
def sha(path): return hashlib.sha256((root/path).read_bytes()).hexdigest()
def md(path):
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
            for row in rows:
                out.append('<tr>'); out.extend('<td>'+cell.strip()+'</td>' for cell in row.strip('|').split('|')); out.append('</tr>')
            out.append('</table>'); continue
        out.append(line); i+=1
    return '\n'.join(out)
summary=(ev/'summary.txt').read_text(encoding='utf-8')
version='0.10.7 候選；正式 0.9.2'
props={'紀錄編號':'VER-HOME-0107-01','紀錄名稱':'0.10.7 候選｜日照方案匯入與跨程序恢復','分類':'驗證紀錄','主題':'版本與維護','階段':'X1','狀態':'已驗證','優先序':'P0','摘要':summary,'來源路徑':'docs/HOME_VALIDATION_0107.md','適用版本':version,'驗證層級':json.dumps(['文件整理','建置','原生數值','原生操作','正式載入','視覺檢視'],ensure_ascii=False),'date:更新日期:start':'2026-10-03','date:更新日期:is_datetime':0}
content=md('docs/HOME_VALIDATION_0107.md')+'\n---\n## 方案規格與操作\n'+md('docs/SUNHOURS_SCENARIO_ARCHIVE.md')+'\n---\n本機來源：`docs/HOME_VALIDATION_0107.md`；SHA-256：`'+sha('docs/HOME_VALIDATION_0107.md')+'`。\n規格來源：`docs/SUNHOURS_SCENARIO_ARCHIVE.md`；SHA-256：`'+sha('docs/SUNHOURS_SCENARIO_ARCHIVE.md')+'`。'
mappings=[('3ec1956a-9b0e-81ac-a858-fefd1fae1c4c','docs/PROJECT_STATUS.md'),('3ec1956a-9b0e-81db-9006-c5c42befece5','docs/KNOWLEDGE_INDEX.md'),('3ec1956a-9b0e-81bf-bdae-eb999326ce85','docs/evidence/ladybug_feature_catalog.json'),('3ec1956a-9b0e-8183-bf5c-f58832a3a7b5','docs/BUILD_AND_RUN.md'),('3ec1956a-9b0e-816b-9d9f-d42013648423','docs/ROADMAP.md'),('3ed1956a-9b0e-8145-9fef-cccd2370acaa','docs/L2_VISUAL_PLAN.md'),('3ec1956a-9b0e-81e2-8398-c5ae704cf7c9','docs/PROJECT_STATUS.md'),('3ec1956a-9b0e-813e-8c23-d6b139442afe','docs/ROADMAP.md')]
payload={'page':{'properties':props,'content':content},'summary':summary,'version':version,'mappings':[{'id':id,'source':p,'sha256':sha(p)} for id,p in mappings],'visual':{'id':'3ee1956a-9b0e-8157-996c-d7e88c4d2cf3','source':'docs/DEVELOPMENT_HIGHLIGHTS.md','sha256':sha('docs/DEVELOPMENT_HIGHLIGHTS.md'),'content':md('docs/DEVELOPMENT_HIGHLIGHTS.md')+'\n---\n本機來源：`docs/DEVELOPMENT_HIGHLIGHTS.md`；SHA-256：`'+sha('docs/DEVELOPMENT_HIGHLIGHTS.md')+'`。'},'risk4':{'id':'3ec1956a9b0e81118f91c6d4411b5408','source':'docs/SUNHOURS_SCENARIO_ARCHIVE.md','sha256':sha('docs/SUNHOURS_SCENARIO_ARCHIVE.md'),'content':md('docs/SUNHOURS_SCENARIO_ARCHIVE.md')}}
(ev/'notion_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared Notion 0.10.7 payload with stable IDs and local SHA values')
