"""Native viewport QA in the owned release document; all temporary visibility/camera edits restored."""
import os,json,System,Rhino
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub';doc=__rhino_doc__
fixture=json.load(open(os.path.join(root,'docs/evidence/sunhours_0101_visual_fixture.json'),encoding='utf-8'));assert doc.RuntimeSerialNumber==fixture['document_serial']
Rhino.RhinoApp.RunScript('EnvironmentalSunHours',False);workspace=Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'));panel=workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel'))
result=json.loads(panel.CompletedResultJson);assert result['Statistics']==fixture['shaded']
scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem);view=doc.Views.ActiveView;old=Rhino.DocObjects.ViewportInfo(view.ActiveViewport);old_mode=view.ActiveViewport.DisplayMode;hidden=[];paths=[]
try:
 for obj in doc.Objects:
  if not obj.IsHidden and str(obj.Id) not in fixture['geometry'] and obj.Attributes.GetUserString('EnvironmentalHub.PreviewOwner')!='bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f/SunHours':
   if doc.Objects.Hide(obj.Id,True):hidden.append(obj.Id)
 v=view.ActiveViewport;v.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.ShadedId)
 v.ChangeToPerspectiveProjection(True,50);v.SetCameraLocations(Rhino.Geometry.Point3d(4*scale,4*scale,0),Rhino.Geometry.Point3d(16*scale,-12*scale,12*scale));v.CameraUp=Rhino.Geometry.Vector3d.ZAxis
 bounds=Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(-scale,-scale,-scale),Rhino.Geometry.Point3d(9*scale,9*scale,4*scale));v.ZoomBoundingBox(bounds)
 capture=Rhino.Display.ViewCapture();capture.Width=1200;capture.Height=900;capture.DrawGrid=False;capture.DrawGridAxes=False;capture.DrawAxes=False
 for name,hide_context in [('sunhours_context',False),('sunhours_result',True)]:
  if hide_context:doc.Objects.Hide(System.Guid(fixture['geometry'][1]),True);hidden.append(System.Guid(fixture['geometry'][1]))
  doc.Views.Redraw();bitmap=capture.CaptureToBitmap(view);assert bitmap is not None
  path=os.path.join(root,'docs/evidence/ui_0101',name+'.png')
  try:bitmap.Save(path,System.Drawing.Imaging.ImageFormat.Png)
  finally:bitmap.Dispose()
  paths.append(path)
 json.dump({'version':'0.10.1','paths':paths,'statistics':result['Statistics'],'native_colors':fixture['native_colors'],'display_offset_metres':.002,'scope':'Real Rhino shaded perspective. Context shown in first image and temporarily hidden in second to inspect all result faces; numeric values and native palette unchanged. Camera/mode/temporary visibility restored.'},open(os.path.join(root,'docs/evidence/ui_0101/viewport_capture.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print(json.dumps({'images':len(paths)}))
finally:
 for i in hidden:doc.Objects.Show(i,True)
 view.ActiveViewport.SetViewProjection(old,False);view.ActiveViewport.DisplayMode=old_mode;doc.Views.Redraw()
