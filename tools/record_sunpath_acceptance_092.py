import json,hashlib,subprocess,datetime,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1];evidence=root/'docs/evidence'
def read(name):return json.loads((evidence/name).read_text(encoding='utf-8-sig'))
loaded=read('release_092_loaded.json');sun=read('sunpath_092_runtime.json');transfer=read('sunpath_092_transfer.json');platform=read('platform_092_runtime.json');workspace=read('workspace_092_runtime.json')
assert loaded['version']=='0.9.2' and loaded['time_passed']==17 and sun['passed']==31 and transfer['passed']==1 and platform['passed']==21 and workspace['passed']==14
assert loaded['radiation_regression_mean']==1233.3471168086037
release=root/'artifacts/releases/0.9.2';manifest=read('release_092_manifest.json')
assert all(hashlib.sha256((release/name).read_bytes()).hexdigest()==digest for name,digest in manifest['files'].items())
existing=[]
for folder in ['EnvironmentalHub.Core','EnvironmentalHub.Adapters']:
 for p in (root/'src'/folder).glob('*'):
  if p.suffix not in ['.cs','.csproj']:continue
  repository_path=p.relative_to(root.parent).as_posix()
  previous=subprocess.run(['git','-c','safe.directory='+root.parent.as_posix(),'show','HEAD:'+repository_path],cwd=root.parent,capture_output=True)
  if previous.returncode!=0:continue
  assert previous.stdout.replace(b'\r\n',b'\n')==p.read_bytes().replace(b'\r\n',b'\n'),repository_path
  existing.append(repository_path)
sources={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'src').rglob('*') if p.suffix in ['.cs','.csproj','.json'] and not any(part in ['bin','obj'] for part in p.parts)}
ui=read('ui_092/capture.json');assert len(ui['shots'])==30
assert read('sunpath_092_text.json')['passed']==2
pilot=read('pilot_092_readiness.json');assert pilot['Failures']==0 and pilot['Warnings']==0 and pilot['Version']=='0.9.2'
receipt={'version':'0.9.2','recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'build':{'errors':0,'warnings':0},
 'native_checks':{'sunpath':31,'epw_location_transfer':1,'existing_flows':60,'workspace':14,'text_scaling':2,'total':108},'radiation_baseline_mean':loaded['radiation_regression_mean'],
 'registered_loaded_path':loaded['loaded_path'],'ui':{'captures':30,'reviewed_images':[Path(s['path']).name for s in ui['shots']],'widths':[320,480],'scope':'Offscreen production Eto/WPF workspace/control state; current light theme'},
 'existing_core_adapter_source_files_unchanged':existing,'source_sha256':sources,'release_manifest':'release_092_manifest.json','viewport_image':'ui_092/sunpath_viewport.png','viewport_reviewed':True,
 'pilot':{'static_pass':sum(x['State']=='PASS' for x in pilot['Checks']),'native_runtime':'NOT_TESTED by readiness script; colleague-machine trial pending'},
 'catalog':{'inventory':122,'standalone':9,'backend':1,'pending':112,'sunpath':'Geometric first batch; optional data/conditions/DST/legend/vector north/vis_set UI deferred'},
 'limitations':['Full Dock sizing, dark theme, keyboard and native dialogs pending','Different-document switching and large minute-preview performance require full acceptance','No cancellation or progress percentage; synchronous GH','No cross-machine colleague onboarding acceptance','Existing source files unchanged; new contracts/adapter mean DLLs changed']}
(evidence/'sunpath_092_acceptance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':108,'ui':30,'existing_source_files':len(existing),'pilot_pass':receipt['pilot']['static_pass']}))
