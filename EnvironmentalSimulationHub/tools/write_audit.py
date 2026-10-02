"""Produce Phase 0 documents from captured runtime and filesystem evidence."""
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

hub = Path(__file__).resolve().parents[1]
workspace = hub.parent
docs = hub / "docs"
evidence = docs / "evidence"
def load(name):
    return json.loads((evidence / name).read_text(encoding="utf-8"))
def payload(call):
    value = next(c["text"] for c in call["response"]["result"]["content"] if c["type"] == "text")
    return json.loads(value).get("payload")
audit = load("runtime_audit.json")
runtime = payload(audit["calls"][1])
components = {}
for call in audit["calls"][2:]:
    for item in payload(call):
        components[item["guid"]] = item
ports = [payload(c) for c in load("radiation_ports.json")["calls"]]
ports += [payload(load("sdk_audit.json")["calls"][1])]
command = ["rg", "--files", "-g", "*.gh", "-g", "*.ghx", "-g", "*.3dm",
           "-g", "*.cs", "-g", "*.py", "-g", "*.epw", "-g", "!**/obj/**",
           "-g", "!**/bin/**", "-g", "!**/tmp*", "-g", "!**/dependencies/**", "-g",
           "!**/cycles_dependencies/**", "-g", "!**/tmp*/**", "-g",
           "!**/validation_media/**", "-g", "!EnvironmentalSimulationHub/**"]
scan = subprocess.run(command, cwd=workspace, capture_output=True, text=True, encoding="utf-8")
assets = []
for filename in scan.stdout.splitlines():
    file = workspace / filename
    row = {"path": filename, "type": file.suffix.lower(), "disposition": "UNKNOWN"}
    if file.suffix.lower() == ".ghx":
        try:
            root = ET.parse(file).getroot()
            names = [n.text or "" for n in root.iter("item") if n.attrib.get("name") == "Name"]
            row["component_names"] = sorted(set(names))
            row["radiation_component_matches"] = [n for n in names if
                "Incident Radiation" in n or "Cumulative Sky Matrix" in n]
            row["inspection"] = "XML component names inspected; runtime unverified"
        except Exception as exc:
            row["inspection_error"] = str(exc)
    elif file.suffix.lower() == ".gh":
        row["inspection"] = "Binary definition indexed; no execution or claim of validity"
    if filename.endswith("SCRIPTS\\bridge.py"):
        row["disposition"] = "WRAP"
        row["inspection"] = "Existing transport read; bounded project probe replaces its unbounded wait"
    assets.append(row)
(evidence / "asset_inventory.json").write_text(json.dumps({
    "assets": assets, "scan_returncode": scan.returncode,
    "scan_stderr": scan.stderr, "excluded": ["obj", "bin", "dependencies", "temporary QA folders"],
}, ensure_ascii=False, indent=2), encoding="utf-8")
(evidence / "runtime_baseline.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding="utf-8")
(evidence / "component_inventory.json").write_text(json.dumps(list(components.values()), ensure_ascii=False, indent=2), encoding="utf-8")

versions = {}
site = Path("C:/Program Files/ladybug_tools/python/Lib/site-packages")
for package in ("ladybug_core", "honeybee_core", "dragonfly_core", "ladybug_radiance", "honeybee_radiance", "honeybee_energy"):
    for metadata in site.glob(package + "-*.dist-info/METADATA"):
        for line in metadata.read_text(encoding="utf-8").splitlines():
            if line.startswith("Version: "):
                versions[package] = line[9:]
                break
solver_commands = {
    "OpenStudio": ["C:/Program Files/ladybug_tools/openstudio/bin/openstudio.exe", "--version"],
    "EnergyPlus": ["C:/Program Files/ladybug_tools/openstudio/EnergyPlus/energyplus.exe", "--version"],
    "Radiance": ["C:/Program Files/ladybug_tools/radiance/bin/rtrace.exe", "-version"],
}
solvers = {}
for name, args in solver_commands.items():
    run = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=15)
    solvers[name] = {"path": args[0], "exit_code": run.returncode,
                     "version_output": (run.stdout + run.stderr).strip()}
(evidence / "solver_audit.json").write_text(json.dumps({"packages": versions, "solvers": solvers,
    "OpenFOAM": {"status": "UNVERIFIED", "reason": "Not found on PATH or checked conventional locations; Eddy provisioning not executed"}}, indent=2), encoding="utf-8")

lines = ["# Component inventory", "", "Audit date: 2026-10-01 (Asia/Taipei).",
    "MCP searches: Climate, Sun, Solar, Radiation, Ladybug, Honeybee, Dragonfly, Eddy; limit 40 per query.",
    "This is a deduplicated search inventory, not an exhaustive plugin catalog. GUIDs are returned by the live library.",
    "", "| Name | Category | GUID |", "| --- | --- | --- |"]
