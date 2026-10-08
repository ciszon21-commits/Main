"""Read only host API and control geometry for remaining native UI checks."""
import json, System, Rhino, clr
clr.AddReference('Eto')
from Eto import Forms
from Eto.Drawing import SystemColors
from System.Reflection import BindingFlags
workspace = Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'))
native = workspace.ControlObject
info = {
    'rhino_methods': [str(m) for m in clr.GetClrType(Rhino.RhinoApp).GetMethods()
                     if any(s in m.Name for s in ['MainWindow', 'Focus', 'Visible'])],
    'appearance_members': [str(m) for m in clr.GetClrType(Rhino.ApplicationSettings.AppearanceSettings).GetMembers()
                           if any(s in m.Name.lower() for s in ['theme', 'dark', 'color'])],
    'workspace_size': [workspace.Width, workspace.Height],
    'native_size': [native.ActualWidth, native.ActualHeight],
    'window': int(Rhino.RhinoApp.MainWindowHandle().ToInt64()),
    'parent': str(native.Parent.GetType().FullName) if native.Parent is not None else None,
    'theme_background': str(SystemColors.ControlBackground),
    'pid': System.Diagnostics.Process.GetCurrentProcess().Id,
    'units': str(__rhino_doc__.ModelUnitSystem)
}
print(json.dumps(info))
