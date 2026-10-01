"""Prepare versioned manifest, package and bounded Rhino MCP replay files."""
import hashlib, json, zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
release=root/'artifacts/releases/0.6.0'
manifest={'version':'0.6.0','plugin':'EnvironmentalHub.Plugin.rhp','plugin_id':'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f',
 'runtime':'Rhino 8 / .NET 8','files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in release.iterdir()
 if f.suffix in ('.dll','.rhp','.json') and f.name!='release_manifest.json'},'dependencies':'Original installed Ladybug / Radiance; no bundled solver.'}
for path in (release/'release_manifest.json',root/'docs/evidence/release_060_manifest.json'):
 path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(root/'artifacts/EnvironmentalHub-0.6.0.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for f in release.iterdir():
  if f.suffix!='.pdb':archive.write(f,f.name)
(root/'tools/release_060_slot_calls.json').write_text(json.dumps([{'name':'spawn_slot','arguments':{}}]),encoding='utf-8')
inspect="""import clr,json
clr.AddReference('Grasshopper')
import Grasshopper as GH
c=GH.Kernel.GH_UserObject('C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects/LB Construct Location.ghuser').InstantiateObject()
print(json.dumps([str(p.Name) for p in c.GetType().GetProperties() if 'code' in p.Name.lower() or 'script' in p.Name.lower()]))
"""
(root/'tools/climate_inspect_calls.json').write_text(json.dumps([{'name':'run_python','arguments':{'slot':'aardvark','script':inspect}}]),encoding='utf-8')
print('0.6.0 package and inspection replay prepared')
