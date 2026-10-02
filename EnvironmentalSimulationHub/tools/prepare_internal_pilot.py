"""Package verified 0.8.7 binaries and colleague guides; no installation or downloads."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
release = root / 'artifacts/releases/0.8.7'
stage = root / 'artifacts/internal_pilot/0.8.7'
source_manifest = json.loads((release / 'release_manifest.json').read_text(encoding='utf-8'))
assert source_manifest['version'] == '0.8.7'
for name, digest in source_manifest['files'].items():
    assert hashlib.sha256((release / name).read_bytes()).hexdigest() == digest, name
for folder in ['plugin', 'guide', 'tools', 'examples']:
    (stage / folder).mkdir(parents=True, exist_ok=True)
files = []
for name in source_manifest['files']:
    target = stage / 'plugin' / name
    shutil.copy2(release / name, target)
    files.append(target)
config_path = stage / 'plugin/hub.config.json'
config = json.loads(config_path.read_text(encoding='utf-8'))
config['OutputDirectory'] = '%LOCALAPPDATA%/EnvironmentalSimulationHub/runs'
config_path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
for name in ['QUICK_START.md', 'PILOT_ACCEPTANCE.md', 'L2_VISUAL_PLAN.md', 'REFERENCE_INDEX.md']:
    target = stage / 'guide' / name
    shutil.copy2(root / 'docs' / name, target)
    files.append(target)
for source, destination in [('tools/Test-HubReadiness.ps1', 'tools/Test-HubReadiness.ps1'),
                            ('samples/quick_start/SolarPlate_4x4m.3dm', 'examples/SolarPlate_4x4m.3dm')]:
    target = stage / destination
    shutil.copy2(root / source, target)
    files.append(target)
start = stage / 'START_HERE.txt'
start.write_text((root / 'docs/QUICK_START.md').read_text(encoding='utf-8'), encoding='utf-8-sig')
files.append(start)
catalog = json.loads((root / 'docs/evidence/ladybug_feature_catalog.json').read_text(encoding='utf-8'))
ids = {'LB-001', 'LB-007', 'LB-009', 'LB-011', 'LB-013', 'LB-020', 'LB-033', 'LB-049', 'LB-063'}
dependencies = {'scope': 'Tested installed user-object baselines; external dependencies not distributed. Native runtime/Python/solver acceptance required.',
                'user_objects': [{k: item[k] for k in ['id', 'name', 'file', 'sha256']}
                                 for item in catalog['components'] if item['id'] in ids]}
assert len(dependencies['user_objects']) == 9
dependency_path = stage / 'dependencies.json'
dependency_path.write_text(json.dumps(dependencies, indent=2) + '\n', encoding='utf-8')
files.append(dependency_path)
manifest = {'version': '0.8.7', 'distribution': 'InternalPilot',
            'native_trial': 'Colleague-machine installation and first use pending',
            'base_release_manifest_sha256': hashlib.sha256((release / 'release_manifest.json').read_bytes()).hexdigest(),
            'configuration_override': {'OutputDirectory': config['OutputDirectory']},
            'runtime_baseline': {'rhino_assembly': '8.35.26251.13001', 'dotnet': '8', 'os': 'Windows'},
            'files': {f.relative_to(stage).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
manifest_path = stage / 'pilot_manifest.json'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
archive_path = root / 'artifacts/EnvironmentalHub-0.8.7-InternalPilot.zip'
with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
    for f in files + [manifest_path]:
        archive.write(f, f.relative_to(stage).as_posix())
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == digest
for name in ['EnvironmentalHub.Plugin.rhp', 'EnvironmentalHub.Core.dll', 'EnvironmentalHub.Adapters.dll']:
    assert (stage / 'plugin' / name).read_bytes() == (release / name).read_bytes()
receipt = {'version': '0.8.7', 'distribution': 'InternalPilot', 'archive': archive_path.relative_to(root).as_posix(),
           'archive_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(), 'files': len(files) + 1,
           'original_binaries_identical': True, 'source_release_unchanged': True,
           'configuration_override': manifest['configuration_override'],
           'scope': 'Archive CRC/file hashes and copied binaries verified; cross-machine/native colleague trial pending.'}
(root / 'docs/evidence/pilot_087_package.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt))
