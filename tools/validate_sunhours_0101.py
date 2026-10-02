"""Independent stock-component comparisons and real cached-panel checks; owned test slot only."""
import os,json,copy,math,clr,System,Rhino
clr.AddReference('Grasshopper')
clr.AddReference('Eto')
clr.AddReference('System.Text.Json')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
from Eto.Forms import Button,CheckBox
from System.Text.Json import JsonSerializer
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
doc=__rhino_doc__;units=doc.ModelUnitSystem;flags=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic
plugin=Rhino.PlugIns.PlugIn.Find(System.Guid('bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f'))
assert str(plugin.GetType().Assembly.GetName().Version)=='0.10.1.0'
ad=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts/releases/0.10.1/EnvironmentalHub.Adapters.dll'))
core=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts/releases/0.10.1/EnvironmentalHub.Core.dll'))
method=ad.GetType('EnvironmentalHub.Adapters.LadybugSunHoursAdapter').GetMethod('RunJson')
before=GH.Instances.DocumentServer.DocumentCount;fixtures=[];checks=[];numeric=[]
out=os.path.join(root,'samples/sunhours_0101');os.makedirs(out,exist_ok=True)
def run(r):return json.loads(method.Invoke(None,System.Array[System.Object]([doc,json.dumps(r),folder])))
def add(g):
 i=doc.Objects.AddMesh(g) if isinstance(g,Rhino.Geometry.Mesh) else doc.Objects.AddBrep(g);fixtures.append(i);return str(i)
def plate(x0=0,x1=4,z=0,size=4):
 scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
 p=Rhino.Geometry.Plane(Rhino.Geometry.Point3d(0,0,z*scale),Rhino.Geometry.Vector3d.ZAxis)
 return add(Rhino.Geometry.PlaneSurface(p,Rhino.Geometry.Interval(x0*scale,x1*scale),Rhino.Geometry.Interval(0,size*scale)).ToBrep())
def request(geo,context=None,step=1,hours=None):
 return {'GeometryIds':[geo],'ContextIds':context or [],'SunSource':{'Location':{'Name':'Taipei','Latitude':25.033,'Longitude':121.5654,'TimeZone':8},'HoursOfYear':hours or list(range(4110,4123))},'TimeStepsPerHour':step,'GridMetres':1,'OffsetMetres':.1,'GeometryBlocks':True,'CpuCount':1,'AcceptWarnings':True}
def stock(r):
 d=GH.Kernel.GH_Document();d.Enabled=False
 try:
  def make(n):
   c=GH.Kernel.GH_UserObject(os.path.join(folder,n+'.ghuser')).InstantiateObject();c.CreateAttributes();d.AddObject(c,False);return c
  def bind(c,n,values):
   p=Param_GenericObject();p.CreateAttributes()
   for v in values:p.PersistentData.Append(GH_ObjectWrapper(v),GH_Path(0))
   d.AddObject(p,False);next(i for i in c.Params.Input if i.Name==n).AddSource(p)
  loc=make('LB Construct Location');sun=make('LB SunPath');hours=make('LB Direct Sun Hours');s=r['SunSource'];l=s['Location']
  for n,v in [('_name_',l['Name']),('_latitude_',l['Latitude']),('_longitude_',l['Longitude']),('_time_zone_',l['TimeZone'])]:bind(loc,n,[v])
  next(i for i in sun.Params.Input if i.Name=='_location').AddSource(next(o for o in loc.Params.Output if o.Name=='location'))
  bind(sun,'hoys_',s['HoursOfYear']);bind(sun,'north_',[s.get('NorthDegrees',0)]);bind(sun,'solar_time_',[s.get('SolarTime',False)])
  next(i for i in hours.Params.Input if i.Name=='_vectors').AddSource(next(o for o in sun.Params.Output if o.Name=='vectors'))
  bind(hours,'_geometry',[doc.Objects.FindId(System.Guid(i)).Geometry for i in r['GeometryIds']])
  if r['ContextIds']:bind(hours,'context_',[doc.Objects.FindId(System.Guid(i)).Geometry for i in r['ContextIds']])
  scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
  for n,v in [('_timestep_',r['TimeStepsPerHour']),('_grid_size',r['GridMetres']*scale),('_offset_dist_',r['OffsetMetres']*scale),('geo_block_',r['GeometryBlocks']),('_cpu_count_',r['CpuCount']),('_run',True)]:bind(hours,n,[v])
  GH.Instances.DocumentServer.AddDocument(d);d.Enabled=True;d.NewSolution(False)
  for c in [loc,sun,hours]:assert not list(c.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error))
  def values(n):return [v.ScriptVariable() for v in next(o for o in hours.Params.Output if o.Name==n).VolatileData.AllData(True)]
  meshes=values('mesh');return {'values':[float(v) for v in values('results')],'points':[[p.X,p.Y,p.Z] for p in values('points')],'colors':[[c.ToArgb() for c in m.VertexColors] for m in meshes],'faces':[[[f.A,f.B,f.C] if f.IsTriangle else [f.A,f.B,f.C,f.D] for f in m.Faces] for m in meshes]}
 finally:GH.Instances.DocumentServer.RemoveDocument(d);d.Dispose()
