"""Advance feature states only after the formal climate runtime receipt passes."""
import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1];docs=root/'docs'
receipt=json.loads((docs/'evidence/release_060_loaded.json').read_text(encoding='utf-8'))
assert receipt['version']=='0.6.0' and receipt['climate_passed']==11
assert receipt['climate_gh_cleanup'] and receipt['climate_failure_preserves_result']
catalog_path=docs/'evidence/ladybug_feature_catalog.json'
catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
names={'LB Import STAT','LB Import DDY'}
for e in catalog['components']:
 if e['name'] in names:e['hub_status']='已接入並實測'
assert len(catalog['components'])==122
assert sum(e['hub_status']=='已接入並實測' for e in catalog['components'])==5
catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
path=docs/'LADYBUG_FEATURE_TABLE.md';text=path.read_text(encoding='utf-8')
text='\n'.join(line.replace('待接入 Hub','已接入並實測') if any('| '+name+' |' in line for name in names) else line for line in text.split('\n'))
text=text.replace('目前 0.5.0 Hub 已實測接入 Incident Radiation、獨立 Import EPW Weather Panel 與 Construct Location', '目前 0.6.0 Hub 已實測接入 Incident Radiation、Import EPW、Construct Location、Import STAT 與 Import DDY')
path.write_text(text,encoding='utf-8')
path=docs/'LADYBUG_FEATURE_TABLE.html';text=path.read_text(encoding='utf-8')
data=json.dumps(catalog['components'],ensure_ascii=False).replace('<','\\u003c')
text,count=re.subn(r'const entries=.*?;const box=',lambda _: 'const entries='+data+';const box=',text,count=1,flags=re.S);assert count==1
path.write_text(text,encoding='utf-8')
(root/'artifacts/catalog_check.js').write_text(re.search(r'<script>(.*?)</script>',text,re.S).group(1),encoding='utf-8')
for path in [root/'README.md',docs/'BUILD_AND_RUN.md']:
 text=path.read_text(encoding='utf-8').replace('artifacts/releases/0.5.0','artifacts/releases/0.6.0').replace('EnvironmentalHub-0.5.0.zip','EnvironmentalHub-0.6.0.zip').replace('Release050.FileListAbsolute.txt','Release060.FileListAbsolute.txt')
 text=text.replace('Release 0.5.0 has','Release 0.6.0 has').replace('# Build and run (0.5.0)','# Build and run (0.6.0)').replace('currently 0.5.0.','currently 0.6.0.').replace('release_050_loaded.json` for the current release outcome','release_060_loaded.json` for the current release outcome')
 text+='\nCurrent 0.6.0 also provides EnvironmentalClimate for original STAT / DDY imports. Three-city full native JSON and design-day IDF comparisons plus invalid-input and Panel checks passed; see docs/CLIMATE_FILE_MODULE.md (CLIMATE_FILE_MODULE.md from this docs directory) and release_060_loaded.json.\n'
 path.write_text(text,encoding='utf-8')
print('Catalog advanced: 5 standalone features, 1 backend, 116 pending')
