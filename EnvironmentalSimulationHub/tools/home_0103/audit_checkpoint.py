"""Audit only this project's staged files and reachable history in the Main checkout."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

def git(*args):
    return subprocess.check_output(['git', *args], cwd=PROJECT)

ROOT = Path(git('rev-parse', '--show-toplevel').decode().strip())
PREFIX = PROJECT.relative_to(ROOT).as_posix() + '/'
entries = [e for e in git('ls-files', '-s', '-z', '--', '.').split(b'\0') if e]
ids = set()
files = []
for entry in entries:
    meta, raw = entry.split(b'\t', 1)
    mode, oid, stage = meta.split()
    name = raw.decode('utf-8')
    assert mode in [b'100644', b'100755'] and stage == b'0', name
    parts = Path(name).parts
    assert not any(p in ['.git', '.codex', '.aws', 'artifacts', 'transfer', 'bin', 'obj', '__pycache__', '.local', '.devtools'] for p in parts), name
    assert Path(name).suffix.lower() not in ['.pem', '.key', '.pfx', '.exe', '.dll', '.rhp', '.zip', '.bundle'], name
    assert not (Path(name).suffix.lower() == '.wea' and any(p in ['home_0102', 'home_0103'] for p in parts)), name
    assert not Path(name).name.startswith('.env') or Path(name).name == '.env.example', name
    ids.add(oid)
    files.append(name)
for entry in git('rev-list', '--objects', 'HEAD', '--', '.').splitlines():
    ids.add(entry.split(b' ', 1)[0])
pattern = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bghp_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}|\bAKIA[A-Z0-9]{16}\b|\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}')
proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=PROJECT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
blobs = maximum = 0
try:
    for oid in sorted(ids):
        proc.stdin.write(oid + b'\n')
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        assert len(header) == 3
        data = proc.stdout.read(int(header[2]))
        assert len(data) == int(header[2]) and proc.stdout.read(1) == b'\n'
        if header[1] == b'blob':
            blobs += 1
            maximum = max(maximum, len(data))
            assert len(data) < 100 * 1024 * 1024, 'Oversized object ' + oid.decode()
            assert not pattern.search(data), 'Credential pattern in object ' + oid.decode() + '; value withheld'
finally:
    proc.stdin.close()
    proc.wait(timeout=10)
report = {'scope': 'Project index and reachable project history; no writes to other Main projects',
    'project_prefix': PREFIX, 'files': len(files), 'blobs_scanned': blobs,
    'max_blob_bytes': maximum, 'high_confidence_credential_patterns': 'NONE_FOUND',
    'forbidden_staged_paths': [], 'inventory_sha256': hashlib.sha256('\n'.join(sorted(files)).encode()).hexdigest(),
    'publication': 'NOT_PERFORMED_BY_AUDIT'}
target = PROJECT / 'docs/evidence/home_0103/checkpoint_audit.json'
target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(report))
