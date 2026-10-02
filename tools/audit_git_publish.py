"""Read-only audit of standalone history/current index before private publication.

Reports filenames/counts only; never prints blob contents or matched secret values.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
git = ['git', '-c', 'safe.directory=' + root.as_posix(), '-C', str(root)]


def run(*args):
    p = subprocess.run(git + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(p.stderr.decode('utf-8', errors='replace')[:1000])
    return p.stdout


assert run('rev-parse', '--show-toplevel').decode().strip().replace('\\', '/') == root.as_posix()
entries = run('ls-files', '-s', '-z').split(b'\0')
files, forbidden = [], []
for entry in entries:
    if not entry:
        continue
    meta, path = entry.split(b'\t', 1)
    mode, oid, stage = meta.split()
    name = path.decode('utf-8')
    files.append(name)
    if mode not in (b'100644', b'100755') or stage != b'0':
        forbidden.append(name)
    parts = Path(name).parts
    if any(p in ('.git', '.codex', '.aws', 'artifacts', 'transfer', 'bin', 'obj', '__pycache__', '.local', '.devtools') for p in parts):
        forbidden.append(name)
    if Path(name).suffix.lower() in ('.pem', '.key', '.pfx', '.exe', '.dll', '.rhp', '.zip', '.bundle') or Path(name).name.startswith('.env') and Path(name).name != '.env.example':
        forbidden.append(name)
if forbidden:
    raise ValueError('Unexpected staged paths: ' + ', '.join(sorted(set(forbidden))))
historical_paths = set(p for p in run('log', 'HEAD', '--format=', '--name-only').decode('utf-8').splitlines() if p)
for name in historical_paths:
    parts = Path(name).parts
    if any(p in ('.git', '.codex', '.aws', 'artifacts', 'transfer', 'bin', 'obj', '__pycache__', '.local', '.devtools') for p in parts):
        raise ValueError('Unexpected historical path requires review: ' + name)
    if Path(name).suffix.lower() in ('.pem', '.key', '.pfx', '.exe', '.dll', '.rhp', '.zip', '.bundle'):
        raise ValueError('Unexpected historical binary/credential path requires review: ' + name)

object_ids = run('rev-list', '--objects', 'HEAD').splitlines()
ids = [row.split(b' ', 1)[0] for row in object_ids]
index_ids = {entry.split(b'\t', 1)[0].split()[1] for entry in entries if entry}
all_ids = sorted(set(ids) | index_ids)
pattern = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bghp_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}|\bAKIA[A-Z0-9]{16}\b|\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}')
blobs, max_bytes = 0, 0
proc = subprocess.Popen(git + ['cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    for oid in all_ids:
        proc.stdin.write(oid + b'\n'); proc.stdin.flush()
        header = proc.stdout.readline().split()
        assert len(header) == 3
        kind, size = header[1], int(header[2])
        data = proc.stdout.read(size)
        assert len(data) == size and proc.stdout.read(1) == b'\n'
        if kind == b'blob':
            blobs += 1
            max_bytes = max(max_bytes, size)
            if size >= 100 * 1024 * 1024:
                raise ValueError('Oversized Git blob; review object ' + oid.decode())
            if pattern.search(data):
                raise ValueError('Possible credential pattern; review object ' + oid.decode() + ' (value withheld)')
finally:
    proc.stdin.close(); proc.wait(timeout=10)
report = {'scope': 'Standalone HEAD history plus staged index; no parent repo writes or network publication',
          'files': len(files), 'blobs_scanned': blobs, 'max_blob_bytes': max_bytes,
          'historical_paths_reviewed': len(historical_paths),
          'high_confidence_credential_patterns': 'NONE_FOUND',
          'forbidden_staged_paths': [], 'github_visibility_verified': False,
          'publication': 'NOT_PERFORMED',
          'file_inventory_sha256': hashlib.sha256('\n'.join(sorted(files)).encode()).hexdigest()}
out = root / 'transfer/git_publish_audit.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
