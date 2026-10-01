"""Real registered Rhino panel tests; dedicated release-test document only."""
import json,os,System,Rhino
from System.Reflection import BindingFlags
import Grasshopper as GH
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
Rhino.RhinoApp.RunScript('EnvironmentalRadiation',False)
rad=Rhino.UI.Panels.GetPanel(System.Guid('c62382ce-7709-4fcd-9dfb-447d1d8a08c0'))
doc=__rhino_doc__;assert len(list(doc.Objects))==0,'Use a dedicated empty test document'
before=GH.Instances.DocumentServer.DocumentCount
scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
surface=Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,4*scale),Rhino.Geometry.Interval(0,4*scale))
fixture=doc.Objects.AddBrep(surface.ToBrep());surface.Dispose()
weather=json.load(open(os.path.join(root,'samples','radiation_smoke','runtime_result.json'),encoding='utf-8'))['weather']
flags=BindingFlags.Instance|BindingFlags.NonPublic
def control(name):return rad.GetType().GetField(name,flags).GetValue(rad)
def execute(name,**changes):
 request={'GeometryIds':[str(fixture)],'WeatherFile':weather,'GridMetres':1,'AcceptWarnings':True,'OutputDirectory':os.path.join(root,'samples','platform_ui',name)}
 request.update(changes)
 return json.loads(rad.ExecuteJson(json.dumps(request)))
