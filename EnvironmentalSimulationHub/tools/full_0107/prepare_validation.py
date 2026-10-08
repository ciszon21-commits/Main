"""Rebase the already corrected home suites into a fresh version/process/output scope."""
import hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EV = ROOT / 'docs/evidence/full_0107'
identity = json.loads((EV / 'identity.json').read_text(encoding='utf-8'))
spawn = json.loads((EV / 'spawn_transport.json').read_text(encoding='utf-8'))
slot = json.loads(spawn['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert not slot['adopted'] and slot['pid'] == identity['pid'] and slot['slotId'] == identity['slot']
sources = ['release_home_0102_calls.json', 'sunhours_existing_home_0102_calls.json',
           'sunhours_existing_home_0102_remainder_calls.json', 'sunhours_home_0102_calls.json',
           'sunhours_workspace_home_0102_calls.json', 'capture_workspace_home_0102_calls.json',
           'capture_sunhours_viewport_home_0102_calls.json', 'export_fixture_calls.json']
records = []
for name in sources:
    source = ROOT / 'tools/home_0102' / name
    calls = json.loads(source.read_text(encoding='utf-8'))
    for call in calls:
        call['arguments']['slot'] = identity['slot']
        script = call['arguments']['script'].replace('home_0102', 'full_0107').replace('0.10.2', '0.10.7')
        script = script.replace('== 29180', '== ' + str(identity['pid']))
        script = script.replace('== 268435457', '== ' + str(identity['document_serial']))
        script = script.replace("'aardvark'", repr(identity['slot']))
        # Verify the explicitly loaded candidate; record the SDK's registration separately.
        if name == 'release_home_0102_calls.json':
            registration_guard = "if os.path.normcase(os.path.normpath(Rhino.PlugIns.PlugIn.PathFromId(guid))) != os.path.normcase(os.path.normpath(path)):\n    raise RuntimeError('Wrong registration')"
            assert registration_guard in script
            script = script.replace(registration_guard, "registered_path = Rhino.PlugIns.PlugIn.PathFromId(guid)")
            script = script.replace("report['language'] = 'zh-TW'", "report['registered_path'] = registered_path\nreport['candidate_load_only'] = True\nreport['language'] = 'zh-TW'")
        call['arguments']['script'] = script
        if name == 'sunhours_workspace_home_0102_calls.json':
            legacy = "Rhino.UI.Panels.ClosePanel(workspace_id)\nRhino.RhinoApp.RunScript('EnvironmentalWeather', False)\nassert System.Object.ReferenceEquals(workspace, Rhino.UI.Panels.GetPanel(workspace_id))"
            replacement = "Rhino.UI.Panels.ClosePanel(workspace_id)\nRhino.RhinoApp.RunScript('EnvironmentalWeather', False)\nworkspace = Rhino.UI.Panels.GetPanel(workspace_id)\nassert all(System.Object.ReferenceEquals(view, workspace.GetModule(t)) for t, view in zip(types, views))"
            if legacy in script:
                call['arguments']['script'] = script.replace(legacy, replacement)
    target = HERE / name.replace('home_0102', 'full_0107')
    target.write_text(json.dumps(calls, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    records.append({'source': source.relative_to(ROOT).as_posix(), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                    'target': target.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
for folder in ['radiation_smoke', 'weather_0101']:
    (ROOT / 'samples/full_0107' / folder).mkdir(parents=True, exist_ok=True)
shutil.copyfile(ROOT / 'samples/radiation_smoke/runtime_result.json', ROOT / 'samples/full_0107/radiation_smoke/runtime_result.json')
(EV / 'runtime').mkdir(parents=True, exist_ok=True)
(EV / 'replay_provenance.json').write_text(json.dumps({'identity': identity, 'sources': records}, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print(json.dumps({'prepared': len(records), 'slot': identity['slot'], 'pid': identity['pid']}))

native = []
for name in sources[:4]:
    native.extend(json.loads((HERE / name.replace('home_0102', 'full_0107')).read_text(encoding='utf-8')))
native.append({'name': 'run_python', 'arguments': {'slot': identity['slot'],
               'script': (HERE / 'selection_rebind_checks.py').read_text(encoding='utf-8')}})
native.extend(json.loads((HERE / 'sunhours_workspace_full_0107_calls.json').read_text(encoding='utf-8')))
(HERE / 'native_regression_calls.json').write_text(json.dumps(native, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
presentation = []
for name in sources[5:]:
    presentation.extend(json.loads((HERE / name.replace('home_0102', 'full_0107')).read_text(encoding='utf-8')))
(HERE / 'presentation_export_calls.json').write_text(json.dumps(presentation, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
