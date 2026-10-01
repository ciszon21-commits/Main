"""Record 0.8.5 only after native regression and explicit visual inspection."""
from pathlib import Path
import json, hashlib, sys
root=Path(__file__).resolve().parents[1]
def read(name):return json.loads((root/'docs/evidence'/name).read_text(encoding='utf-8'))
loaded=read('release_085_loaded.json');runtime=read('platform_085_runtime.json')
capture=read('ui_085/capture.json');palette=read('topic_085_palette.json')
logic=read('binary_085_logic.json')
assert loaded['version']==runtime['version']=='0.8.5' and palette['version']=='0.8.5.0'
assert runtime['passed']==21 and loaded['time_passed']==17 and loaded['location_passed']==11 and loaded['climate_passed']==11
assert loaded['overview_buttons_verified']==5 and loaded['shared_navigation_routes_verified']==6
assert len(capture['shots'])==22 and '--visual-reviewed' in sys.argv
hashes={}
for name in ['EnvironmentalHub.Core.dll','EnvironmentalHub.Adapters.dll']:
    prior=hashlib.sha256((root/'artifacts/releases/0.8.3'/name).read_bytes()).hexdigest()
    current=hashlib.sha256((root/'artifacts/releases/0.8.5'/name).read_bytes()).hexdigest()
    verified=next(b for b in logic['binaries'] if b['name']==name)
    assert verified['previous_sha256'].lower()==prior and verified['current_sha256'].lower()==current
    assert verified['metadata_equal_except_build_module_id_and_informational_git_revision'] and verified['method_bodies_equal']
    hashes[name]={'sha256':current,'previous_sha256':prior,'byte_identical_to_083':prior==current,'logic_comparison':verified}
report={'version':'0.8.5','build':{'warnings':0,'errors':0},'simulation_binaries':hashes,
        'radiation_regression_mean':loaded['radiation_regression_mean'],
        'native_platform_cases':21,'native_time_cases':17,'native_location_cases':11,'native_climate_cases':11,
        'navigation':{'overview_buttons':5,'shared_routes':6,'weather_result_preserved':loaded['navigation_preserves_weather_result']},
        'palette':palette,
        'visual_review':{'images':22,'widths':[320,480],'scope':capture['scope'],
                        'findings':'Opaque restrained topic colors and native line icons visible; full-width titles and readable fields/actions. Result colors remain native. Narrow panels scroll vertically.'},
        'catalog':{'installed_entries':122,'independently_integrated':8,'backend_only':1,'pending':113},
        'computer_use_used':False,
        'not_accepted':['Full Dock/theme-switch/keyboard/picker/dialog coverage','Reliable asynchronous progress/cancellation','Persistent scenario-library import','Additional simulation engines'],
        'interface_strategy':'V1 uses existing Rhino/Eto; V2 larger visual interaction after major functional acceptance.'}
(root/'docs/evidence/topic_085_acceptance.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
p=root/'docs/DEVELOPMENT_LOG.md';s=p.read_text(encoding='utf-8')
entry='''

## 2026-10-01 — 0.8.5 native topic hierarchy and visual refinement

- DESIGN: Added muted semantic accents for model, environment, settings, run, results and compare; centralized light/dark tokens, quiet rules and native vector module/section icons. Full-width titles follow the compact brand/version row. Literal labels disable mnemonic parsing so ampersands remain visible; 0.8.4 captures revealed this and its loaded binary is preserved. No solver palette or numerical output is recolored.
- SCOPE: V1 remains in the current Rhino/Eto framework. V2 larger visual interaction is explicitly deferred until the major function milestones are accepted. This release adds no Ladybug adapters; catalog remains eight independently integrated, one backend-only and 113 pending entries out of 122.
- VERIFIED: 0 errors / 0 warnings. Fresh owned Rhino loaded registered 0.8.5; unchanged radiation benchmark 1233.3471168086037 kWh/m2. Native platform 21, time 17, location 11 and climate 11 cases passed, plus five overview buttons and six module routes. Core/Adapter source is unchanged. Whole-file hashes differ from 0.8.3 because the SDK embeds the current informational Git revision and build identity; all managed method bodies and metadata match after excluding only MVID and that revision. The comparison covers IL, locals, stack and exception regions; it is not byte identity. Actual host topic/secondary text colors are opaque and exceed 4.5:1 contrast; token math also checked white and #20242A. Twenty-two native production-control offscreen images at 320/480 px inspected. See topic_085_acceptance.json and binary_085_logic.json.
- LIMITS: Token math is not native dark-theme QA. Full Dock/theme switching, keyboard/picker/dialog checks, asynchronous progress/cancel and further engine integration remain open. No Computer Use. Existing loaded Rhino processes need restart to use the new assembly; versioned packages and registration backups retain earlier releases.
'''
if '0.8.5 native topic hierarchy and visual refinement' not in s:p.write_text(s+entry,encoding='utf-8')
print('0.8.5 native UI acceptance recorded; solver method bodies and metadata verified.')
