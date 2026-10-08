assert not os.path.exists(fixture_path)
os.makedirs(outputs,exist_ok=True)
assert str(doc.ModelUnitSystem)=='Millimeters'
workspace.ShowModule(module_type)
surface = Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,8000),Rhino.Geometry.Interval(0,8000))
brep = surface.ToBrep()
geometry = doc.Objects.AddBrep(brep)
brep.Dispose()
surface.Dispose()
assert geometry != System.Guid.Empty
request = json.load(open(os.path.join(root,'samples/home_0105/visual_sunhours_0102/result_with_presentation.json'),encoding='utf-8'))['NativeResult']['InputParameters']
request['GeometryIds']=[str(geometry)]
request['ContextIds']=[]
panel.SetGeometry(System.Array[System.Guid]([geometry]),System.Array[System.Guid]([]))
completed = json.loads(panel.ExecuteJson(json.dumps(request)))
assert completed['Statistics']['Count']==256 and completed['Statistics']['Mean']==13
panel.SaveScenario('無遮蔭基準')
plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(0,0,3000),Rhino.Geometry.Vector3d.ZAxis)
surface = Rhino.Geometry.PlaneSurface(plane,Rhino.Geometry.Interval(0,4000),Rhino.Geometry.Interval(0,8000))
shade_brep = surface.ToBrep()
shade = doc.Objects.AddBrep(shade_brep)
shade_brep.Dispose()
surface.Dispose()
request['ContextIds']=[str(shade)]
completed = json.loads(panel.ExecuteJson(json.dumps(request)))
assert completed['Statistics']['Count']==256 and completed['Statistics']['Mean']<13
panel.SaveScenario('新增遮蔭')
panel.CompareScenarios(0,1)
fixture = {'pid':identity['pid'],'document_serial':doc.RuntimeSerialNumber,'geometry':str(geometry),'shade':str(shade),
           'model_crc':{str(i):str(doc.Objects.FindId(i).Geometry.DataCRC(0)) for i in [geometry,shade]},
           'request':request,'shaded':completed['Statistics'],'baseline_mean':13,'scenarios':2,
           'result_json':panel.ExportResultJson(),'comparison_json':panel.ExportComparisonJson()}
json.dump(fixture,open(fixture_path,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
panel.ShowStage(5)
read_state()
