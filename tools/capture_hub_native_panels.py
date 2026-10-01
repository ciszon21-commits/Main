"""Rhino UI-thread WPF render of actual registered Eto panels; no Computer Use."""
import os,json,clr,System,Rhino
clr.AddReference('Eto')
import Eto.Forms as Forms
import Eto.Drawing as Drawing
clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from System.Windows import Size,Rect,Window,WindowStyle,Application
from System.Windows.Threading import DispatcherFrame,Dispatcher,DispatcherPriority
from System.Windows.Media import PixelFormats,DrawingVisual,VisualBrush,Stretch,BrushMappingMode
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
dest=os.path.join(root,'docs','evidence','ui_085');os.makedirs(dest,exist_ok=True)
modules=[('overview','EnvironmentalHub','7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'),
 ('weather','EnvironmentalWeather','1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a'),
 ('location','EnvironmentalLocation','5f78d8d4-e9a1-4713-bb04-d08466339735'),
 ('climate','EnvironmentalClimate','499a99e8-8e73-4a6b-8208-fc879e413d36'),
 ('climate_location','EnvironmentalClimate','499a99e8-8e73-4a6b-8208-fc879e413d36'),
 ('time','EnvironmentalTime','06843693-df8a-421c-938b-96e2b9e88066'),
 ('time_period','EnvironmentalTime','06843693-df8a-421c-938b-96e2b9e88066'),
 ('radiation','EnvironmentalRadiation','c62382ce-7709-4fcd-9dfb-447d1d8a08c0'),
 ('radiation_settings','EnvironmentalRadiation','c62382ce-7709-4fcd-9dfb-447d1d8a08c0'),
 ('radiation_results','EnvironmentalRadiation','c62382ce-7709-4fcd-9dfb-447d1d8a08c0'),
 ('radiation_compare','EnvironmentalRadiation','c62382ce-7709-4fcd-9dfb-447d1d8a08c0')]
shots=[]
for name,command,guid in modules:
 Rhino.RhinoApp.RunScript(command,False)
 source=Rhino.UI.Panels.GetPanel(System.Guid(guid))
 # Dock parents clip inactive panels. Host a second instance of the same
 # production panel class offscreen, copying its actual tested control state.
 panel=System.Activator.CreateInstance(source.GetType())
 flags=System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance
 labels=[]
 for field in source.GetType().GetFields(flags):
  old=field.GetValue(source);new=field.GetValue(panel)
  if old is None or new is None or not hasattr(old,'GetType'):continue
  typename=str(old.GetType().FullName)
  if typename=='Eto.Forms.DropDown':
   new.Items.Clear()
   for item in old.Items:new.Items.Add(str(item.Text))
   new.SelectedIndex=old.SelectedIndex
  elif typename=='Eto.Forms.NumericStepper':new.Value=old.Value
  elif typename=='Eto.Forms.CheckBox':new.Checked=old.Checked
  elif typename in ['Eto.Forms.Label','Eto.Forms.TextBox','Eto.Forms.Button']:labels.append((old,new))
 for old,new in labels:
  new.Text=old.Text;new.Enabled=old.Enabled
  if isinstance(old,Forms.Label):new.Font=old.Font
 if name.startswith('radiation'):
  result=source.GetType().GetField('lastResult',flags).GetValue(source)
  panel.GetType().GetField('lastResult',flags).SetValue(panel,result)
  if result is not None:
   presenter=source.GetType().Assembly.GetType('EnvironmentalHub.Plugin.ResultPresentation')
   content=presenter.GetMethod('Legend',System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic).Invoke(None,System.Array[System.Object]([result]))
   panel.GetType().GetField('legend',flags).GetValue(panel).Content=content
  def walk(c):
   yield c
   if hasattr(c,'Controls'):
    for child in c.Controls:
     for item in walk(child):yield item
  if name=='radiation_settings':
   next(c for c in walk(panel) if isinstance(c,Forms.CheckBox) and c.Text=='Advanced settings').Checked=True
 if name=='time_period':
  fixture=json.load(open(os.path.join(root,'samples','weather','analysis_period.json'),encoding='utf-8'))
  panel.ExecutePeriodJson(json.dumps(fixture['InputParameters']))
 if name=='climate_location':
  fixture=json.load(open(os.path.join(root,'samples','weather','import_ddy.json'),encoding='utf-8'))
  panel.ExecuteJson(json.dumps(fixture['InputParameters']))
 try:native=panel.ControlObject
 except Exception:
  try:native=panel.Handler.Control
  except Exception:
   raise RuntimeError('Native control accessor unavailable: '+str([str(p.Name) for p in panel.GetType().GetProperties()]))
 if not hasattr(native,'Measure'):raise RuntimeError('Not a WPF framework element: '+str(native.GetType().FullName))
 window=Forms.Form();window.ShowInTaskbar=False;window.Location=Drawing.Point(-10000,-10000);window.Content=panel
 try:
  for width in [320,480]:
   window.ClientSize=Drawing.Size(width,760)
   native.Width=width;native.Height=760
   window.Show();native.ApplyTemplate();native.UpdateLayout()
   frame=DispatcherFrame()
   def ready():frame.Continue=False
   native.Dispatcher.BeginInvoke(System.Action(ready),DispatcherPriority.ContextIdle)
   Dispatcher.PushFrame(frame)
   native.Measure(Size(width,760));native.Arrange(Rect(0,0,width,760));native.UpdateLayout()
   if name.startswith('radiation'):
    panel.ShowStage({'radiation':0,'radiation_settings':2,'radiation_results':4,'radiation_compare':5}[name]);native.UpdateLayout()
   # Draw through a VisualBrush to avoid the Dock parent's screen offset/clip.
   visual=DrawingVisual();context=visual.RenderOpen()
   brush=VisualBrush(native);brush.Stretch=Stretch.Fill
   brush.ViewboxUnits=BrushMappingMode.Absolute;brush.Viewbox=Rect(0,0,width,760)
   try:context.DrawRectangle(brush,None,Rect(0,0,width,760))
   finally:context.Close()
   bitmap=RenderTargetBitmap(width,760,96,96,PixelFormats.Pbgra32);bitmap.Render(visual)
   path=os.path.join(dest,name+'_'+str(width)+'.png')
   encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap))
   stream=System.IO.FileStream(path,System.IO.FileMode.Create)
   try:encoder.Save(stream)
   finally:stream.Dispose()
   shots.append({'module':name,'width':width,'actual_width':native.ActualWidth,'actual_height':native.ActualHeight,'path':path,'native_type':str(native.GetType().FullName)})
 finally:
  window.Close();window.Dispose()
Rhino.RhinoApp.RunScript('EnvironmentalHub',False)
json.dump({'scope':'Production Eto/WPF panel classes hosted offscreen at 320/480, with actual tested control state copied from registered panels; current host theme only; no full Dock/dialog/keyboard/theme-switch acceptance','shots':shots},open(os.path.join(dest,'capture.json'),'w',encoding='utf-8'),indent=2)
print(json.dumps({'captured':len(shots),'output':dest}))
