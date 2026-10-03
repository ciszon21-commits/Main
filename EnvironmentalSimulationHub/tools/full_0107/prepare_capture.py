import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]; here=Path(__file__).resolve().parent
identity=json.loads((root/'docs/evidence/full_0107/identity.json').read_text(encoding='utf-8'))
call=json.loads((root/'tools/full_0107/capture_workspace_full_0107_calls.json').read_text(encoding='utf-8'))[0]
script=call['arguments']['script']
start=script.index('for (name, command, guid) in modules:')
script=script[:start]+"modules = [item for item in modules if item[0]=='sunhours_compare']\n"+script[start:]
call['arguments']['script']=script
(here/'capture_comparison_calls.json').write_text(json.dumps([call],ensure_ascii=False),encoding='utf-8')
