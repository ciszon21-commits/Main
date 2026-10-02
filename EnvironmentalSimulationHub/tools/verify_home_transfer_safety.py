"""Verify the transfer archive and exercise boundaries inside project-owned scratch."""
import hashlib
import json
from pathlib import Path
import stat
import sys
import uuid
import zipfile
import safe_transfer as transfer

root = Path(__file__).resolve().parents[1]
archive = Path(sys.argv[1]).resolve()
qa = root / 'transfer/verification' / uuid.uuid4().hex
qa.mkdir(parents=True)
checks = []
report = transfer.verify(archive)
checks.append('zip_sha_inventory_and_every_payload_sha')

with zipfile.ZipFile(archive) as z:
    manifest = json.loads(z.read(transfer.MANIFEST))
    for name, info in manifest['files'].items():
        source = root.joinpath(*transfer.checked_name(name)[1:])
        assert source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() == info['sha256'], name
    assert all(name.startswith('EnvironmentalSimulationHub/') for name in z.namelist())
    assert not any(any(p in transfer.SKIP_PARTS for p in Path(n).parts) for n in z.namelist())
    assert any('/SunHoursContracts.cs' in n for n in z.namelist())
    assert any('/SunHoursPanel.cs' in n for n in z.namelist())
    assert not manifest['git_history_included']
checks.append('source_snapshot_exact_and_uncommitted_files_included')
checks.append('project_only_no_parent_git_caches_or_external_installations')

destination = qa / 'roundtrip/EnvironmentalSimulationHub'
transfer.extract(archive, destination)
for name, info in manifest['files'].items():
    path = transfer.native_path(destination.joinpath(*transfer.checked_name(name)[1:]))
    assert path.stat().st_size == info['bytes']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == info['sha256'], name
checks.append('fresh_directory_extract_and_independent_payload_readback')

def reject(label, action, dest=None):
    failed = False
    try:
        action()
    except (ValueError, FileExistsError):
        failed = True
    assert failed, label
    if dest is not None:
        assert not dest.exists(), label
    checks.append(label)

existing = qa / 'existing/EnvironmentalSimulationHub'
existing.mkdir(parents=True)
sentinel = existing / 'keep.txt'
sentinel.write_text('existing home work must survive', encoding='utf-8')
reject('existing_destination_rejected_without_overwrite', lambda: transfer.extract(archive, existing))
assert sentinel.read_text(encoding='utf-8') == 'existing home work must survive'
assert [p.name for p in existing.iterdir()] == ['keep.txt']

tampered = qa / 'tampered.zip'
tampered.write_bytes(archive.read_bytes() + b'changed')
dest = qa / 'tampered/EnvironmentalSimulationHub'
reject('corrupt_zip_rejected_before_destination_creation',
       lambda: transfer.extract(tampered, dest, archive.with_suffix('.sha256.json')), dest)

def dangerous(label, names, link=False):
    path = qa / (label + '.zip')
    payload = {n: b'test' for n in names}
    raw = json.dumps({'files': {n: {'bytes': 4, 'sha256': transfer.sha(b'test')} for n in names}}).encode()
    with zipfile.ZipFile(path, 'w') as z:
        for name in names:
            if link:
                entry = zipfile.ZipInfo(name)
                entry.create_system = 3
                entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(entry, payload[name])
            else:
                z.writestr(name, payload[name])
        z.writestr(transfer.MANIFEST, raw)
    path.with_suffix('.sha256.json').write_text(json.dumps({'zip_bytes': path.stat().st_size,
        'zip_sha256': transfer.sha(path.read_bytes()), 'manifest_sha256': transfer.sha(raw)}))
    dest = qa / label / 'EnvironmentalSimulationHub'
    reject(label, lambda: transfer.extract(path, dest), dest)

dangerous('traversal_rejected_before_write', ['EnvironmentalSimulationHub/../../outside.txt'])
dangerous('absolute_path_rejected_before_write', ['C:/outside.txt'])
dangerous('case_duplicate_rejected_before_write', ['EnvironmentalSimulationHub/A.txt', 'EnvironmentalSimulationHub/a.txt'])
dangerous('ads_path_rejected_before_write', ['EnvironmentalSimulationHub/data.txt:stream'])
dangerous('file_directory_collision_rejected_before_write', ['EnvironmentalSimulationHub/file', 'EnvironmentalSimulationHub/file/child'])
dangerous('archive_symlink_rejected_before_write', ['EnvironmentalSimulationHub/link'], link=True)

# Exercise a genuinely >260-character Windows path without changing OS policy.
long_archive = qa / 'long_path.zip'
long_name = 'EnvironmentalSimulationHub/' + '/'.join(['a' * 90, 'b' * 90, 'c' * 90, 'result.txt'])
long_data = b'long path transfer proof'
long_raw = json.dumps({'files': {long_name: {'bytes': len(long_data), 'sha256': transfer.sha(long_data)}}}).encode()
with zipfile.ZipFile(long_archive, 'w') as z:
    z.writestr(long_name, long_data)
    z.writestr(transfer.MANIFEST, long_raw)
long_archive.with_suffix('.sha256.json').write_text(json.dumps({'zip_bytes': long_archive.stat().st_size,
    'zip_sha256': transfer.sha(long_archive.read_bytes()), 'manifest_sha256': transfer.sha(long_raw)}))
long_dest = qa / 'long_path/EnvironmentalSimulationHub'
transfer.extract(long_archive, long_dest)
long_file = transfer.native_path(long_dest.joinpath(*transfer.checked_name(long_name)[1:]))
assert long_file.read_bytes() == long_data
checks.append('windows_extended_length_path_extract_readback_without_os_changes')

result = {'status': 'PASS', 'checks': checks, 'passed': len(checks), 'payload_files': report['files'],
          'zip_bytes': report['zip_bytes'], 'zip_sha256': report['zip_sha256'],
          'source_scope': str(root), 'scratch_scope': str(qa),
          'registration_or_process_changes': False, 'transmission': 'NOT_PERFORMED',
          'home_native_runtime': 'NOT_TESTED'}
receipt = archive.with_suffix('.verification.json')
receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'passed': len(checks), 'files': report['files'],
                  'zip_megabytes': round(report['zip_bytes'] / 1048576, 2), 'receipt': str(receipt)}, ensure_ascii=False))
