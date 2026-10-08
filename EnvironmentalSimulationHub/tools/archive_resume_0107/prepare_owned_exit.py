from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]; here=Path(__file__).resolve().parent
identity=json.loads((root/'docs/evidence/archive_resume_0107/identity.json').read_text(encoding='utf-8'))
spawn=json.loads((root/'docs/evidence/archive_resume_0107/spawn_transport.json').read_text(encoding='utf-8'))
owned=json.loads(spawn['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert not owned['adopted'] and owned['pid']==identity['pid'] and owned['slotId']==identity['slot']
script=(here/'common.py').read_text(encoding='utf-8')+'''
assert not list(doc.Objects) and not doc.Modified
assert identity['pid']==20924
proof={'pid':identity['pid'],'document_serial':doc.RuntimeSerialNumber,'original_spawn_non_adopted':True,'empty_unmodified':True,'method':'Rhino native Exit after router re-adoption blocked close_slot'}
json.dump(proof,open(os.path.join(evidence,'owned_exit_guard.json'),'w',encoding='utf-8'),indent=2)
Rhino.RhinoApp.RunScript('_Exit',False)
'''
(here/'owned_exit_calls.json').write_text(json.dumps([{'name':'run_python','arguments':{'slot':identity['slot'],'script':script}}],ensure_ascii=False),encoding='utf-8')
