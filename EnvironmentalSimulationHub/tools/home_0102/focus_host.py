"""Bring only the owned Rhino host forward using Rhino's own SDK."""
import System, Rhino, clr, json
Rhino.RhinoApp.SetFocusToMainWindow(__rhino_doc__)
host = Rhino.UI.RhinoEtoApp.MainWindow
print(json.dumps({'main_window': int(Rhino.RhinoApp.MainWindowHandle().ToInt64()),
                  'host_type': str(host.GetType().FullName),
                  'visible': host.Visible,
                  'state': str(host.WindowState) if hasattr(host, 'WindowState') else None,
                  'host_properties': [str(p) + ' writable=' + str(p.CanWrite) for p in host.GetType().GetProperties()
                                      if any(v in p.Name for v in ['Visible', 'WindowState', 'Size'])],
                  'host_methods': [str(m) for m in host.GetType().GetMethods()
                                   if m.Name in ['Show', 'BringToFront', 'Focus']],
                  'eto_members': [str(m) for m in clr.GetClrType(Rhino.UI.RhinoEtoApp).GetMembers()
                                  if 'Window' in m.Name or 'Theme' in m.Name]}))