for item in sorted(components.values(), key=lambda v: v["name"]):
    lines.append(f"| {item['name']} | {item['category']} | `{item['guid']}` |")
lines += ["", "## Verified radiation ports", ""]
for item in ports:
    if not item or "inputs" not in item:
        continue
    lines += [f"### {item['name']}", "", "Inputs: " + ", ".join(f"`{p['name']}` ({p['access']})" for p in item["inputs"]),
              "", "Outputs: " + ", ".join(f"`{p['name']}`" for p in item["outputs"]), ""]
lines += ["Correct component name: `LB Cumulative Sky Matrix`; the attempted `LB Sky Matrix` lookup returned not found.",
          "", "Installed source and runtime report component version 1.10.0. This differs from package/loader assembly versions."]
(docs / "COMPONENT_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
counts = Counter(a["type"] for a in assets)
(docs / "ENVIRONMENT_AUDIT.md").write_text(f"""# Phase 0 environment audit

2026-10-01, Asia/Taipei. Evidence is in `evidence/`; physical result is in `../samples/radiation_smoke/`.

## Runtime baseline

- Rhino and Grasshopper: {runtime['rhino_version']}; Rhino process uses .NET {runtime['dotnet_runtime']}.
- Installed .NET SDKs: 8.0.424 and 10.0.400 (terminal `dotnet --info`).
- Explicit MCP target: aardvark, PID 37272, port 10501. Default armadillo was stale and pruned by the router.
- Initial Rhino document: unnamed, no path, Centimeters, tolerance 0.01, 0 objects, 6 visible layers.
- Initial GH canvas closed; no active document, components, connections, groups, or clusters.
- Router requires its external SQLite state database to be writable; sandbox-only initialization failed. Authorized execution responded.

## Plugin and solver audit

| Stack | Verified version | Availability evidence |
| --- | --- | --- |
| Ladybug | core {versions.get('ladybug_core')}; radiation components 1.10.0 | Live library and actual radiation run |
| Honeybee | core {versions.get('honeybee_core')} | Live HB component search; energy/daylight execution pending |
| Dragonfly | core {versions.get('dragonfly_core')} | Live DF component search; execution pending |
| Eddy3D | package 1.15.0-beta.827; loaded provisioning 1.15.0.827 | Live library search; wind execution pending |
| OpenStudio | {solvers['OpenStudio']['version_output']} | Version command exit 0; full energy run pending |
| EnergyPlus | {solvers['EnergyPlus']['version_output']} | Version command exit 0; full energy run pending |
| Radiance | {solvers['Radiance']['version_output']} | Version exit 0; gendaymtx used by Ladybug sky matrix |
| OpenFOAM | UNVERIFIED | No confirmed executable/version; do not infer from Eddy3D presence |

Actual LBT installation root is `C:/Program Files/ladybug_tools`, not `C:/ladybug_tools`.

## Assets and MVP decision

Indexed {len(assets)} existing source/model/workflow/weather files; by extension: {dict(counts)}.
GHX component names were inspected. Binary GH files are UNKNOWN until individually read and runtime tested.
No working local radiation definition was established by this audit. There was no active definition to wrap.
Use the installed original LB Import EPW, LB Cumulative Sky Matrix, and LB Incident Radiation user objects to form the smallest slice.
Existing unrelated CAD, cinema, structural, and Revit assets remain UNKNOWN or outside this MVP; no changes were made to them.
The asset JSON records exclusions and any search access errors; this is not a claim to have executed every existing binary workflow.

## Verified vertical slice

Rhino 4m × 4m horizontal Brep snapshot → GH parameter → original Ladybug → Radiance sky matrix → 16 results → colored mesh and legend in Rhino.
Seattle-Tacoma bundled TMYx 2004–2018 EPW, annual period, north 0°, 1m grid (100cm), 1 CPU, Tregenza sky.
Mean/min/max: 1233.3471168086037 kWh/m². Repeat run per-value maximum difference: 0.
Mesh has 16 faces and 64 vertex colors. Viewport screenshot visually inspected.
This is a smoke fixture, not Taipei weather, a production adapter, or full scientific validation.

First solve produced no outputs because the new GH document was disabled. Enabled the same document and re-ran; no solver replacement.
Initial failure and successful transport receipts are retained.

## Git baseline

Parent repository exists on branch master but initially has no commits; all prior project folders are untracked.
No global safe.directory setting was changed; commands use a one-command safe.directory override.
Human author identity was not configured. Only this new Hub folder belongs to the milestone scope.
""", encoding="utf-8")
print(json.dumps({"assets": len(assets), "components": len(components), "solver_versions": solvers}, ensure_ascii=False))
