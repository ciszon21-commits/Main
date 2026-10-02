"""Build and solve a minimal workflow with original installed Ladybug components.

Caller provides hub_root, weather_file, and user_object_root. This is a Phase 0
runtime fixture, not the future production adapter or a physics implementation.
"""
import os
import json
import time
import hashlib
import System
import Rhino
import clr
from System.Drawing import PointF, Color
clr.AddReference("Grasshopper")
import Grasshopper as GH
from Grasshopper.Kernel import GH_Document, GH_RuntimeMessageLevel
from Grasshopper.Kernel.Special import GH_Panel, GH_Group
from Grasshopper.Kernel.Parameters import Param_Brep
from Grasshopper.Kernel.Types import GH_Brep
from Grasshopper.Kernel.Data import GH_Path

rhino_doc = __rhino_doc__
if not rhino_doc:
    raise ValueError("RAD-INPUT-001: Rhino document missing")
if not os.path.isfile(weather_file):
    raise ValueError("CLIMATE-EPW-003: Weather file missing")
scale = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters, rhino_doc.ModelUnitSystem)
if not scale > 0:
    raise ValueError("RAD-UNIT-001: Model unit conversion invalid")
work = os.path.join(hub_root, "samples", "radiation_smoke")
os.makedirs(work, exist_ok=True)
workflow_path = os.path.join(hub_root, "workflows", "radiation", "radiation_main.gh")
os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
if os.path.exists(workflow_path):
    raise ValueError("Existing workflow requires a checkpoint before rebuilding")
definition = GH_Document()
definition.FilePath = workflow_path

def add(obj, x, y):
    obj.CreateAttributes()
    obj.Attributes.Pivot = PointF(x, y)
    definition.AddObject(obj, False)
    return obj

def stock(name, x, y):
    target = os.path.join(user_object_root, name + ".ghuser")
    if not os.path.isfile(target):
        raise ValueError("RAD-PLUGIN-001: Missing installed user object: " + name)
    obj = GH.Kernel.GH_UserObject(target).InstantiateObject()
    return add(obj, x, y)

def panel(name, value, x, y):
    obj = GH_Panel()
    obj.NickName = name
    obj.UserText = str(value)
    return add(obj, x, y)

def port(component, name, output=False):
    params = component.Params.Output if output else component.Params.Input
    return next(p for p in params if p.Name == name)

def wire(source, output, target, input_name):
    port(target, input_name).AddSource(port(source, output, True))

def group(name, items):
    obj = GH_Group()
    obj.NickName = name
    obj.Colour = Color.FromArgb(70, 40, 110, 200)
    definition.AddObject(obj, False)
    for item in items:
        obj.AddObject(item.InstanceGuid)

weather = panel("EPW / Seattle bundled smoke fixture", weather_file, 30, 50)
grid = panel("Grid / model units (1 metre)", scale, 30, 200)
folder = panel("Run folder", work, 30, 300)
run = panel("Run", "True", 30, 400)
north = panel("North / degrees", 0, 30, 500)
cpu = panel("CPU count", 1, 30, 600)
geometry = add(Param_Brep(), 260, 220)
geometry.NickName = "AnalysisGeometry / 4m x 4m"
surface = Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY,
    Rhino.Geometry.Interval(0, 4 * scale), Rhino.Geometry.Interval(0, 4 * scale)).ToBrep()
geometry.PersistentData.Append(GH_Brep(surface), GH_Path(0))
epw = stock("LB Import EPW", 450, 60)
sky = stock("LB Cumulative Sky Matrix", 700, 60)
radiation = stock("LB Incident Radiation", 960, 200)
port(epw, "_epw_file").AddSource(weather)
wire(epw, "location", sky, "_location")
wire(epw, "direct_normal_rad", sky, "_direct_rad")
wire(epw, "diffuse_horizontal_rad", sky, "_diffuse_rad")
port(sky, "north_").AddSource(north)
port(sky, "_folder_").AddSource(folder)
wire(sky, "sky_mtx", radiation, "_sky_mtx")
port(radiation, "_geometry").AddSource(geometry)
port(radiation, "_grid_size").AddSource(grid)
port(radiation, "_cpu_count_").AddSource(cpu)
port(radiation, "_run").AddSource(run)
group("00_INPUT", [weather, grid, folder, run, north, cpu, geometry])
group("10_PREPROCESS / EPW", [epw])
group("40_SOLVER / Radiance gendaymtx + Ladybug", [sky, radiation])
GH.Instances.DocumentServer.AddDocument(definition)
definition.Enabled = True
start = time.time()
definition.NewSolution(False)
errors = []
warnings = []
for component in (epw, sky, radiation):
    errors.extend(component.Name + ": " + str(m) for m in
                  component.RuntimeMessages(GH_RuntimeMessageLevel.Error))
    warnings.extend(component.Name + ": " + str(m) for m in
                    component.RuntimeMessages(GH_RuntimeMessageLevel.Warning))
def data(name):
    return list(port(radiation, name, True).VolatileData.AllData(True))
values = [float(v.Value) for v in data("results")]
meshes = [v.Value for v in data("mesh") if hasattr(v, "Value")
          and isinstance(v.Value, Rhino.Geometry.Mesh)]
receipt = {"status": "RUNTIME_FAILED", "errors": errors, "warnings": warnings,
           "values": values, "mesh_count": len(meshes),
           "legend_item_count": len(data("legend")), "unit": "kWh/m2",
           "workflow": workflow_path, "weather": weather_file,
           "weather_sha256": hashlib.sha256(open(weather_file, "rb").read()).hexdigest(),
           "model_units": str(rhino_doc.ModelUnitSystem), "grid_model_units": scale,
           "grid_metres": 1, "period": "annual", "north_degrees": 0,
           "cpu_count": 1, "sky_density": "Tregenza", "fixture_city": "Seattle",
           "elapsed_seconds": time.time() - start,
           "component_versions": {c.Name: c.Message for c in (epw, sky, radiation)}}
if errors or not values or not meshes or not receipt["legend_item_count"]:
    with open(os.path.join(work, "runtime_result.json"), "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    raise RuntimeError(json.dumps(receipt))
receipt["statistics"] = {"min": min(values), "max": max(values),
                         "mean": sum(values) / len(values), "count": len(values)}
receipt["result_mesh_faces"] = sum(m.Faces.Count for m in meshes)
receipt["result_mesh_vertex_colors"] = sum(m.VertexColors.Count for m in meshes)
receipt["status"] = "RUNTIME_VERIFIED"
io = GH.Kernel.GH_DocumentIO(definition)
if not io.SaveQuiet(workflow_path):
    raise RuntimeError("RAD-EXPORT-001: Workflow save failed")
Rhino.RhinoApp.RunScript("_Grasshopper", False)
GH.Instances.ActiveCanvas.Document = definition
rhino_doc.Views.Redraw()
with open(os.path.join(work, "runtime_result.json"), "w", encoding="utf-8") as f:
    json.dump(receipt, f, ensure_ascii=False, indent=2)
print(json.dumps(receipt))
