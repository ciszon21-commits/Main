from pathlib import Path
import json,hashlib,zipfile
root=Path(__file__).resolve().parents[1]
release=root/'artifacts/releases/0.8.6'
manifest={'version':'0.8.6','language':'zh-TW','plugin':'EnvironmentalHub.Plugin.rhp','plugin_id':'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f','runtime':'Rhino 8 / .NET 8','files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in release.iterdir() if f.suffix in ('.dll','.rhp','.json') and f.name!='release_manifest.json'},'dependencies':'Original installed Ladybug / Radiance; Core and Adapter source unchanged.'}
for p in [release/'release_manifest.json',root/'docs/evidence/release_086_manifest.json']:p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(root/'artifacts/EnvironmentalHub-0.8.6.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for f in release.iterdir():
        if f.suffix!='.pdb':archive.write(f,f.name)
(root/'tools/release_086_slot_calls.json').write_text(json.dumps([{'name':'spawn_slot','arguments':{}}]),encoding='utf-8')
old=json.loads((root/'tools/release_085_calls.json').read_text(encoding='utf-8'))[0]['arguments']['script']
# Generate replay inputs from the existing numerical acceptance scopes, with versioned outputs.
slot_transport=root/'docs/evidence/release_086_slot_transport.json'
if slot_transport.exists():
    transport=json.loads(slot_transport.read_text(encoding='utf-8'))
    payload=json.loads(transport['calls'][0]['response']['result']['content'][0]['text'])['payload']
    slot=payload['slotId']
    (root/'samples/weather_086').mkdir(exist_ok=True)
    replacements={
        "'Mean' in panel.SummaryText":"'平均值' in panel.SummaryText",
        "'12 monthly values'":"'12 逐月資料'",
        "'Previous result retained'":"'已保留前次結果'",
        "startswith('Calculated')":"startswith('計算完成')",
        "'Latitude' in climate_panel.SummaryText":"'緯度' in climate_panel.SummaryText",
        "'Start' in climate_panel.SummaryText":"'起始' in climate_panel.SummaryText",
        "'Local standard time' in climate_panel.SummaryText":"'當地標準時間' in climate_panel.SummaryText",
        "'Dry bulb max' in climate_panel.SummaryText":"'最高乾球溫度' in climate_panel.SummaryText",
        "'8760 values' in climate_panel.SummaryText":"'8760 筆數值' in climate_panel.SummaryText",
        "'subhour' in str(e)":"'次小時' in str(e)",
        "'Δ average'":"'Δ 平均值'", "'grid spacing'":"'網格間距'", "'not area-weighted'":"'未依面積加權'",
        "'PASS 64'":"'符合 64'", "'FAIL 0'":"'未符合 0'", "'Not comparable'":"'無法直接比較'",
        "'Advanced settings'":"'進階設定'",
        "'samples','weather'":"'samples','weather_086'",
        "'samples','platform_ui'":"'samples','platform_ui_086'",
        "'platform_085_runtime.json'":"'platform_086_runtime.json'",
        "'ui_085'":"'ui_086'"
    }
    def localized(script):
        script=script.replace('0.8.5','0.8.6').replace('release_085','release_086').replace("'dugong'",repr(slot))
        for a,b in replacements.items():script=script.replace(a,b)
        return script
    release_script=localized(old)
    release_script=release_script.replace('doc=__rhino_doc__;scale=',"doc=__rhino_doc__;assert len(list(doc.Objects))==0,'Dedicated empty release document required'\nscale=")
    extra="""
# Verify visible Chinese field names and immutable original contracts.
assert list(result['InputParameters'].keys())==['SchemaVersion','Format','FilePath']
assert str(panel.GetType().GetField('fields',flags).GetValue(panel).Items[0].Text).startswith('乾球溫度')
text_type=plugin.GetType().Assembly.GetType('EnvironmentalHub.Plugin.HubText')
error_method=text_type.GetMethod('Error',BindingFlags.Static|BindingFlags.NonPublic)
detail=error_method.Invoke(None,System.Array[System.Object]([System.Exception('CLIMATE-FILE-001: Wrong file.')]))
assert 'CLIMATE-FILE-001' in detail and '副檔名' in detail
unknown=error_method.Invoke(None,System.Array[System.Object]([System.Exception('Native message 42')]))
assert '原始診斷' in unknown and 'Native message 42' in unknown
report['language']='zh-TW'
report['chinese_weather_selector']=True
report['chinese_diagnostics_preserve_codes']=True
report['unknown_native_diagnostics_preserved']=True
"""
    # The final result variable is STAT data, so only test keys that belong to that contract.
    release_script=release_script.replace("json.dump(report,open(",extra+"\njson.dump(report,open(")
    for name,script in [
        ('release_086_calls.json',release_script),
        ('platform_086_calls.json',localized((root/'tools/validate_platform_ui.py').read_text(encoding='utf-8'))),
        ('ui_086_calls.json',localized((root/'tools/capture_hub_native_panels.py').read_text(encoding='utf-8'))),
        ('chinese_086_calls.json',(root/'tools/validate_chinese_ui.py').read_text(encoding='utf-8'))]:
        (root/'tools'/name).write_text(json.dumps([{'name':'run_python','arguments':{'slot':slot,'script':script}}],ensure_ascii=False,indent=2),encoding='utf-8')
    print('Prepared bounded 0.8.6 acceptance for '+slot)
