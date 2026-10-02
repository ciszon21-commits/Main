"""Actual Rhino viewport of tested SunPath geometry; owned release document only."""
import os,json,System,Rhino
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
doc=__rhino_doc__
assert doc.RuntimeSerialNumber==json.load(open(os.path.join(root,'docs/evidence/platform_092_runtime.json'),encoding='utf-8'))['document_serial']
workspace=Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'))
panel=workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunPathPanel'))
result=json.loads(panel.CompletedResultJson);assert len(result['Positions'])==5
view=doc.Views.ActiveView;old=Rhino.DocObjects.ViewportInfo(view.ActiveViewport);hidden=[]
try:
 for obj in doc.Objects:
  if not obj.IsHidden and not str(obj.Attributes.Name).startswith('EnvironmentalHub / SunPath'):
   if doc.Objects.Hide(obj.Id,True):hidden.append(obj.Id)
 v=view.ActiveViewport;radius=result['InputParameters']['RadiusMetres']/result['MetresPerModelUnit']
 v.ChangeToPerspectiveProjection(True,50)
 v.SetCameraLocations(Rhino.Geometry.Point3d(0,0,0),Rhino.Geometry.Point3d(radius*3,-radius*3,radius*2.2))
 v.CameraUp=Rhino.Geometry.Vector3d.ZAxis
 panel.LocateResult();doc.Views.Redraw()
 capture=Rhino.Display.ViewCapture();capture.Width=1200;capture.Height=900;capture.DrawGrid=False;capture.DrawGridAxes=False;capture.DrawAxes=False
 bitmap=capture.CaptureToBitmap(view)
 assert bitmap is not None
 path=os.path.join(root,'docs/evidence/ui_092/sunpath_viewport.png')
 try:bitmap.Save(path,System.Drawing.Imaging.ImageFormat.Png)
 finally:bitmap.Dispose()
 print(path)
finally:
 for identifier in hidden:doc.Objects.Show(identifier,True)
 view.ActiveViewport.SetViewProjection(old,False);doc.Views.Redraw()
