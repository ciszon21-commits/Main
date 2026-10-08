import System, Rhino
assert System.Diagnostics.Process.GetCurrentProcess().Id == 29180, 'Wrong Rhino process'
assert __rhino_doc__.RuntimeSerialNumber == 268435457, 'Wrong test document'
assert __rhino_doc__.Path in (None, ''), 'Only the owned unsaved test document is allowed'
import System, Rhino
workspace_id = System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
view_types = {'7281a8f2-e2c4-4c27-bcb5-22cbb0688b32': 'HubOverviewPanel', '1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a': 'WeatherPanel', '5f78d8d4-e9a1-4713-bb04-d08466339735': 'LocationPanel', '499a99e8-8e73-4a6b-8208-fc879e413d36': 'ClimateFilePanel', '06843693-df8a-421c-938b-96e2b9e88066': 'TimePanel', 'c62382ce-7709-4fcd-9dfb-447d1d8a08c0': 'RadiationPanel'}

def get_view(guid):
    workspace = Rhino.UI.Panels.GetPanel(workspace_id)
    return workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.' + view_types[str(guid)]))
'Rhino UI-thread WPF render of actual registered Eto panels; no Computer Use.'
import os, json, clr, System, Rhino
clr.AddReference('Eto')
import Eto.Forms as Forms
import Eto.Drawing as Drawing
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
from System.Windows import Size, Rect, Window, WindowStyle, Application
from System.Windows.Threading import DispatcherFrame, Dispatcher, DispatcherPriority
from System.Windows.Media import PixelFormats, DrawingVisual, VisualBrush, Stretch, BrushMappingMode
from System.Windows.Media.Imaging import RenderTargetBitmap, PngBitmapEncoder, BitmapFrame
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
dest = os.path.join(root, 'docs', 'evidence/home_0102/runtime', 'ui_0101')
os.makedirs(dest, exist_ok=True)
modules = [('overview', 'EnvironmentalHub', '7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'), ('weather', 'EnvironmentalWeather', '1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a'), ('location', 'EnvironmentalLocation', '5f78d8d4-e9a1-4713-bb04-d08466339735'), ('climate', 'EnvironmentalClimate', '499a99e8-8e73-4a6b-8208-fc879e413d36'), ('climate_location', 'EnvironmentalClimate', '499a99e8-8e73-4a6b-8208-fc879e413d36'), ('time', 'EnvironmentalTime', '06843693-df8a-421c-938b-96e2b9e88066'), ('time_period', 'EnvironmentalTime', '06843693-df8a-421c-938b-96e2b9e88066'), ('radiation', 'EnvironmentalRadiation', 'c62382ce-7709-4fcd-9dfb-447d1d8a08c0'), ('radiation_settings', 'EnvironmentalRadiation', 'c62382ce-7709-4fcd-9dfb-447d1d8a08c0'), ('radiation_results', 'EnvironmentalRadiation', 'c62382ce-7709-4fcd-9dfb-447d1d8a08c0'), ('radiation_compare', 'EnvironmentalRadiation', 'c62382ce-7709-4fcd-9dfb-447d1d8a08c0')]
shots = []
modules += [(n, 'EnvironmentalSunHours', 'sunhours') for n in ['sunhours_model', 'sunhours_source', 'sunhours_settings', 'sunhours_results', 'sunhours_view', 'sunhours_compare', 'sunhours_error']]
modules += [(name, 'EnvironmentalSunPath', 'sunpath') for name in ['sunpath_input', 'sunpath_settings', 'sunpath_results', 'sunpath_error']]
for (name, command, guid) in modules:
    Rhino.RhinoApp.RunScript(command, False)
    source = Rhino.UI.Panels.GetPanel(workspace_id).GetModule(Rhino.UI.Panels.GetPanel(workspace_id).GetType().Assembly.GetType('EnvironmentalHub.Plugin.' + ('SunHoursPanel' if guid == 'sunhours' else 'SunPathPanel'))) if guid in ['sunpath', 'sunhours'] else get_view(System.Guid(guid))
    workspace = System.Activator.CreateInstance(Rhino.UI.Panels.GetPanel(workspace_id).GetType())
    workspace.ShowModule(source.GetType())
    panel = workspace.GetModule(source.GetType())
    flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance
    labels = []
    if name.startswith('sunhours'):
        for item in source.GetType().GetField('scenarios', flags).GetValue(source):
            panel.GetType().GetField('scenarios', flags).GetValue(panel).Add(item)
    for field in [] if name == 'sunpath_input' else source.GetType().GetFields(flags):
        old = field.GetValue(source)
        new = field.GetValue(panel)
        if old is None or new is None or (not hasattr(old, 'GetType')):
            continue
        typename = str(old.GetType().FullName)
        if typename == 'Eto.Forms.DropDown':
            new.Items.Clear()
            for item in old.Items:
                new.Items.Add(str(item.Text))
            new.SelectedIndex = old.SelectedIndex
        elif typename == 'Eto.Forms.NumericStepper':
            new.Value = old.Value
        elif typename == 'Eto.Forms.CheckBox':
            new.Checked = old.Checked
        elif typename in ['Eto.Forms.Label', 'Eto.Forms.TextBox', 'Eto.Forms.Button']:
            labels.append((old, new))
    for (old, new) in labels:
        new.Text = old.Text
        new.Enabled = old.Enabled
        if isinstance(old, Forms.Label):
            new.Font = old.Font
    if name.startswith('sunhours'):
        result = source.GetType().GetField('result', flags).GetValue(source)
        panel.GetType().GetField('result', flags).SetValue(panel, result)
        if result is not None:
            presenter = source.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunHoursPresentation')
            panel.GetType().GetField('legend', flags).GetValue(panel).Content = presenter.GetMethod('Legend', System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic).Invoke(None, System.Array[System.Object]([result]))
        if name == 'sunhours_settings':
            panel.GetType().GetField('reveal', flags).GetValue(panel).Checked = True
        if name == 'sunhours_error':
            try:
                panel.ExecuteJson('{}')
            except Exception:
                pass
    if name.startswith('radiation'):
        result = source.GetType().GetField('lastResult', flags).GetValue(source)
        panel.GetType().GetField('lastResult', flags).SetValue(panel, result)
        if result is not None:
            presenter = source.GetType().Assembly.GetType('EnvironmentalHub.Plugin.ResultPresentation')
            content = presenter.GetMethod('Legend', System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic).Invoke(None, System.Array[System.Object]([result]))
            panel.GetType().GetField('legend', flags).GetValue(panel).Content = content

        def walk(c):
            yield c
            if hasattr(c, 'Controls'):
                for child in c.Controls:
                    for item in walk(child):
                        yield item
        if name == 'radiation_settings':
            next((c for c in walk(panel) if isinstance(c, Forms.CheckBox) and c.Text == '進階設定')).Checked = True
    if name == 'time_period':
        fixture = json.load(open(os.path.join(root, 'samples/home_0102', 'weather_0101', 'analysis_period.json'), encoding='utf-8'))
        panel.ExecutePeriodJson(json.dumps(fixture['InputParameters']))
    if name == 'climate_location':
        fixture = json.load(open(os.path.join(root, 'samples/home_0102', 'weather_0101', 'import_ddy.json'), encoding='utf-8'))
        panel.ExecuteJson(json.dumps(fixture['InputParameters']))
    if name.startswith('sunpath') and name != 'sunpath_input':
        panel.GetType().GetField('result', flags).SetValue(panel, source.GetType().GetField('result', flags).GetValue(source))
        if name == 'sunpath_settings':
            panel.GetType().GetField('reveal', flags).GetValue(panel).Checked = True
        if name == 'sunpath_error':
            try:
                panel.ExecuteJson(json.dumps({'RadiusMetres': 0}))
            except Exception:
                pass
    try:
        native = workspace.ControlObject
    except Exception:
        try:
            native = workspace.Handler.Control
        except Exception:
            raise RuntimeError('Native control accessor unavailable: ' + str([str(p.Name) for p in panel.GetType().GetProperties()]))
    if not hasattr(native, 'Measure'):
        raise RuntimeError('Not a WPF framework element: ' + str(native.GetType().FullName))
    window = Forms.Form()
    window.ShowInTaskbar = False
    window.Location = Drawing.Point(-10000, -10000)
    window.Content = workspace
    try:
        for width in [320, 480]:
            window.ClientSize = Drawing.Size(width, 760)
            native.Width = width
            native.Height = 760
            window.Show()
            native.ApplyTemplate()
            native.UpdateLayout()
            frame = DispatcherFrame()

            def ready():
                frame.Continue = False
            native.Dispatcher.BeginInvoke(System.Action(ready), DispatcherPriority.ContextIdle)
            Dispatcher.PushFrame(frame)
            native.Measure(Size(width, 760))
            native.Arrange(Rect(0, 0, width, 760))
            native.UpdateLayout()
            if name.startswith('sunhours'):
                panel.ShowStage({'sunhours_model': 0, 'sunhours_source': 1, 'sunhours_settings': 2, 'sunhours_results': 4, 'sunhours_view': 4, 'sunhours_compare': 5, 'sunhours_error': 3}[name])
                native.UpdateLayout()
                if name == 'sunhours_view':
                    target = panel.GetType().GetField('displayOffset', flags).GetValue(panel)
                    scroll = panel.GetType().GetField('scroll', flags).GetValue(panel)
                    top = scroll.Content.PointToScreen(Drawing.PointF.Empty)
                    position = target.PointToScreen(Drawing.PointF.Empty)
                    scroll.ScrollPosition = Drawing.Point(0, max(0, int(position.Y - top.Y) - 12))
                    native.UpdateLayout()
            if name.startswith('radiation'):
                panel.ShowStage({'radiation': 0, 'radiation_settings': 2, 'radiation_results': 4, 'radiation_compare': 5}[name])
                native.UpdateLayout()
            if name in ['sunpath_settings', 'sunpath_results', 'sunpath_error']:
                field = {'sunpath_settings': 'month', 'sunpath_results': 'summary', 'sunpath_error': 'run'}[name]
                target = panel.GetType().GetField(field, flags).GetValue(panel)
                scroll = panel.Content
                top = scroll.Content.PointToScreen(Drawing.PointF.Empty)
                position = target.PointToScreen(Drawing.PointF.Empty)
                scroll.ScrollPosition = Drawing.Point(0, max(0, int(position.Y - top.Y) - 12))
                native.UpdateLayout()
            visual = DrawingVisual()
            context = visual.RenderOpen()
            brush = VisualBrush(native)
            brush.Stretch = Stretch.Fill
            brush.ViewboxUnits = BrushMappingMode.Absolute
            brush.Viewbox = Rect(0, 0, width, 760)
            try:
                context.DrawRectangle(brush, None, Rect(0, 0, width, 760))
            finally:
                context.Close()
            bitmap = RenderTargetBitmap(width, 760, 96, 96, PixelFormats.Pbgra32)
            bitmap.Render(visual)
            path = os.path.join(dest, name + '_' + str(width) + '.png')
            encoder = PngBitmapEncoder()
            encoder.Frames.Add(BitmapFrame.Create(bitmap))
            stream = System.IO.FileStream(path, System.IO.FileMode.Create)
            try:
                encoder.Save(stream)
            finally:
                stream.Dispose()
            shots.append({'module': name, 'width': width, 'actual_width': native.ActualWidth, 'actual_height': native.ActualHeight, 'path': path, 'native_type': str(native.GetType().FullName)})
    finally:
        window.Close()
        window.Dispose()
Rhino.RhinoApp.RunScript('EnvironmentalHub', False)
json.dump({'scope': 'Production unified workspace and cached module views hosted offscreen at 320/480, with actual tested control state copied from live workspace views; current host theme only; no full Dock/dialog/keyboard/theme-switch acceptance', 'shots': shots}, open(os.path.join(dest, 'capture.json'), 'w', encoding='utf-8'), indent=2)
print(json.dumps({'captured': len(shots), 'output': dest}))