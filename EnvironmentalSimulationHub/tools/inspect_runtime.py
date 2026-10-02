"""Read-only script executed in the explicitly selected Rhino MCP slot."""
import json
import System
import Rhino
import clr

report = {
    "rhino_version": str(Rhino.RhinoApp.Version),
    "dotnet_runtime": str(System.Environment.Version),
    "document": None,
}
doc = __rhino_doc__
if doc:
    objects = list(doc.Objects)
    report["document"] = {
        "name": doc.Name, "path": doc.Path, "units": str(doc.ModelUnitSystem),
        "absolute_tolerance": doc.ModelAbsoluteTolerance,
        "object_count": len(objects),
        "invalid_geometry_ids": [str(o.Id) for o in objects if not o.Geometry.IsValid],
        "geometry_types": sorted(set(str(o.Geometry.GetType()) for o in objects)),
        "layers": [{"name": l.FullPath, "visible": l.IsVisible}
                   for l in doc.Layers if not l.IsDeleted],
    }
try:
    clr.AddReference("Grasshopper")
    import Grasshopper
    kernel = Grasshopper.Kernel
    report["grasshopper_assembly_version"] = str(
        clr.GetClrType(kernel.GH_Document).Assembly.GetName().Version)
    canvas = Grasshopper.Instances.ActiveCanvas
    active = canvas.Document if canvas else None
    report["gh_active_document"] = str(active.DocumentID) if active else None
    report["gh_documents"] = []
    for definition in Grasshopper.Instances.DocumentServer:
        details = {"name": definition.DisplayName, "path": definition.FilePath,
                   "active": definition == active, "objects": [], "wire_count": 0}
        for item in definition.Objects:
            record = {"name": item.Name, "nickname": item.NickName,
                      "instance_guid": str(item.InstanceGuid),
                      "component_guid": str(item.ComponentGuid),
                      "type": str(item.GetType())}
            if isinstance(item, kernel.IGH_Component):
                record["inputs"] = [{"name": p.Name, "sources": [str(s.InstanceGuid)
                                     for s in p.Sources]} for p in item.Params.Input]
                record["outputs"] = [p.Name for p in item.Params.Output]
                details["wire_count"] += sum(p.SourceCount for p in item.Params.Input)
            if isinstance(item, kernel.Special.GH_Group):
                record["members"] = [str(g) for g in item.ObjectIDs]
            details["objects"].append(record)
        report["gh_documents"].append(details)
    report["loaded_assemblies"] = sorted([
        {"name": a.GetName().Name, "version": str(a.GetName().Version)}
        for a in System.AppDomain.CurrentDomain.GetAssemblies()
        if any(word in a.GetName().Name.lower() for word in
               ("ladybug", "honeybee", "dragonfly", "eddy", "grasshopper"))
    ], key=lambda a: a["name"])
except Exception as exc:
    report["grasshopper_error"] = str(exc)
print(json.dumps(report, ensure_ascii=False))
