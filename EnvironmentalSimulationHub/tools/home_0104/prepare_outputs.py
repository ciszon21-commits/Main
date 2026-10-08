from pathlib import Path

root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
source = root / 'tools/home_0103/record_validation.py'
text = source.read_text(encoding='utf-8').replace('home_0103', 'home_0104').replace('0.10.3', '0.10.4')
text = text.replace("suites['selection_rebind'] = rebind['passed']", "suites['selection_rebind'] = rebind['passed']\nwidth = read(EV / 'floating_width_checks.json')\nassert width['passed'] == 6 and width['pid'] == identity['pid']\nsuites['floating_width'] = width['passed']")
text = text.replace("ROOT / 'src/EnvironmentalHub.Plugin/SunHoursPanel.cs'", "ROOT / 'src/EnvironmentalHub.Plugin/HubWorkspacePanel.cs'")
text = text.replace("'full_native_dock': 'NOT_ACCEPTED'", "'floating_initial_width': '500 outer / 490 content; 6 native checks passed',\n    'narrow_layout_issues': ['320 px workspace home button clipped', '320 px time period end column clipped', 'some numeric spinners clipped at 320 px'],\n    'full_native_dock': 'NOT_ACCEPTED: OpenPanelAsSibling returned false'")
text = text.replace("'initial narrow container width UI-WIDTH-0103'", "'remaining narrow layout UI-NARROW-0104'")
text = text.replace("'scope': 'Production offscreen controls and real 3D viewport; full native interaction remains pending'", "'scope': '44 production offscreen controls and 2 real viewports reviewed; narrow clipping remains. Native floating width verified separately; complete UI is pending'")
text = text.replace('全平台 161 項', '全平台 167 項（含浮動寬度 6 項）')
text = text.replace('完整原生 UI 待驗收', '初始浮動寬度已修正，窄版及完整原生 UI 待驗收')
(here / 'record_validation.py').write_text(text, encoding='utf-8', newline='\n')
text = (root / 'tools/home_0103/normalize_export_newlines.py').read_text(encoding='utf-8')
text = text.replace("['home_0102', 'home_0103']", "['home_0104']").replace('evidence/home_0103', 'evidence/home_0104')
(here / 'normalize_export_newlines.py').write_text(text, encoding='utf-8', newline='\n')
