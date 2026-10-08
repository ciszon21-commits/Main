import os, json, System, Rhino, scriptcontext as sc, clr
assert System.Diagnostics.Process.GetCurrentProcess().Id == __OWNED_PID__
test = sc.sticky['ESH_DEPLOY_0109']
doc = __rhino_doc__
assert doc.RuntimeSerialNumber == test['identity']['document_serial']
workspace = test['workspace']; panel = test['panel']
from Eto.Forms import Form
from Eto.Drawing import Size as EtoSize
clr.AddReference('PresentationCore'); clr.AddReference('PresentationFramework'); clr.AddReference('WindowsBase')
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap, PngBitmapEncoder, BitmapFrame
from System.Reflection import BindingFlags
native = workspace.Handler.GetType().GetProperty('Control').GetValue(workspace.Handler)
window = workspace.ParentWindow
assert isinstance(window, Form) and window.NativeHandle != Rhino.RhinoApp.MainWindowHandle()
shots = []
for width in [320, 480]:
    window.ClientSize = EtoSize(width, 920)
    Rhino.RhinoApp.Wait()
    native.UpdateLayout()
    # Resize only this plugin's dedicated floating window to the requested actual panel width.
    for retry in range(3):
        delta = width - int(round(native.ActualWidth))
        if delta == 0: break
        window.ClientSize = EtoSize(window.ClientSize.Width + delta, window.ClientSize.Height)
        Rhino.RhinoApp.Wait(); native.UpdateLayout()
    panel.ShowStage(4); Rhino.RhinoApp.Wait(); native.UpdateLayout()
    actual_width, height = int(round(native.ActualWidth)), int(round(native.ActualHeight))
    assert actual_width == width and height > 0, 'Native panel width mismatch'
    bitmap = RenderTargetBitmap(actual_width, height, 96, 96, PixelFormats.Pbgra32)
    bitmap.Render(native)
    target = os.path.join(root, 'docs/evidence/deploy_0109', 'native-' + str(width) + '.png')
    encoder = PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(bitmap))
    stream = System.IO.FileStream(target, System.IO.FileMode.Create)
    try: encoder.Save(stream)
    finally: stream.Dispose()
    shots.append({'width':width,'actual_width':native.ActualWidth,'actual_height':native.ActualHeight,'path':target,'type':str(native.GetType().FullName)})
json.dump({'scope':'Actual registered native floating workspace; current system theme; WPF SDK bitmap. Full Dock theme/DPI/keyboard not claimed. WebView remains disabled.', 'shots':shots}, open(os.path.join(root,'docs/evidence/deploy_0109/capture.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps({'captured':len(shots)}))
