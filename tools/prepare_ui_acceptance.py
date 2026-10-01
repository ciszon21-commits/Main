from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
receipt=json.loads((root/'docs/evidence/release_083_loaded.json').read_text(encoding='utf-8'))
script=(root/'tools/validate_hub_navigation.py').read_text(encoding='utf-8')+'\n'+(root/'tools/capture_hub_native_panels.py').read_text(encoding='utf-8')
(root/'tools/ui_acceptance_calls.json').write_text(json.dumps([{'name':'run_python','arguments':{'slot':receipt['slot'],'script':script}}],indent=2),encoding='utf-8')
