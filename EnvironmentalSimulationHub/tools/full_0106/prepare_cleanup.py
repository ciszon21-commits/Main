import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]; here=Path(__file__).resolve().parent
identity=json.loads((root/'docs/evidence/full_0106/identity.json').read_text(encoding='utf-8'))
assert identity['slot'] and identity['pid']
script='''import System, Rhino, os, json
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
identity=json.load(open(os.path.join(root,'docs/evidence/full_0106/identity.json'),encoding='utf-8'))
assert System.Diagnostics.Process.GetCurrentProcess().Id==identity['pid']
doc=__rhino_doc__
assert doc.RuntimeSerialNumber==identity['document_serial'] and doc.Path in (None,'')
allowed=set()
def collect(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if key in ('GeometryIds','ContextIds') and isinstance(item,list): allowed.update(str(x).lower() for x in item)
            collect(item)
    elif isinstance(value,list):
        for item in value: collect(item)
for base in ['samples/full_0106','docs/evidence/full_0106/runtime']:
    for folder,dirs,files in os.walk(os.path.join(root,base)):
        for name in files:
            if name.endswith('.json'):
                try: collect(json.load(open(os.path.join(folder,name),encoding='utf-8-sig')))
                except (ValueError,UnicodeError): pass
objects=list(doc.Objects)
proof=[]
for obj in objects:
    tag=obj.Attributes.GetUserString('EnvironmentalHub.PreviewOwner')
    owned=str(obj.Id).lower() in allowed or (tag is not None and tag.startswith('bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f/'))
    proof.append({'id':str(obj.Id),'owned':owned,'crc':str(obj.Geometry.DataCRC(0)),'tag':tag})
json.dump({'pid':identity['pid'],'live_objects':proof},open(os.path.join(root,'docs/evidence/full_0106/cleanup_inventory.json'),'w',encoding='utf-8'),indent=2)
assert all(o['owned'] for o in proof),'Unrecognized object; do not close or delete'
for obj in objects: assert doc.Objects.Delete(obj.Id,True)
doc.Modified=False
assert not list(doc.Objects) and not doc.Modified
print(json.dumps({'pid':identity['pid'],'owned_objects_removed':len(objects),'empty_unmodified':True}))
'''
(here/'cleanup_calls.json').write_text(json.dumps([
    dict(name='run_python',arguments=dict(slot=identity['slot'],script=script)),
    dict(name='close_slot',arguments=dict(slot=identity['slot']))],ensure_ascii=False),encoding='utf-8')
