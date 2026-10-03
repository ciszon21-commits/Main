"""Create a home-machine replay without editing historical scripts or receipts."""
import ast
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'docs/evidence/home_0102'
SOURCE_ROOT = 'C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'


def adapt(value, slot):
    normalized = value.replace('\\', '/')
    while '//' in normalized:
        normalized = normalized.replace('//', '/')
    if SOURCE_ROOT in normalized:
        value = normalized.replace(SOURCE_ROOT, ROOT.as_posix())
    value = value.replace('artifacts/releases/0.10.1', 'artifacts/home-build/0.10.2')
    value = value.replace('docs/evidence/', 'docs/evidence/home_0102/runtime/')
    value = value.replace('samples/', 'samples/home_0102/')
    if value == 'evidence':
        value = 'evidence/home_0102/runtime'
    elif value == 'samples':
        value = 'samples/home_0102'
    elif value == 'releases':
        value = 'home-build'
    elif value == 'armadillo':
        value = slot
    return value.replace('0.10.1', '0.10.2')


class Rebase(ast.NodeTransformer):
    def __init__(self, slot):
        self.slot = slot

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = adapt(node.value, self.slot)
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        if len(node.comparators) == 1 and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id == 'path':
            # Windows accepts mixed separators; assembly paths use backslashes.
            def normalize(expr):
                return ast.Call(func=ast.parse('os.path.normcase').body[0].value,
                                args=[ast.Call(func=ast.parse('os.path.normpath').body[0].value,
                                               args=[expr], keywords=[])], keywords=[])
            node.left = normalize(node.left)
            node.comparators[0] = normalize(node.comparators[0])
        return node


spawn = json.loads((EVIDENCE / 'spawn_transport.json').read_text(encoding='utf-8'))
response = spawn['calls'][0]['response']['result']
assert not response.get('isError'), response
payload = json.loads(response['content'][0]['text'])['payload']
assert not payload['adopted'], 'Only a newly spawned test Rhino may be used'
slot = payload['slotId']
(EVIDENCE / 'runtime').mkdir(parents=True, exist_ok=True)
fixture_dir = ROOT / 'samples/home_0102/radiation_smoke'
fixture_dir.mkdir(parents=True, exist_ok=True)
(ROOT / 'samples/home_0102/weather_0101').mkdir(parents=True, exist_ok=True)
shutil.copyfile(ROOT / 'samples/radiation_smoke/runtime_result.json', fixture_dir / 'runtime_result.json')

sources = ['release_0101_calls.json', 'sunhours_existing_0101_calls.json',
           'sunhours_existing_0101_remainder_calls.json',
           'sunhours_0101_calls.json', 'sunhours_workspace_0101_calls.json',
           'capture_workspace_0101_calls.json',
           'capture_sunhours_viewport_0101_calls.json']
provenance = []
for source in sources:
    raw = (ROOT / 'tools' / source).read_bytes()
    calls = json.loads(raw)
    if source == 'sunhours_existing_0101_calls.json':
        # Only the platform phase belongs here. The corrected remainder phase
        # explicitly permits its owned document to retain the radiation fixture.
        calls = calls[:1]
    if source == 'sunhours_workspace_0101_calls.json':
        # Keep platform and visual-fixture stages separate from UI rendering.
        calls = calls[:2]
    for index, call in enumerate(calls):
        assert call['name'] == 'run_python'
        call['arguments']['slot'] = slot
        tree = Rebase(slot).visit(ast.parse(call['arguments']['script']))
        script = ast.unparse(ast.fix_missing_locations(tree))
        # The combined historical calls predate the eighth homepage action.
        script = script.replace("['開始日射分析', '開啟太陽路徑']",
                                "['開始日射分析', '開啟太陽路徑', '開啟日照時數']")
        # The source machine used centimetres; a home document may already use mm.
        # A negative unit-change check must actually change the unit system.
        script = script.replace(
            'doc.ModelUnitSystem = Rhino.UnitSystem.Millimeters\n    try:\n        panel.ExecuteJson',
            'doc.ModelUnitSystem = (Rhino.UnitSystem.Meters if old_units == Rhino.UnitSystem.Millimeters else Rhino.UnitSystem.Millimeters)\n    try:\n        panel.ExecuteJson')
        script = script.replace(
            'doc.AdjustModelUnitSystem(Rhino.UnitSystem.Millimeters, False)\n    try:\n        failed',
            'doc.AdjustModelUnitSystem(Rhino.UnitSystem.Meters if units == Rhino.UnitSystem.Millimeters else Rhino.UnitSystem.Millimeters, False)\n    try:\n        failed')
        # Every replay invocation is pinned to the process created by this run.
        guard = ('import System, Rhino\n'
                 f"assert System.Diagnostics.Process.GetCurrentProcess().Id == {payload['pid']}, 'Wrong Rhino process'\n"
                 "assert __rhino_doc__.RuntimeSerialNumber == 268435457, 'Wrong test document'\n"
                 "assert __rhino_doc__.Path in (None, ''), 'Only the owned unsaved test document is allowed'\n")
        call['arguments']['script'] = guard + script
        (HERE / (source.replace('_calls.json', '') + f'_{index}.py')).write_text(guard + script, encoding='utf-8')
    target = HERE / source.replace('0101', 'home_0102')
    target.write_text(json.dumps(calls, ensure_ascii=False, indent=2), encoding='utf-8')
    provenance.append({'source': source, 'source_sha256': hashlib.sha256(raw).hexdigest(),
                       'generated': target.relative_to(ROOT).as_posix(),
                       'generated_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                       'calls': len(calls)})
(EVIDENCE / 'replay_provenance.json').write_text(json.dumps({
    'version': '0.10.2', 'slot': payload, 'source_root': SOURCE_ROOT,
    'home_root': ROOT.as_posix(), 'output_scope': 'samples/home_0102 and docs/evidence/home_0102',
    'historical_evidence_modified': False, 'replays': provenance
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'slot': slot, 'pid': payload['pid'], 'prepared': len(sources)}))
