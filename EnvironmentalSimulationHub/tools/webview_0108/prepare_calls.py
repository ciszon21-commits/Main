"""Bind each new test call to the freshly spawned, non-adopted Rhino PID/document."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
evidence = root / 'docs/evidence/webview_0108/fixed'
spawn = json.loads((evidence / 'spawn_transport.json').read_text(encoding='utf-8'))
slot = json.loads(spawn['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert slot['adopted'] is False
assert any(t['name'] == 'run_python' and 'script' in t['inputSchema']['properties'] for t in spawn['tools']['result']['tools'])
mode = sys.argv[1]
prefix = f'''import json, os, System, Rhino, scriptcontext as sc
root = {str(root.as_posix())!r}
evidence = os.path.join(root, 'docs/evidence/webview_0108/fixed')
assert System.Diagnostics.Process.GetCurrentProcess().Id == {slot['pid']}
doc = __rhino_doc__
assert doc is not None and doc.Objects.Count == 0
'''
if mode != 'identity':
    identity = json.loads((evidence / 'identity.json').read_text(encoding='utf-8'))
    assert identity['pid'] == slot['pid']
    prefix += f'assert doc.RuntimeSerialNumber == {identity["document_serial"]}\n'
script = prefix + (here / (mode + '.py')).read_text(encoding='utf-8')
if mode == 'capture':
    width, theme = int(sys.argv[2]), sys.argv[3]
    assert width in (320, 480) and theme in ('light', 'dark')
    script = prefix + f'capture_width = {width}\ncapture_theme = {theme!r}\n' + (here / 'capture.py').read_text(encoding='utf-8')
(here / (mode + '_calls.json')).write_text(json.dumps([{'name': 'run_python', 'arguments': {'slot': slot['slotId'], 'script': script}}], ensure_ascii=False), encoding='utf-8')
print(json.dumps({'mode': mode, 'slot': slot['slotId'], 'pid': slot['pid']}))