def compare(name,r):
 a=run(r);b=stock(r);assert len(a['Values'])==len(b['values'])
 assert all(abs(x-y)<1e-9 for x,y in zip(a['Values'],b['values']))
 assert all(abs(x-y)<1e-8 for p,q in zip(a['Points'],b['points']) for x,y in zip(p,q))
 assert [m['VertexColorsArgb'] for m in a['ResultMesh']]==b['colors'];assert [m['Faces'] for m in a['ResultMesh']]==b['faces']
 assert a['Units']=='h';assert all(0<=v<=len(a['SunlightVectors'])/r['TimeStepsPerHour']+1e-8 for v in a['Values'])
 numeric.append({'name':name,'stats':a['Statistics'],'sun_vectors':len(a['SunlightVectors']),'timestep':r['TimeStepsPerHour']});checks.append('stock_numeric_points_faces_colors:'+name)
 json.dump(a,open(os.path.join(out,name+'.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2);return a
try:
 g=plate();r=request(g);a=compare('unshaded_hourly',r);assert all(v==13 for v in a['Values'])
 roof=plate(-100,100,5,200);b=compare('full_canopy',request(g,[roof]));assert b['Statistics']['Maximum']==0
 half=plate(0,2,1);c=compare('partial_canopy',request(g,[half]));assert len(set(c['Values']))>1
 compare('half_hour_night_filter',request(g,step=2,hours=[4110+i*.5 for i in range(28)]))
 compare('single_hour_weight',request(g,hours=[4116]));d=compare('single_quarter_hour_weight',request(g,step=4,hours=[4116]));assert d['Statistics']['Mean']==.25
 r=request(g);r['SunSource']['NorthDegrees']=90;compare('north_90',r)
 r=request(g);r['SunSource']['SolarTime']=True;compare('solar_time',r)
 r=request(g);r['SunSource']['Location']={'Name':'Sydney','Latitude':-33.8688,'Longitude':151.2093,'TimeZone':10};compare('southern_winter',r)
 scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem);m=Rhino.Geometry.Mesh()
 for x,y in [(0,0),(4,0),(4,4),(0,4)]:m.Vertices.Add(x*scale,y*scale,0)
 m.Faces.AddFace(0,3,2);m.Faces.AddFace(0,2,1);mg=add(m)
 r=request(mg);r['GeometryBlocks']=False;r['OffsetMetres']=0;d=compare('mesh_no_self_block',r);assert len(d['Values'])==2 and all(v==13 for v in d['Values'])
 r['GeometryBlocks']=True;r['OffsetMetres']=.1;d=compare('mesh_self_block',r);assert all(v==0 for v in d['Values'])
 for unit in [Rhino.UnitSystem.Millimeters,Rhino.UnitSystem.Meters]:
  doc.AdjustModelUnitSystem(unit,False);d=compare(str(unit),request(plate()));assert d['Statistics']['Count']==16 and d['Statistics']['Mean']==13
 doc.AdjustModelUnitSystem(units,False)
 invalids=[];base=request(g)
 for label,field,value in [('empty_geometry','GeometryIds',[]),('unknown_geometry','GeometryIds',[str(System.Guid.NewGuid())]),('overlap','ContextIds',[g]),('duplicate_geometry','GeometryIds',[g,g]),('grid_zero','GridMetres',0),('grid_too_small','GridMetres',.001),('negative_offset','OffsetMetres',-1),('zero_cpu','CpuCount',0),('schema','SchemaVersion','2.0'),('bad_rate','TimeStepsPerHour',7),('rate_mismatch','TimeStepsPerHour',2)]:
  r=copy.deepcopy(base);r[field]=value;invalids.append((label,r))
 for label,h in [('duplicate_hoy',[4116,4116]),('irregular_hoy',[4116,4116.5,4116.75]),('sparse_hoy',[4116,4118]),('out_of_year',[8760])]:
  r=copy.deepcopy(base);r['SunSource']['HoursOfYear']=h;invalids.append((label,r))
 for name,r in invalids:
  failed=False
  try:run(r)
  except Exception:failed=True
  assert failed,name;checks.append('invalid_rejected:'+name)
 Rhino.RhinoApp.RunScript('EnvironmentalSunHours',False);workspace=Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'));assembly=workspace.GetType().Assembly
 panel=workspace.GetModule(assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel'));sunpanel=workspace.GetModule(assembly.GetType('EnvironmentalHub.Plugin.SunPathPanel'))
 sunpanel.ExecuteJson(json.dumps(base['SunSource']));panel.SetGeometry(System.Array[System.Guid]([System.Guid(g)]),System.Array[System.Guid]([]));panel.UseCompletedSunPath()
 sentinel=doc.Objects.AddPoint(Rhino.Geometry.Point3d(0,0,-scale));fixtures.append(sentinel);attrs=doc.Objects.FindId(sentinel).Attributes.Duplicate();attrs.Name='EnvironmentalHub / user named object';doc.Objects.ModifyAttributes(sentinel,attrs,True)
 def field(name):return panel.GetType().GetField(name,flags).GetValue(panel)
 def objects():
  settings=Rhino.DocObjects.ObjectEnumeratorSettings();settings.HiddenObjects=True;settings.NormalObjects=True;settings.LockedObjects=True
  return list(doc.Objects.GetObjectList(settings))
 field('solo').Checked=True
 field('run').PerformClick();a=json.loads(panel.CompletedResultJson);assert a['Statistics']['Mean']==13 and not doc.Objects.FindId(sentinel).IsHidden
 sunowned=[o for o in objects() if o.Attributes.GetUserString('EnvironmentalHub.PreviewOwner')=='bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f/SunPath'];assert sunowned and all(o.IsHidden for o in sunowned);checks.append('completed_sunpath_transfer_real_run_and_tagged_only_isolation')
 preview=lambda:[o for o in objects() if o.Attributes.GetUserString('EnvironmentalHub.PreviewOwner')=='bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f/SunHours']
 mesh=preview()[0].Geometry;expected=.002*scale;assert all(abs(v.Z-expected)<1e-6 for v in mesh.Vertices);assert all(v[2]==0 for v in a['ResultMesh'][0]['Vertices']);checks.append('native_export_unshifted_preview_offset_2mm')
 saved=panel.CompletedResultJson;panel.SetDisplayOffset(.01);assert panel.CompletedResultJson==saved;assert all(abs(v.Z-.01*scale)<1e-6 for v in preview()[0].Geometry.Vertices);checks.append('display_offset_changes_preview_only')
 field('visible').Checked=False;assert all(o.IsHidden for o in preview());field('visible').Checked=True;assert all(not o.IsHidden for o in preview());checks.append('result_visibility_toggle')
 workspace.ShowModule(assembly.GetType('EnvironmentalHub.Plugin.SunPathPanel'));assert all(not doc.Objects.FindId(o.Id).IsHidden for o in sunowned);workspace.ShowModule(panel.GetType());checks.append('module_exit_restores_other_previews')
 panel.SetTargetRange(13,13);assert '100.0%' in panel.AssessmentText;checks.append('inclusive_project_criterion')
 panel.SaveScenario('Unshaded');panel.ExecuteJson(json.dumps(request(g,[half])));panel.SaveScenario('Shade');assert 'Δ' in panel.CompareScenarios(0,1);checks.append('scenario_comparison_with_matching_sun_source')
 r=request(g,hours=[4115,4116]);panel.ExecuteJson(json.dumps(r));panel.SaveScenario('Other period');assert '不顯示差值' in panel.CompareScenarios(0,2);checks.append('mismatched_period_suppresses_delta')
 previous=panel.CompletedResultJson;ids=[o.Id for o in preview()]
 for name,r in [('invalid',invalids[0][1]),('all_night',request(g,hours=[4104,4105]))]:
  failed=False
  try:panel.ExecuteJson(json.dumps(r))
  except Exception:failed=True
  assert failed and panel.CompletedResultJson==previous and [o.Id for o in preview()]==ids;checks.append('failed_'+name+'_retains_result_preview')
 GH.Kernel.GH_Document.EnableSolutions=False
 try:
  failed=False
  try:panel.ExecuteJson(json.dumps(base))
  except Exception:failed=True
  assert failed and panel.CompletedResultJson==previous and [o.Id for o in preview()]==ids;checks.append('disabled_gh_retains_result_preview')
 finally:GH.Kernel.GH_Document.EnableSolutions=True
 bad=json.loads(previous);bad['ResultMesh'].append({'Vertices':[],'Faces':[[0,1,2]],'VertexColorsArgb':[]})
 typed=JsonSerializer.Deserialize(json.dumps(bad),core.GetType('EnvironmentalHub.Core.SunHoursResult'),None)
 failed=False
 try:panel.GetType().GetMethod('ReplacePreview',flags).Invoke(panel,System.Array[System.Object]([doc,typed]))
 except Exception:failed=True
 assert failed and [o.Id for o in preview()]==ids;checks.append('partial_preview_failure_rolls_back')
 exported=json.loads(panel.ExportResultJson());assert exported['NativeResult']==json.loads(previous) and exported['Presentation']['DisplayOffsetMetres']==.01;checks.append('export_contains_native_result_and_presentation')
 panel.DeletePreview();assert not preview() and panel.CompletedResultJson==previous and panel.ScenarioCount==3 and doc.Objects.FindId(sentinel) is not None;checks.append('clear_owned_only_preserves_results_scenarios_user_geometry')
 panel.SetDisplayOffset(.002);panel.ExecuteJson(json.dumps(request(g,[half])));panel.LocateResult();panel.LocateGeometry();checks.append('viewport_result_and_analysis_region_focus')
 doc.AdjustModelUnitSystem(Rhino.UnitSystem.Millimeters,False)
 try:
  failed=False
  try:panel.ExecuteJson(json.dumps(base))
  except Exception:failed=True
  assert failed;checks.append('unit_change_rejected_before_execution')
 finally:doc.AdjustModelUnitSystem(units,False)
 assert GH.Instances.DocumentServer.DocumentCount==before;checks.append('gh_documents_released')
 report={'version':'0.10.1','passed':len(checks),'cases':checks,'stock_comparisons':numeric,'slot':'armadillo','document_serial':doc.RuntimeSerialNumber,'scope':'Original installed components, native points/values/faces/colors and real cached-panel operations. Full Dock/themes/dialogs and cross-machine trial not accepted.'}
 json.dump(report,open(os.path.join(root,'docs/evidence/sunhours_0101_runtime.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2);print(json.dumps({'passed':len(checks),'stock_comparisons':len(numeric)}))
finally:
 doc.AdjustModelUnitSystem(units,False)
 if 'panel' in globals():panel.DeletePreview()
 if 'sunpanel' in globals():sunpanel.DeletePreview()
 for i in fixtures:doc.Objects.Delete(i,True)
 doc.Views.Redraw()
