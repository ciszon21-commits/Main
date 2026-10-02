"""Record final acceptance after native execution and explicit image inspection."""
from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[1]
loaded=json.loads((root/'docs/evidence/release_083_loaded.json').read_text(encoding='utf-8'))
runtime=json.loads((root/'docs/evidence/platform_ui_runtime.json').read_text(encoding='utf-8'))
capture=json.loads((root/'docs/evidence/ui_083/capture.json').read_text(encoding='utf-8'))
assert loaded['version']==runtime['version']=='0.8.3' and runtime['passed']==21
assert loaded['time_passed']==17 and loaded['location_passed']==11 and loaded['climate_passed']==11
assert loaded['overview_buttons_verified']==5 and loaded['shared_navigation_routes_verified']==6
assert len(capture['shots'])==22 and '--visual-reviewed' in sys.argv
hashes={}
for name in ['EnvironmentalHub.Core.dll','EnvironmentalHub.Adapters.dll']:
 prior=hashlib.sha256((root/'artifacts/releases/0.7.2'/name).read_bytes()).hexdigest()
 current=hashlib.sha256((root/'artifacts/releases/0.8.3'/name).read_bytes()).hexdigest()
 assert prior==current
 hashes[name]={'sha256':current,'byte_identical_to':'0.7.2'}
report={'version':'0.8.3','build':{'warnings':0,'errors':0},'core_preflight_checks':25,
 'core_preflight_scope':'Executed during 0.8.1 UI work against the unchanged Core source; final Core binary hash identical.',
 'native_platform_cases':21,'native_time_cases':17,'native_location_cases':11,'native_climate_cases':11,
 'radiation_regression_mean':loaded['radiation_regression_mean'],'simulation_binaries':hashes,
 'navigation':{'overview_buttons':5,'shared_routes':6,'weather_result_preserved':loaded['navigation_preserves_weather_result']},
 'visual_review':{'reviewer':'Codex image inspection','images':22,'widths':[320,480],'scope':capture['scope'],'findings':'Ruled hierarchy, visible numeric fields/actions, readable labels and result color samples; vertical scrolling at narrow width. Long paths remain selectable horizontally in text inputs.'},
 'not_accepted':['Full Dock/theme-switch/keyboard/picker/dialog coverage','Reliable asynchronous percentage progress/cancellation','Persistent scenario-library import','Additional simulation engines'],
 'computer_use_used':False,'catalog':{'installed_entries':122,'independently_integrated':8,'backend_only':1,'pending':113}}
(root/'docs/evidence/platform_083_acceptance.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
p=root/'docs/DEVELOPMENT_LOG.md';s=p.read_text(encoding='utf-8')
entry='''

## 2026-10-01 — Original time tools and 0.8.3 building-performance UI

- DONE: Added typed original LB Analysis Period, Calculate HOY and HOY to DateTime adapters and native Time Panel. Seventeen native/reference/error checks pass, including cross-year, overnight, subhour and end-day normalization. Catalog now tracks eight independently integrated entries, one verified radiation backend and 113 pending entries out of 122.
- UI AUDIT / DESIGN: Audited native Eto/WPF panels and GH workflow; recorded findings in UI_AUDIT_2026-10-01.md. Shared header/navigation and ruled sections replace repeated card frames. The overview distinguishes an executable solar workflow, supporting environment tools and planned engine integrations. Human-readable climate labels retain original names/types in exported contracts.
- SOLAR FLOW: Six stages with fixed stage navigation; explicit completed EPW/hourly-period transfer; existing advanced CPU/sky/reflectance/offset defaults; typed preflight; KPI/range/exact mesh-color samples; optional inclusive project criterion; owned-preview viewport focus; uniquely named session scenarios and full-provenance comparison JSON. Changed inputs and failed runs preserve useful completed results.
- ROOT CAUSES / FIXES: Narrow shared table columns previously hid numeric inputs; wide hints now sit outside field grids. Native criterion controls round to one decimal, so the public boundary rejects unsupported precision instead of silently changing a threshold. Per-run unordered colors are not interpreted as a continuous palette. Geometry fingerprint differences are disclosed as records requiring model review, not proof of physical geometry changes.
- VERIFIED: Final build has 0 errors / 0 warnings. Twenty-five Core preflight checks, 21 native UI/result cases, five overview buttons and six shared routes passed. Fresh coati Rhino loaded the registered 0.8.3 assembly. Radiation baseline remains 1233.3471168086037 kWh/m2. The 96-cell three-dimensional fixture confirms native multi-color face mapping. Core and Adapter DLLs are byte-identical to pre-platform 0.7.2. Twenty-two production Eto/WPF offscreen renders at 320/480 px were visually inspected in the current theme. See platform_083_acceptance.json and release_083_loaded.json.
- LIMITS / NEXT: Current GH solve is synchronous; reliable percentage progress/cancel requires a separately verified runner. Full Dock/theme/keyboard/dialog acceptance, persistent scenario-library import and additional engines remain open. Continue the remaining L1 Ladybug location/data utilities, then broader solar/comfort/chart coverage. No Computer Use or CFD execution was used. Versioned package and registry backups preserve earlier releases; existing loaded Rhino processes need restart to use the new binary.
'''
if 'Original time tools and 0.8.3 building-performance UI' not in s:p.write_text(s+entry,encoding='utf-8')
print('Final platform acceptance recorded; simulation binary identity verified.')
