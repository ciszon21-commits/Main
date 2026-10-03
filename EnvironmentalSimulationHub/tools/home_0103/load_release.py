import os, json, System, Rhino
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
spawn = json.load(open(os.path.join(root, 'docs/evidence/home_0103/spawn_transport.json'), encoding='utf-8'))
slot = json.loads(spawn['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert not slot['adopted'] and System.Diagnostics.Process.GetCurrentProcess().Id == slot['pid'], 'Wrong owned process'
doc = __rhino_doc__
assert doc.Path in (None, '') and doc.Objects.Count == 0, 'Fresh test document required'
path = os.path.join(root, 'artifacts/home-build/0.10.3/EnvironmentalHub.Plugin.rhp')
guid = System.Guid('bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f')
Rhino.PlugIns.PlugIn.LoadPlugIn(path)
plugin = Rhino.PlugIns.PlugIn.Find(guid)
assert plugin is not None
assert str(plugin.GetType().Assembly.GetName().Version) == '0.10.3.0'
assert os.path.normcase(os.path.normpath(plugin.GetType().Assembly.Location)) == os.path.normcase(os.path.normpath(path))
proof = {'version': '0.10.3', 'pid': slot['pid'], 'slot': slot['slotId'], 'document_serial': doc.RuntimeSerialNumber,
         'path': plugin.GetType().Assembly.Location, 'rhino': str(Rhino.RhinoApp.Version), 'runtime': str(System.Environment.Version)}
dest = os.path.join(root, 'docs/evidence/home_0103')
os.makedirs(dest, exist_ok=True)
json.dump(proof, open(os.path.join(dest, 'identity.json'), 'w', encoding='utf-8'), indent=2)
print(json.dumps(proof))
