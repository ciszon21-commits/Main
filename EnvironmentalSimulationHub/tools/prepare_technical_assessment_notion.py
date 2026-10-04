"""Prepare one detailed assessment and targeted existing-page additions."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT/'docs/evidence/technical_assessment_20261003'


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def md_text(text):
    text = re.sub(r'\[([^\]]+)\]\((?!https?://)([^)]+)\)',
                  lambda m: m[1]+'（`'+m[2]+'`）', text)
    out, lines, i, literal = [], text.splitlines(), 0, False
    while i < len(lines):
        line = lines[i]
        if line.startswith('```'):
            literal = not literal
        if not literal and line.startswith('|') and i+1 < len(lines) and re.match(r'^\|[\s:|\-]+$', lines[i+1]):
            rows = [line]
            i += 2
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i])
                i += 1
            out.append('<table fit-page-width="true" header-row="true">')
            for row in rows:
                out.append('<tr>')
                out.extend('<td>'+cell.strip()+'</td>' for cell in row.strip('|').split('|'))
                out.append('</tr>')
            out.append('</table>')
            continue
        if line.strip() != '<!-- GENERATED_ENTRY_ESTIMATES -->':
            out.append(line)
        i += 1
    return '\n'.join(out)


def section(path, start, stop):
    text = (ROOT/path).read_text(encoding='utf-8')
    return md_text(text[text.index(start):text.index(stop)])


def main():
    source = 'docs/TECHNICAL_ASSESSMENT_2026-10-03.md'
    text = (ROOT/source).read_text(encoding='utf-8').split('\n', 1)[1].lstrip()
    boundaries = ['## 6. 後續功能、依賴與技術評估', '## 附錄：112個待補入口的初步估算']
    first, tail = text.split(boundaries[0], 1)
    middle, appendix = (boundaries[0]+tail).split(boundaries[1], 1)
    chunks = [md_text(first), md_text(middle), md_text(boundaries[1]+appendix)]
    footer = '\n---\n## 雙端來源\n本機來源：`'+source+'`；SHA-256：`'+sha(source)+'`。\n估算模型：`docs/evidence/technical_assessment_20261003/estimate_model.json`；SHA-256：`'+sha('docs/evidence/technical_assessment_20261003/estimate_model.json')+'`。\n本機路徑供追溯，不是雲端下載連結。工期為工程假設；正式0.9.2／候選0.10.7，沒有新增求解驗收或提高覆蓋。\n目前狀態：<mention-page url="https://app.notion.com/p/3ec1956a9b0e81aca858fefd1fae1c4c"/>；規劃：<mention-page url="https://app.notion.com/p/3ec1956a9b0e816b9d9fd42013648423"/>；視覺化精華：<mention-page url="https://app.notion.com/p/3ee1956a9b0e8157996cd7e88c4d2cf3"/>。'
    chunks[-1] += footer
    props = {'紀錄編號':'ASSESS-TECH-001',
             '紀錄名稱':'完整技術評估｜架構、難點、後續功能與工期',
             '分類':'技術架構','主題':'平台整合','階段':'X1','狀態':'採用中','優先序':'P0',
             '摘要':'C#／.NET 8與Rhino／Eto／GH原生Ladybug架構；11項未解瓶頸、完整功能依賴及112入口逐項估算。一位工程人員＋AI全時基準：近期L2 38–70人日／8–14工作週；完整Ladybug V1 309–677人日／約16–34規劃月。工程假設、非交付承諾；包含.NET 8支援至2026-11-10的相容性探查。正式0.9.2／候選0.10.7覆蓋未變。',
             '來源路徑':source,'適用版本':'0.10.7 候選；正式 0.9.2',
             '驗證層級':json.dumps(['文件整理'],ensure_ascii=False),
             'date:更新日期:start':'2026-10-03','date:更新日期:is_datetime':0}
    maps = [
        ('3ec1956a-9b0e-81db-9006-c5c42befece5','docs/KNOWLEDGE_INDEX.md','## 2026-10-03 · 技術、難點與工期完整評估','## 2026-10-03 · 0.10.7 日照方案匯入與恢復'),
        ('3ec1956a-9b0e-816b-9d9f-d42013648423','docs/ROADMAP.md','## 2026-10-03 · 工期與技術依賴評估','## 2026-10-03 · 0.10.7 日照方案匯入與恢復'),
        ('3ee1956a-9b0e-8157-996c-d7e88c4d2cf3','docs/DEVELOPMENT_HIGHLIGHTS.md','## 技術與工期評估 · 2026-10-03','## 里程碑'),
    ]
    payload = {'properties':props,'chunks':chunks,'summary':props['摘要'],
               'mappings':[{'id':i,'source':p,'source_sha256':sha(p),'addition':section(p,a,b)} for i,p,a,b in maps],
               'source':source,'source_sha256':sha(source),
               'model_sha256':sha('docs/evidence/technical_assessment_20261003/estimate_model.json')}
    EV.mkdir(parents=True,exist_ok=True)
    (EV/'notion_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    print(json.dumps({'chunk_characters':[len(c) for c in chunks], 'source_sha256':payload['source_sha256'], 'mapping_count':len(maps)},ensure_ascii=True))


if __name__ == '__main__':
    main()
