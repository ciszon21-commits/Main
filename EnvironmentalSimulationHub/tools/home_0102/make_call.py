"""Pin an additional reviewed SDK script to the existing owned test process."""
import json
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
proof = json.loads((root / 'docs/evidence/home_0102/replay_provenance.json').read_text(encoding='utf-8'))
slot = proof['slot']
source = (here / sys.argv[1]).resolve()
source.relative_to(here)
script = ('import System\n'
          f"assert System.Diagnostics.Process.GetCurrentProcess().Id == {slot['pid']}, 'Wrong Rhino process'\n"
          "assert __rhino_doc__.RuntimeSerialNumber == 268435457, 'Wrong test document'\n"
          + source.read_text(encoding='utf-8'))
target = source.with_name(source.stem + '_calls.json')
target.write_text(json.dumps([{'name': 'run_python', 'arguments': {'slot': slot['slotId'], 'script': script}}],
                            ensure_ascii=False, indent=2), encoding='utf-8')
print(target.name)
