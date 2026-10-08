from pathlib import Path

root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
text = (root / 'tools/home_0103/record_validation.py').read_text(encoding='utf-8')
text = text.replace('home_0103', 'home_0105').replace('0.10.3', '0.10.5')
text = text.replace('HOME_VALIDATION_0103.md', 'HOME_VALIDATION_0105.md')
text = text.replace("suites['selection_rebind'] = rebind['passed']", "suites['selection_rebind'] = rebind['passed']\nwidth = read(EV / 'floating_width_checks.json')\nassert width['passed'] == 7 and width['pid'] == identity['pid']\nsuites['floating_width'] = width['passed']")
text = text.replace("ROOT / 'src/EnvironmentalHub.Plugin/SunHoursPanel.cs'", "ROOT / 'src/EnvironmentalHub.Plugin/HubWorkspacePanel.cs'")
text = text.replace("'full_native_dock': 'NOT_ACCEPTED'", "'floating_initial_width': '500 outer / 490 content; 7 native checks passed',\n    'full_native_dock': 'NOT_ACCEPTED'")
text = text.replace("'initial narrow container width UI-WIDTH-0103', ", '')
text = text.replace('全平台 161 項', '全平台 168 項（含浮動寬度 7 項）')
text = text.replace('完整原生 UI 待驗收', '初始浮動寬度已修正，完整原生 UI 待驗收')
text = text.replace("'historical_receipts_modified': False", "'historical_receipts_modified': False,\n    'width_issue': {'id': 'UI-WIDTH-0103', 'status': 'FLOATING_FIXED_NATIVE_VISUAL_QA_PENDING', 'scope': 'Measured actual floating container; docked layout not accepted'},\n    'rejected_intermediate_candidate': 'home_0104/candidate_disposition.json'")
(here / 'record_validation.py').write_text(text, encoding='utf-8', newline='\n')
text = (root / 'tools/home_0103/normalize_export_newlines.py').read_text(encoding='utf-8')
text = text.replace("['home_0102', 'home_0103']", "['home_0105']").replace('evidence/home_0103', 'evidence/home_0105')
(here / 'normalize_export_newlines.py').write_text(text, encoding='utf-8', newline='\n')