cases=[]
try:
 a=execute('baseline');assert a['Statistics']['Mean']==1233.3471168086037
 rad.SaveScenario('Baseline · 1 m grid');cases.append('save_completed_snapshot')
 try:rad.SaveScenario('Baseline · 1 m grid')
 except Exception:pass
 else:raise RuntimeError('Duplicate scenario name accepted')
 assert rad.ScenarioCount==1;cases.append('unique_scenario_names')
 b=execute('candidate',GridMetres=0.5)
 rad.SaveScenario('Candidate · 0.5 m grid')
 text=rad.CompareScenarios(0,1);assert 'Δ average' in text and 'grid spacing' in text and 'not area-weighted' in text
 assert b['Statistics']['Count']==64;cases.append('matching_weather_comparison_with_changed_grid')
 rad.SetTargetRange(0,1500)
 assert 'PASS 64' in rad.AssessmentText and 'FAIL 0' in rad.AssessmentText;cases.append('target_range_counts')
 presenter=rad.GetType().Assembly.GetType('EnvironmentalHub.Plugin.ResultPresentation')
 native_result=control('lastResult')
 assess=presenter.GetMethod('Assessment',BindingFlags.Static|BindingFlags.NonPublic).Invoke(None,System.Array[System.Object]([native_result,System.Double(b['Statistics']['Minimum']),System.Double(b['Statistics']['Maximum'])]))
 assert 'PASS 64' in assess;cases.append('inclusive_exact_result_boundary')
 try:rad.SetTargetRange(0,1233.347)
 except Exception:pass
 else:raise RuntimeError('Unsupported criterion precision accepted')
 cases.append('explicit_criterion_precision')
 prior=rad.AssessmentText
 try:rad.SetTargetRange(100,0)
 except Exception:pass
 else:raise RuntimeError('Invalid target accepted')
 assert rad.AssessmentText==prior;cases.append('invalid_target_preserves_criterion')
 c=execute('selected_hours',HoursOfYear=[4000,4001],Settings={'CpuCount':1,'GroundReflectance':0.3,'OffsetMetres':0.15,'HighDensity':False})
 assert list(control('hours'))==[4000,4001] and control('reflectance').Value==0.3 and control('offset').Value==0.15
 # Inspect the real request used by buttons without solving twice.
 request=rad.GetType().GetMethod('Request',flags).Invoke(rad,System.Array[System.Object]([False]))
 assert list(request.HoursOfYear)==[4000,4001] and request.Settings.GroundReflectance==0.3 and request.Settings.OffsetMetres==0.15
 cases.append('button_request_retains_hours_and_advanced_settings')
 rad.SaveScenario('Two-hour study')
 assert 'Not comparable' in rad.CompareScenarios(0,2) and 'Δ average' not in rad.ComparisonText
 cases.append('different_time_period_suppresses_delta')
 exported=json.loads(rad.ExportComparisonJson());assert len(exported['Scenarios'])==3 and exported['Scenarios'][0]['Result']==a
 assert exported['Scenarios'][2]['Result']['InputParameters']['HoursOfYear']==[4000,4001]
 assert exported['ProjectCriterion']['Minimum']==0 and exported['ProjectCriterion']['Maximum']==1500
 cases.append('comparison_export_preserves_full_provenance')
 old=rad.ResultText;owned=rad.RenderedObjectCount
 try:execute('invalid',GridMetres=-1)
 except Exception:pass
 else:raise RuntimeError('Invalid request accepted')
 assert rad.ResultText==old and rad.RenderedObjectCount==owned;cases.append('failed_validation_preserves_result_and_preview')
 rad.LocateResult();cases.append('viewport_zoom_to_owned_preview')
 rad.ResetResult();assert rad.RenderedObjectCount==0 and rad.ScenarioCount==3 and doc.Objects.FindId(fixture) is not None
 cases.append('reset_preserves_scenarios_and_model')
 wp=Rhino.UI.Panels.GetPanel(System.Guid('1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a'))
 selection=json.loads(wp.CompletedSelectionJson)
 rad.UseImportedWeather();assert control('weather').Text==selection['WeatherFile'] and list(control('hours'))==selection['HoursOfYear']
 cases.append('completed_weather_selection_transfer')
 tp=Rhino.UI.Panels.GetPanel(System.Guid('06843693-df8a-421c-938b-96e2b9e88066'))
 period=json.loads(tp.ExecutePeriodJson(json.dumps({'StartMonth':6,'StartDay':21,'EndMonth':6,'EndDay':21})))
 rad.UseCompletedPeriod();assert list(control('hours'))==period['HoursOfYear'];previous_hours=list(control('hours'))
 cases.append('native_hourly_period_transfer')
 tp.ExecutePeriodJson(json.dumps({'StartMonth':6,'StartDay':21,'EndMonth':6,'EndDay':21,'TimeStep':2}))
 try:rad.UseCompletedPeriod()
 except Exception as e:assert 'subhour' in str(e)
 else:raise RuntimeError('Fractional period silently rounded')
 assert list(control('hours'))==previous_hours;cases.append('fractional_period_rejected_without_input_mutation')
 tp.ExecuteCalendarJson(json.dumps({'Month':6,'Day':21,'Hour':13,'Minute':30}))
 try:rad.UseCompletedPeriod()
 except Exception:pass
 else:raise RuntimeError('Calendar conversion accepted as a period')
 assert list(control('hours'))==previous_hours;cases.append('calendar_result_is_not_period')
 box=Rhino.Geometry.Box(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,4*scale),Rhino.Geometry.Interval(0,4*scale),Rhino.Geometry.Interval(0,4*scale)).ToBrep()
 assert doc.Objects.Replace(fixture,box);box.Dispose()
 final=execute('final_visual_fixture')
 rad.SetTargetRange(1000,1300);rad.CompareScenarios(0,1)
 assert GH.Instances.DocumentServer.DocumentCount==before
 cases.append('original_gh_document_cleanup')
 # Verify each sampled face color corresponds to a real native mesh value.
 pairs=[];index=0
 for mesh in final['ResultMesh']:
  for face in mesh['Faces']:
   colors=[mesh['VertexColorsArgb'][v] for v in face];assert len(set(colors))==1
   pairs.append([final['Values'][index],colors[0]]);index+=1
 assert index==len(final['Values']);cases.append('native_face_color_mapping')
 assert len(set(c for v,c in pairs))>1;cases.append('multi_color_3d_result_legend')
 for stage_index in range(6):rad.ShowStage(stage_index)
 cases.append('six_stage_navigation')
 rad.ShowStage(4)
 report={'version':rad.ProductVersion,'cases':cases,'passed':len(cases),'fixture_id':str(fixture),'document_serial':doc.RuntimeSerialNumber,'baseline_mean':a['Statistics']['Mean'],'candidate_cells':b['Statistics']['Count'],'legend_samples':pairs,'comparison':rad.ComparisonText,'assessment':rad.AssessmentText,'native_panel':True,'core_changed':False,'cancel_available':False}
 json.dump(report,open(os.path.join(root,'docs','evidence','platform_ui_runtime.json'),'w',encoding='utf-8'),indent=2)
 print(json.dumps(report))
except Exception:
 rad.ResetResult();doc.Objects.Delete(fixture,True);raise
