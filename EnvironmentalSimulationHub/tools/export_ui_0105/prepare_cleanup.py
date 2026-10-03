import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
identity = json.loads((root / 'docs/evidence/export_ui_0105/identity.json').read_text(encoding='utf-8'))
script = (here / 'common.py').read_text(encoding='utf-8') + '''
for obj in list(doc.Objects):
    assert doc.Objects.Delete(obj.Id,True)
doc.Modified = False
assert len(list(doc.Objects)) == 0 and not doc.Modified
print(json.dumps({'pid':identity['pid'],'owned_objects_removed':True,'empty_unmodified':True}))
'''
(here / 'cleanup_calls.json').write_text(json.dumps([
    dict(name='run_python',arguments=dict(slot=identity['slot'],script=script)),
    dict(name='close_slot',arguments=dict(slot=identity['slot']))],ensure_ascii=False),encoding='utf-8')
