from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
receipt=json.loads((root/'docs/evidence/release_085_loaded.json').read_text(encoding='utf-8'))
script='\n'.join((root/'tools'/name).read_text(encoding='utf-8') for name in ['validate_platform_ui.py','validate_hub_navigation.py','validate_topic_palette.py','capture_hub_native_panels.py'])
(root/'tools/ui_acceptance_calls.json').write_text(json.dumps([{'name':'run_python','arguments':{'slot':receipt['slot'],'script':script}}],indent=2),encoding='utf-8')
