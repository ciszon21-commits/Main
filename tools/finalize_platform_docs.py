"""Current-release documentation only; preserve historical runtime receipts."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
for relative in ['README.md','docs/BUILD_AND_RUN.md','docs/LADYBUG_FEATURE_TABLE.md','docs/LADYBUG_FEATURE_TABLE.html','docs/LADYBUG_DEVELOPMENT_PLAN.md','docs/ROADMAP.md','docs/UI_UX_STANDARD.md','docs/UI_AUDIT_2026-10-01.md']:
 p=root/relative;s=p.read_text(encoding='utf-8')
 for old in ['0.7.1','0.7.2','0.8.0','0.8.2']:s=s.replace(old,'0.8.3')
 for old in ['071','080','082']:s=s.replace('release_'+old+'_loaded.json','release_083_loaded.json').replace('ui_'+old+'/','ui_083/').replace('Release'+old+'.FileListAbsolute.txt','Release083.FileListAbsolute.txt')
 s=s.replace('DLLs are byte-identical between 0.8.3 and 0.8.3','DLLs are byte-identical between 0.7.2 and 0.8.3')
 p.write_text(s,encoding='utf-8')
p=root/'docs/LADYBUG_DEVELOPMENT_PLAN.md';s=p.read_text(encoding='utf-8')
s=s.replace('Hub 目前正式功能為 Incident Radiation、Import EPW、Construct Location、Import STAT 與 Import DDY；','Hub 目前正式功能為 Incident Radiation、Import EPW、Construct Location、Import STAT、Import DDY、Analysis Period、Calculate HOY 與 HOY to DateTime；')
s=s.replace('下一批開發獨立 Analysis Period／HOY、Location 解構及資料工具。','三項獨立時間功能已實測接入；下一批為 Location 解構及資料工具。')
p.write_text(s,encoding='utf-8')
print('Current documentation now points to 0.8.3; historical evidence retained.')
