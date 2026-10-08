import json
import System
import Rhino

assert System.Diagnostics.Process.GetCurrentProcess().Id == 12004, 'Host changed; rediscover before running'
doc = __rhino_doc__
plugin = Rhino.PlugIns.PlugIn.Find(System.Guid('bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f'))
proof = {'pid': 12004, 'document_serial': doc.RuntimeSerialNumber,
         'object_count': doc.Objects.Count, 'document_modified': doc.Modified,
         'plugin_loaded': plugin is not None}
if plugin is not None:
    assembly = plugin.GetType().Assembly
    proof['assembly'] = assembly.Location
    proof['version'] = str(assembly.GetName().Version)
    panel_type = assembly.GetType('EnvironmentalHub.Plugin.HubWorkspacePanel')
    panel = Rhino.UI.Panels.GetPanel(panel_type.GUID, doc.RuntimeSerialNumber)
    proof['visible'] = Rhino.UI.Panels.IsPanelVisible(panel_type, True)
    proof['panel_created'] = panel is not None
    if panel is not None:
        proof['size'] = str(panel.Size)
        proof['active_module'] = str(panel.ActiveModule)
        proof['parent_window'] = str(panel.ParentWindow)
        proof['parents'] = []
        parent = panel.Parent
        while parent is not None:
            proof['parents'].append({'type': str(parent.GetType()), 'size': str(parent.Size)})
            parent = parent.Parent
print(json.dumps(proof, ensure_ascii=False))
