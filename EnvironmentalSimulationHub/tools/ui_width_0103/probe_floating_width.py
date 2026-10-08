import json
import System
import Rhino
import Eto.Forms as forms
import Eto.Drawing as drawing

assert System.Diagnostics.Process.GetCurrentProcess().Id == 12004
doc = __rhino_doc__
assert doc.RuntimeSerialNumber == 268435457
panel = Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'), doc.RuntimeSerialNumber)
window = panel.ParentWindow
assert isinstance(window, forms.Form), 'Only an Eto floating form can be resized'
assert window.NativeHandle != Rhino.UI.RhinoEtoApp.MainWindow.NativeHandle, 'Never resize the Rhino main window'
before = {'window': str(window.Size), 'panel': str(panel.Size), 'location': str(window.Location),
          'objects': doc.Objects.Count, 'modified': doc.Modified, 'module': str(panel.ActiveModule)}
try:
    window.Size = drawing.Size(500, window.Size.Height)
    Rhino.RhinoApp.Wait()
    after = {'window': str(window.Size), 'panel': str(panel.Size), 'location': str(window.Location),
             'objects': doc.Objects.Count, 'modified': doc.Modified, 'module': str(panel.ActiveModule)}
    assert window.Size.Width == 500 and panel.Size.Width >= 480
    assert all(before[k] == after[k] for k in ('location', 'objects', 'modified', 'module'))
    print(json.dumps({'before': before, 'after': after, 'public_api': 'Eto.Forms.Control.ParentWindow / Window.Size', 'restored': True}))
finally:
    width, height = [int(x) for x in before['window'].split(',')]
    window.Size = drawing.Size(width, height)
    Rhino.RhinoApp.Wait()
