"""Publish time feature states after formal native acceptance."""
import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1];docs=root/'docs'
receipt=json.loads((docs/'evidence/release_072_loaded.json').read_text(encoding='utf-8'))
assert receipt['time_passed']==17 and receipt['overview_visible'] and receipt['time_gh_cleanup']
names={'LB Analysis Period','LB Calculate HOY','LB HOY to DateTime'}
path=docs/'evidence/ladybug_feature_catalog.json';catalog=json.loads(path.read_text(encoding='utf-8'))
assert len([e for e in catalog['components'] if e['name'] in names])==3
for entry in catalog['components']:
 if entry['name'] in names:entry['hub_status']='已接入並實測'
assert len(catalog['components'])==122 and sum(e['hub_status']=='已接入並實測' for e in catalog['components'])==8
path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
path=docs/'LADYBUG_FEATURE_TABLE.md';text=path.read_text(encoding='utf-8')
text='\n'.join(line.replace('待接入 Hub','已接入並實測') if any('| '+name+' |' in line for name in names) else line for line in text.split('\n'))
text=text.replace('目前 0.6.0 Hub 已實測接入 Incident Radiation、Import EPW、Construct Location、Import STAT 與 Import DDY','目前 0.7.2 Hub 已實測接入 Incident Radiation、Import EPW、Construct Location、Import STAT、Import DDY、Analysis Period、Calculate HOY 與 HOY to DateTime')
path.write_text(text,encoding='utf-8')
path=docs/'LADYBUG_FEATURE_TABLE.html';text=path.read_text(encoding='utf-8');data=json.dumps(catalog['components'],ensure_ascii=False).replace('<','\\u003c')
text,n=re.subn(r'const entries=.*?;const box=',lambda _: 'const entries='+data+';const box=',text,count=1,flags=re.S);assert n==1
path.write_text(text,encoding='utf-8');(root/'artifacts/catalog_check.js').write_text(re.search(r'<script>(.*?)</script>',text,re.S).group(1),encoding='utf-8')
for path in [root/'README.md',docs/'BUILD_AND_RUN.md']:
 text=path.read_text(encoding='utf-8').replace('artifacts/releases/0.6.0','artifacts/releases/0.7.2').replace('EnvironmentalHub-0.6.0.zip','EnvironmentalHub-0.7.2.zip').replace('Release060.FileListAbsolute.txt','Release072.FileListAbsolute.txt')
 text=text.replace('Release 0.6.0 has','Release 0.7.2 has').replace('# Build and run (0.6.0)','# Build and run (0.7.2)').replace('currently 0.6.0.','currently 0.7.2.').replace('release_060_loaded.json` for the current release outcome','release_072_loaded.json` for the current release outcome')
 text=text.replace('command `EnvironmentalHub` to open the loaded panel','command `EnvironmentalRadiation` to open the radiation panel').replace('`EnvironmentalHub` opens radiation','`EnvironmentalRadiation` opens radiation')
 text+='\n0.7.2 unified entry: EnvironmentalHub opens the overview; EnvironmentalRadiation opens radiation directly. EnvironmentalTime provides original period and date/HOY tools. All panels share navigation and styling; source/result state remains module-specific. See TIME_AND_HUB_MODULE.md in docs for native runtime and UI capture scope.\n'
 path.write_text(text,encoding='utf-8')
print('Catalog advanced: 8 standalone features, 1 backend, 113 pending')
