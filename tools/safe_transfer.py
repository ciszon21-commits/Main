"""Project-only snapshot, integrity verification and non-overwriting extraction.

No registry, network, process control, vendor installation or parent-repository writes.
Uses Python standard library only. Run --help for commands.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile

PROJECT = 'EnvironmentalSimulationHub'
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT + '/TRANSFER_MANIFEST.json'
MAX_BYTES = 1024 ** 3
SKIP_PARTS = {'.git', '.codex', '.agents', '.aws', 'bin', 'obj', '__pycache__', '.venv', 'node_modules'}
RELEASES = {'0.9.2', '0.10.1', '0.10.2'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def native_path(path):
    """Windows extended-length I/O without altering OS/global long-path settings."""
    path = Path(path).absolute()
    value = str(path)
    if os.name == 'nt' and not value.startswith('\\\\?\\'):
        return Path('\\\\?\\UNC\\' + value[2:] if value.startswith('\\\\') else '\\\\?\\' + value)
    return path


def linked(path):
    return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)


def contained(path, root):
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        raise ValueError('Path outside project/destination: ' + str(path))


def checked_name(name):
    parts = PurePosixPath(name).parts
    if (not parts or parts[0] != PROJECT or name != '/'.join(parts)
            or '\\' in name or any(p in ('', '.', '..') or len(p) > 255 or any(c in p for c in ':*?"<>|') or any(ord(c) < 32 for c in p)
            or p.endswith((' ', '.')) or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)', p, re.I)
            for p in parts) or any(p.lower() in SKIP_PARTS for p in parts)):
        raise ValueError('Unsafe archive entry: ' + name)
    return parts


def snapshot_files():
    if ROOT.name != PROJECT or linked(ROOT):
        raise ValueError('Pack tool must run from the original project tools directory')
    files, omitted = [], []
    for folder, dirs, names in os.walk(ROOT, followlinks=False):
        base = Path(folder)
        kept = []
        for name in sorted(dirs):
            path = base / name
            rel = path.relative_to(ROOT).as_posix()
            if name in SKIP_PARTS or rel == 'transfer' or rel == 'samples/reliability_validation':
                omitted.append({'path': rel, 'reason': 'rebuildable/cache or transfer output'})
                continue
            if linked(path):
                raise ValueError('Refusing project reparse point: ' + rel)
            if rel == 'artifacts':
                kept.append(name)
                continue
            if rel.startswith('artifacts/'):
                if rel != 'artifacts/releases' and not any(rel == 'artifacts/releases/' + v or rel.startswith('artifacts/releases/' + v + '/') for v in RELEASES):
                    omitted.append({'path': rel, 'reason': 'historical/rebuildable artifact; retained on source machine'})
                    continue
            kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = base / name
            rel = path.relative_to(ROOT).as_posix()
            if linked(path):
                raise ValueError('Refusing project reparse point: ' + rel)
            if rel.startswith('artifacts/') and not any(rel.startswith('artifacts/releases/' + v + '/') for v in RELEASES):
                omitted.append({'path': rel, 'reason': 'historical/rebuildable artifact'})
                continue
            if path.suffix in ('.pyc', '.pdb', '.log', '.wea') or name == '.DS_Store':
                omitted.append({'path': rel, 'reason': 'rebuildable/debug output'})
                continue
            if name.lower().startswith('.env') or path.suffix.lower() in ('.pfx', '.pem', '.key'):
                raise ValueError('Credential-like file requires review: ' + rel)
            contained(path, ROOT)
            checked_name(PROJECT + '/' + rel)
            if path.suffix.lower() in ('.py', '.ps1', '.json', '.txt', '.md', '.cs', '.config'):
                content = path.read_text(encoding='utf-8-sig', errors='replace')
                if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bghp_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}|\bAKIA[A-Z0-9]{16}\b|\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}', content):
                    raise ValueError('Possible credential content requires review: ' + rel)
            files.append(path)
    return sorted(files), omitted


def git_capture():
    repo = ROOT if (ROOT / '.git').exists() else ROOT.parent
    prefix = ['git', '-c', 'safe.directory=' + repo.as_posix(), '-C', str(repo)]
    def run(*args):
        return subprocess.run(prefix + list(args), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    # Read-only Git commands; exclude every other project from status and patch.
    scope = '.' if repo == ROOT else PROJECT
    return {'head': run('rev-parse', 'HEAD').decode().strip(), 'repository_scope': str(repo),
            'status': run('status', '--short', '--untracked-files=all', '--', scope).decode('utf-8'),
            'patch': run('diff', '--binary', 'HEAD', '--', scope)}


def verify(archive, sidecar=None):
    archive = Path(archive)
    sidecar = Path(sidecar) if sidecar else archive.with_suffix('.sha256.json')
    expected = json.loads(sidecar.read_text(encoding='utf-8'))
    if archive.stat().st_size != expected['zip_bytes'] or sha(archive.read_bytes()) != expected['zip_sha256']:
        raise ValueError('ZIP size/SHA-256 mismatch; no extraction performed')
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        names = [e.filename for e in entries]
        if len(names) != len(set(n.casefold() for n in names)):
            raise ValueError('Duplicate archive entry')
        if sum(e.file_size for e in entries) > MAX_BYTES:
            raise ValueError('Archive exceeds declared transfer size limit')
        for entry in entries:
            checked_name(entry.filename)
            mode = entry.external_attr >> 16
            if entry.is_dir() or stat.S_ISLNK(mode) or entry.flag_bits & 1:
                raise ValueError('Unexpected directory/link/encrypted entry')
        lowered = set(n.casefold() for n in names)
        for name in names:
            for parent in PurePosixPath(name).parents:
                if str(parent).casefold() in lowered:
                    raise ValueError('Archive file/directory collision')
        raw = z.read(MANIFEST)
        if sha(raw) != expected['manifest_sha256']:
            raise ValueError('Manifest hash mismatch')
        manifest = json.loads(raw.decode('utf-8'))
        if set(names) != set(manifest['files']) | {MANIFEST}:
            raise ValueError('Archive file inventory mismatch')
        for name, info in manifest['files'].items():
            data = z.read(name)
            if len(data) != info['bytes'] or sha(data) != info['sha256']:
                raise ValueError('Payload hash mismatch: ' + name)
    return {'status': 'VERIFIED', 'files': len(manifest['files']), 'zip_sha256': expected['zip_sha256'],
            'zip_bytes': expected['zip_bytes'], 'native_home_runtime': 'NOT_TESTED'}


def pack(output):
    if ROOT.name != PROJECT or linked(ROOT):
        raise ValueError('Pack tool must run from the original project tools directory')
    output = Path(output).resolve()
    contained(output, ROOT)
    contained(output, ROOT / 'transfer')
    if output.exists() or output.with_suffix('.sha256.json').exists():
        raise ValueError('Refusing to overwrite an existing transfer snapshot')
    output.parent.mkdir(parents=True, exist_ok=True)
    capture = git_capture()
    receipt_dir = ROOT / 'docs/evidence/home_transfer'
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / 'project_changes.patch').write_bytes(capture.pop('patch'))
    (receipt_dir / 'source_git_state.json').write_text(json.dumps(capture, ensure_ascii=False, indent=2), encoding='utf-8')
    files, omitted = snapshot_files()
    payload = {PROJECT + '/' + p.relative_to(ROOT).as_posix(): p.read_bytes() for p in files}
    if sum(map(len, payload.values())) > MAX_BYTES:
        raise ValueError('Project snapshot exceeds transfer size limit')
    manifest = {'schema': '1.0', 'project': PROJECT, 'kind': 'development snapshot, not installer',
                'last_accepted_release': '0.9.2', 'native_tested_candidate': '0.10.1',
                'build_only_candidate': '0.10.2', 'git_head': capture['head'],
                'uncommitted_sources_included': True, 'git_history_included': False,
                'external_dependencies_included': False, 'excluded': omitted,
                'files': {n: {'bytes': len(b), 'sha256': sha(b)} for n, b in payload.items()}}
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in payload.items():
            z.writestr(name, data)
        z.writestr(MANIFEST, raw)
    sidecar = {'zip_name': output.name, 'zip_bytes': output.stat().st_size,
               'zip_sha256': sha(output.read_bytes()), 'manifest_sha256': sha(raw),
               'scope': 'Only EnvironmentalSimulationHub; files retained at source; no transmission performed'}
    output.with_suffix('.sha256.json').write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return verify(output)


def extract(archive, destination, sidecar=None):
    result = verify(archive, sidecar)
    dest = Path(destination).absolute()
    if dest.name != PROJECT:
        raise ValueError('Destination final directory must be ' + PROJECT)
    for ancestor in (dest,) + tuple(dest.parents):
        if ancestor.exists() and linked(ancestor):
            raise ValueError('Refusing destination reparse point')
    io_dest = native_path(dest)
    if io_dest.exists() and (not io_dest.is_dir() or any(io_dest.iterdir())):
        raise ValueError('Destination must be new or empty; never overwrite existing work')
    with zipfile.ZipFile(archive) as z:
        # Validate every final path before creating the destination.
        targets = [(e, dest.joinpath(*checked_name(e.filename)[1:])) for e in z.infolist()]
        for _, path in targets:
            contained(path, dest)
        io_dest.mkdir(parents=True, exist_ok=True)
        for entry, path in targets:
            io_path = native_path(path)
            io_path.parent.mkdir(parents=True, exist_ok=True)
            with io_path.open('xb') as f:
                f.write(z.read(entry.filename))
    return dict(result, destination=str(dest), extraction='COPIED', registration='NOT_CHANGED')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('pack'); p.add_argument('output')
    p = subs.add_parser('verify'); p.add_argument('archive'); p.add_argument('--sidecar')
    p = subs.add_parser('extract'); p.add_argument('archive'); p.add_argument('destination'); p.add_argument('--sidecar')
    args = parser.parse_args()
    try:
        if args.command == 'pack': response = pack(args.output)
        elif args.command == 'verify': response = verify(args.archive, args.sidecar)
        else: response = extract(args.archive, args.destination, args.sidecar)
        print(json.dumps(response, ensure_ascii=False, indent=2))
    except Exception as exc:
        parser.exit(1, 'Transfer stopped: ' + str(exc) + '\n')
