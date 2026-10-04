"""Verify report arithmetic, coverage, links, readback evidence and unchanged code."""
import ast
import hashlib
import json
import math
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT/'docs/evidence/technical_assessment_20261003'


def main():
    doc = ROOT/'docs/TECHNICAL_ASSESSMENT_2026-10-03.md'
    text = doc.read_text(encoding='utf-8')
    model = json.loads((EV/'estimate_model.json').read_text(encoding='utf-8'))
    receipt = json.loads((ROOT/'docs/evidence/notion_technical_assessment_sync_2026-10-03.json').read_text(encoding='utf-8'))
    catalog = json.loads((ROOT/'docs/evidence/ladybug_feature_catalog.json').read_text(encoding='utf-8'))
    checks = {}
    def require(name, value):
        checks[name] = bool(value)
        if not value:
            raise AssertionError(name)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    require('source_document_sha', sha(doc) == receipt['new_record']['source_sha256'])
    require('model_sha', sha(EV/'estimate_model.json') == receipt['estimate_model_sha256'])
    require('catalog_unchanged_sha', sha(ROOT/'docs/evidence/ladybug_feature_catalog.json') == model['catalog_sha256'])
    require('catalog_count', len(catalog['components']) == catalog['count'] == 122)
    actual_formal = {c['id'] for c in catalog['components'] if c['hub_status'] == '已接入並實測'}
    expected = {c['id'] for c in catalog['components']} - actual_formal - {'LB-061'}
    actual = {c['id'] for c in model['entries']}
    require('full_remaining_112_entry_mapping', len(actual_formal) == 9 and expected == actual and len(actual) == len(model['entries']) == 112)
    require('notion_112_entry_mapping', set(receipt['notion_appendix_ids']) == actual and len(receipt['notion_appendix_ids']) == 112)
    require('complexity_counts', dict(Counter(c['complexity'] for c in model['entries'])) == model['complexity_counts'])
    require('entry_totals', [sum(c['person_days'][i] for c in model['entries']) for i in [0,1]] == model['entry_person_days'])
    require('shared_totals', [sum(c[i] for c in model['shared_packages']) for i in [1,2]] == model['shared_person_days'])
    require('ladybug_budget', [math.ceil((a+b)*1.25) for a,b in zip(model['entry_person_days'],model['shared_person_days'])] == model['ladybug_budget_person_days'] == [309,677])
    require('near_l2_budget', [math.ceil(sum(c[i] for c in model['near_l2_packages'])*1.25) for i in [1,2]] == model['near_l2_budget_person_days'] == [38,70])
    require('future_budget', [math.ceil(sum(c[i] for c in model['future_packages'])*1.25) for i in [1,2]] == model['future_budget_person_days'] == [208,369])
    require('combined_budget', [a+b for a,b in zip(model['ladybug_budget_person_days'],model['future_budget_person_days'])] == model['combined_budget_person_days'] == [517,1046])
    appendix = text.split('<!-- GENERATED_ENTRY_ESTIMATES -->')[1]
    require('local_appendix_rows', set(re.findall(r'^\| (LB-\d{3}) \|',appendix,re.M)) == actual)
    require('twelve_main_sections', set(re.findall(r'^## (\d+)\.',text,re.M)) == {str(i) for i in range(1,13)})
    require('two_architecture_diagrams', text.count('```mermaid') == 2 and text.count('```') == 4)
    for row in model['entries']:
        a,b = row['person_days']
        require('appendix_'+row['id'], f"| {row['id']} | {row['name']} | {row['complexity']} | {a:g}–{b:g} |" in appendix)
    links = re.findall(r'\[[^\]]+\]\(([^)]+)\)',text)
    missing = [link for link in links if not link.startswith(('http://','https://','#')) and not (doc.parent/link).exists()]
    require('local_links_exist', not missing)
    require('traditional_chinese_new_document', not re.search('条件|结果|脚本|价值|基础|这样|状态|与|样',text))
    require('no_trailing_whitespace_new_document', all(line == line.rstrip() for line in text.splitlines()))
    require('scope_assumptions_explicit', all(s in text for s in ['初步工程估算','1 位','25%','不是 P50','2026-11-10','期限','子集合']))
    for record in receipt['existing_records']:
        require('synced_source_'+record['id'], record['source_sha256_present'] and sha(ROOT/record['source']) == record['source_sha256'])
    require('parent_layers_and_child_database', all(receipt['parent']['readback'].values()))
    require('notion_counts_formal_unchanged', receipt['database_counts'] == {'total':198,'unique_ids':198,'professional':76,'catalog':122,'formal_integrated':9,'backend':1,'pending':112,'views':9})
    for name in ['build_technical_assessment.py','prepare_technical_assessment_notion.py','audit_technical_assessment.py']:
        ast.parse((ROOT/'tools'/name).read_text(encoding='utf-8'))
    unchanged = subprocess.run(['git','diff','--exit-code','--','src','docs/evidence/ladybug_feature_catalog.json','docs/evidence/archive_0107','docs/evidence/notion_home_0107_sync_2026-10-03.json'],cwd=ROOT,capture_output=True,text=True)
    require('product_code_and_prior_acceptance_unchanged', unchanged.returncode == 0)
    whitespace = subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    require('git_diff_check', whitespace.returncode == 0)
    result = {'document':str(doc),'assessment_date':'2026-10-03',
              'checks':checks,'all_passed':all(checks.values()),'local_link_count':len(links),
              'appendix_entries':112,'new_document_bytes':doc.stat().st_size,
              'runtime_tests_rerun':False,'plugin_changed':False,'source_document_sha256':sha(doc)}
    (EV/'document_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    print(json.dumps({k:v for k,v in result.items() if k != 'checks'},ensure_ascii=True))


if __name__ == '__main__':
    main()
