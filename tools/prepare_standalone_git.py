"""Import only Hub HEAD history into Hub/.git; never modify the parent repo.

Keeps working files untouched. Records source/imported commit mapping and validates
every imported tree plus author/committer/message. All outputs stay under Hub.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'EnvironmentalSimulationHub'
assert ROOT.name == PROJECT
PARENT = ROOT.parent
GIT = ['git', '-c', 'safe.directory=' + PARENT.as_posix(), '-C', str(PARENT)]
LOCAL = ['git', '-c', 'safe.directory=' + ROOT.as_posix(), '-C', str(ROOT)]
OUT = ROOT / 'transfer/git-history'


def run(command, data=None):
    proc = subprocess.run(command, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode('utf-8', errors='replace')[:1500])
    return proc.stdout


def unquote(value):
    value = value.rstrip(b'\n')
    if not value.startswith(b'"'):
        return value
    assert value.endswith(b'"')
    value = value[1:-1]
    escaped = {b'n': b'\n', b'r': b'\r', b't': b'\t', b'b': b'\b', b'f': b'\f', b'v': b'\v', b'a': b'\a', b'\\': b'\\', b'"': b'"'}
    return re.sub(rb'\\([0-7]{3}|.)', lambda m: bytes([int(m[1], 8)]) if len(m[1]) == 3 else escaped[m[1]], value)


def path(value):
    value = unquote(value)
    prefix = (PROJECT + '/').encode()
    if not value.startswith(prefix):
        raise ValueError('Foreign historical path; import stopped')
    value = value[len(prefix):]
    # JSON C quoting is valid here: project filenames contain ordinary UTF-8.
    return json.dumps(value.decode('utf-8'), ensure_ascii=False).encode()


def rewrite(raw):
    src, dest = io.BytesIO(raw), io.BytesIO()
    while line := src.readline():
        if line.startswith(b'data '):
            count = int(line[5:])
            data = src.read(count)
            assert len(data) == count
            dest.write(line); dest.write(data)
            continue
        if line.startswith(b'M '):
            command, mode, mark, name = line.rstrip(b'\n').split(b' ', 3)
            line = b' '.join([command, mode, mark, path(name)]) + b'\n'
        elif line.startswith(b'D '):
            line = b'D ' + path(line[2:]) + b'\n'
        elif line.startswith((b'R ', b'C ')):
            raise ValueError('Unexpected rename/copy directive; use default no-rename export')
        elif line.startswith((b'commit ', b'reset ')):
            command, ref = line.rstrip(b'\n').split(b' ', 1)
            if not ref.startswith(b'refs/heads/'):
                raise ValueError('Unexpected historical ref')
            line = command + b' refs/heads/main\n'
        dest.write(line)
    return dest.getvalue()


def read_marks(file):
    return dict(line.split() for line in file.read_text(encoding='ascii').splitlines())


resume = '--resume-import' in sys.argv
if (ROOT / '.git').exists() and not resume:
    raise SystemExit('Local .git already exists; refusing to replace it')
OUT.mkdir(parents=True, exist_ok=True)
head = run(GIT + ['rev-parse', 'HEAD']).decode().strip()
source_commits = run(GIT + ['rev-list', head]).decode().splitlines()
all_paths = run(GIT + ['log', head, '--format=', '--name-only']).decode('utf-8').splitlines()
assert all(not name or name.startswith(PROJECT + '/') for name in all_paths)
if resume:
    assert (OUT / 'source.marks').is_file() and (OUT / 'imported.marks').is_file()
    assert run(LOCAL + ['rev-parse', '--show-toplevel']).decode().strip().replace('\\', '/') == ROOT.as_posix()
    marks_a, marks_b = read_marks(OUT / 'source.marks'), read_marks(OUT / 'imported.marks')
    baseline = {old: marks_b[mark] for mark, old in marks_a.items()}[head]
    assert run(LOCAL + ['rev-parse', 'master']).decode().strip() == baseline
    run(LOCAL + ['branch', '-m', 'master', 'main'])
    stream = (OUT / 'project.fast-export').read_bytes()
else:
    raw = run(GIT + ['fast-export', '--export-marks=' + str(OUT / 'source.marks'), 'HEAD', '--', PROJECT])
    stream = rewrite(raw)
    (OUT / 'project.fast-export').write_bytes(stream)
    run(LOCAL + ['init', '--initial-branch=main'])
    run(LOCAL + ['fast-import', '--quiet', '--export-marks=' + str(OUT / 'imported.marks')], stream)
run(LOCAL + ['config', '--local', 'user.name', 'Codex'])
run(LOCAL + ['config', '--local', 'user.email', 'codex@openai.com'])
run(LOCAL + ['config', '--local', 'core.longpaths', 'true'])
run(LOCAL + ['config', '--local', 'core.autocrlf', 'input'])
run(LOCAL + ['read-tree', 'main'])
source_marks, imported_marks = read_marks(OUT / 'source.marks'), read_marks(OUT / 'imported.marks')
mapping = {old: imported_marks[mark] for mark, old in source_marks.items()}
assert set(mapping) == set(source_commits)
for old, new in mapping.items():
    old_tree = run(GIT + ['rev-parse', old + ':' + PROJECT]).strip()
    new_tree = run(LOCAL + ['rev-parse', new + '^{tree}']).strip()
    assert old_tree == new_tree, old
    form = '%an%n%ae%n%at%n%ai%n%cn%n%ce%n%ct%n%ci%n%B'
    assert run(GIT + ['show', '-s', '--format=' + form, old]) == run(LOCAL + ['show', '-s', '--format=' + form, new]), old
assert run(GIT + ['rev-parse', 'HEAD']).decode().strip() == head
report = {'source_parent_head': head, 'standalone_baseline_head': mapping[head],
          'imported_commits': len(mapping), 'all_commit_subtree_hashes_match': True,
          'author_committer_dates_messages_preserved': True,
          'source_parent_head_unchanged': True, 'working_files_not_checked_out_or_replaced': True,
          'commit_ids_changed_reason': 'Removed EnvironmentalSimulationHub path prefix; new root trees/parents',
          'codex_checkpoint_refs_imported': False, 'commits': mapping,
          'export_sha256': hashlib.sha256(stream).hexdigest()}
(ROOT / 'docs/evidence/standalone_git_import_20261002.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'commits'}, indent=2))
