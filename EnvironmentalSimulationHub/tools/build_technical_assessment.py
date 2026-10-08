"""Build a transparent planning estimate from the locked 122-entry catalog.

No solver is executed. Ranges are engineering judgment, not measured throughput.
"""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'docs/evidence/ladybug_feature_catalog.json'
OUT = ROOT / 'docs/evidence/technical_assessment_20261003'
DOC = ROOT / 'docs/TECHNICAL_ASSESSMENT_2026-10-03.md'
FORMAL = {1, 7, 9, 11, 13, 20, 33, 57, 63}
HIGH = {12, 35, 37, 38, 39, 43, 45, 47, 48, 49, 52, 53, 54, 55,
        58, 64, 66, 67, 68, 70, 71, 74}
LOW = {2, 3, 10, 17, 18, 19, 21, 24, 25, 27, 30, 36, 41, 44, 65,
       76, 77, 79, 81, 82, 83, 87, 91, 93, 94, 95, 97, 100, 101,
       102, 103, 104, 106, 108, 109, 110, 112, 113, 114, 115, 116, 117, 118}
SHARED = [
    ('V02 完整宿主操作收尾', 3, 6),
    ('DataCollection／Header／型別與單位共用契約', 12, 20),
    ('既有 SunPath／日射／日照進階選項補齊', 8, 15),
    ('工作執行器、程序隔離與取消第一版', 15, 25),
    ('大型模型、完整主題／操作與跨模組回歸', 10, 18),
    ('跨機試用、依賴鎖定、發布及回復', 6, 12),
    ('全目錄、操作文件與 Notion 三層整理', 4, 7),
    ('.NET／Rhino 版本生命週期相容性探查', 3, 6),
]
NEAR = [
    ('V02 完整宿主操作收尾', 3, 6),
    ('V03 Sky Mask 第一批', 6, 10),
    ('V04 Solar Envelope 第一批', 8, 15),
    ('必要 L1 依賴與結果條件補齊', 5, 10),
    ('相關大型案例／回歸／一次跨機試用', 8, 15),
]
EXTENSIONS = [
    ('CFD：引擎部署探查＋單風向＋多風向／一種風舒適準則', 40, 70),
    ('採光：單時刻＋年度採光／一種眩光流程', 35, 60),
    ('能耗：單棟建築模型、材料／排程、年度求解與結果', 35, 60),
    ('碳排：一套明定資料源的營運／材料碳排初版', 15, 30),
    ('V2：設計 8–15＋互動實作 25–45＋操作驗收 8–15', 41, 75),
]


def totals(rows):
    return [sum(r[1] for r in rows), sum(r[2] for r in rows)]


def buffered(pair):
    return [math.ceil(v * 1.25) for v in pair]


def main():
    source = json.loads(CATALOG.read_text(encoding='utf-8'))
    assert source['count'] == len(source['components']) == 122
    assert not (LOW & HIGH) and not (FORMAL & (LOW | HIGH))
    items = []
    for c in source['components']:
        number = int(c['id'][3:])
        if number in FORMAL or number == 61:
            continue
        level, bounds = ('S', [.5, 1.5]) if number in LOW else ('C', [4, 9]) if number in HIGH else ('M', [1.5, 3.5])
        if number == 49:
            bounds = [4, 7]
        elif number == 67:
            bounds = [6, 10]
        elif number == 68:
            bounds = [8, 15]
        items.append({'id': c['id'], 'name': c['name'], 'category': c['subcategory'],
                      'complexity': level, 'person_days': bounds,
                      'status': '後端轉獨立流程待開發' if number == 49 else '待接入'})
    assert len(items) == 112 and len({c['id'] for c in items}) == 112
    entry_total = [sum(c['person_days'][i] for c in items) for i in [0, 1]]
    shared = totals(SHARED)
    subtotal = [a+b for a, b in zip(entry_total, shared)]
    budget = buffered(subtotal)
    extension_budget = buffered(totals(EXTENSIONS))
    result = {
        'assessment_date': '2026-10-03', 'code_baseline': '7dd5e01',
        'formal_version': '0.9.2', 'candidate_version': '0.10.7',
        'basis': 'Initial engineering judgment, one engineer with AI assistance, 8h/person-day, 5 days/week, 20 days/planning month; no measured productivity distribution.',
        'reserve_factor': 1.25,
        'catalog_sha256': hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        'catalog_category_counts': dict(Counter(c['subcategory'] for c in source['components'])),
        'formal_coverage': [9, 1, 112], 'candidate_coverage': [10, 1, 111],
        'estimated_entries': 112,
        'explanation': '111 candidate-pending entries plus LB-049 backend-to-independent workflow; LB-061 closure and existing options are shared work, not another entry.',
        'complexity_counts': dict(Counter(c['complexity'] for c in items)),
        'entries': items, 'entry_person_days': entry_total,
        'shared_packages': SHARED, 'shared_person_days': shared,
        'ladybug_subtotal_person_days': subtotal,
        'ladybug_budget_person_days': budget,
        'ladybug_planning_months': [round(v/20, 1) for v in budget],
        'near_l2_packages': NEAR,
        'near_l2_budget_person_days': buffered(totals(NEAR)),
        'future_packages': EXTENSIONS,
        'future_budget_person_days': extension_budget,
        'combined_budget_person_days': [a+b for a, b in zip(budget, extension_budget)],
        'excluded': ['External approval/QA waiting', 'new physics implementation',
                     'fully coupled Outdoor+ (additional 40–80 person-days before reserve)',
                     'enterprise multi-tenant cloud/BIM synchronization',
                     'runtime/host migration execution if exploration finds major incompatibility'],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'estimate_model.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='')
    text = DOC.read_text(encoding='utf-8')
    marker = '<!-- GENERATED_ENTRY_ESTIMATES -->'
    assert marker in text
    text = text.split(marker)[0]
    for old, new in {'脚': '腳', '条件': '條件', '结果': '結果', '点／': '點／',
                     '价值': '價值', '基础': '基礎', '这样': '這樣', '這样': '這樣',
                     '状态': '狀態', '载入与': '載入與', '載入与': '載入與'}.items():
        text = text.replace(old, new)
    text += marker + '\n\n'
    text += '| 入口 | 原生名稱 | 難度 | 初步人日 | 狀態／範圍 |\n| --- | --- | --- | --- | --- |\n'
    for c in items:
        a, b = c['person_days']
        text += f"| {c['id']} | {c['name']} | {c['complexity']} | {a:g}–{b:g} | {c['status']} |\n"
    DOC.write_text(text, encoding='utf-8', newline='')
    print(json.dumps({k:v for k,v in result.items() if k not in ['entries','shared_packages','near_l2_packages','future_packages']},ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
