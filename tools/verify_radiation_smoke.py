"""Verify Rhino-origin input, repeatability, colored result, and export a fixture."""
import os
import json
import math
import hashlib
import System
import Rhino
import clr
from System.Drawing import Color
from System.Collections.Generic import List
clr.AddReference("Grasshopper")
import Grasshopper as GH
from Grasshopper.Kernel.Types import GH_Brep
from Grasshopper.Kernel.Data import GH_Path

doc = __rhino_doc__
work = os.path.join(hub_root, "samples", "radiation_smoke")
workflow_path = os.path.join(hub_root, "workflows", "radiation", "radiation_main.gh")
definition = next(d for d in GH.Instances.DocumentServer if d.FilePath == workflow_path)
radiation = next(c for c in definition.Objects if c.Name == "LB Incident Radiation")
geometry = next(c for c in definition.Objects if c.NickName.startswith("AnalysisGeometry"))
receipt = json.load(open(os.path.join(work, "runtime_result.json"), encoding="utf-8"))
old_values = receipt["values"]

def layer(name, color):
    index = doc.Layers.FindByFullPath(name, -1)
    if index < 0:
        value = Rhino.DocObjects.Layer()
        value.Name = name
        value.Color = color
        index = doc.Layers.Add(value)
    return index

input_layer = layer("EnvironmentalHub_Input", Color.Gray)
attrs = Rhino.DocObjects.ObjectAttributes()
attrs.LayerIndex = input_layer
attrs.Name = "Radiation smoke / 4m horizontal plane"
brep = list(geometry.PersistentData.AllData(True))[0].Value
object_id = doc.Objects.AddBrep(brep, attrs)
rhino_object = doc.Objects.FindId(object_id)
if not rhino_object or not rhino_object.Geometry.IsValid:
    raise ValueError("RAD-INPUT-002: Rhino fixture geometry invalid")
geometry.PersistentData.Clear()
geometry.PersistentData.Append(GH_Brep(rhino_object.Geometry.DuplicateBrep()), GH_Path(0))
geometry.ExpireSolution(False)
definition.NewSolution(False)

def output(name):
    p = next(p for p in radiation.Params.Output if p.Name == name)
    return list(p.VolatileData.AllData(True))

new_values = [float(v.Value) for v in output("results")]
if len(new_values) != len(old_values) or any(not math.isfinite(v) for v in new_values):
    raise RuntimeError("RAD-RESULT-001: Result count or finite-value check failed")
delta = max(abs(a - b) for a, b in zip(old_values, new_values))
if delta > 1e-9:
    raise RuntimeError("RAD-VERIFY-001: Repeat run differs from the stock baseline")
mesh = output("mesh")[0].Value
if not isinstance(mesh, Rhino.Geometry.Mesh) or mesh.Faces.Count != len(new_values):
    raise RuntimeError("RAD-RESULT-002: Mesh/value alignment failed")
result_layer = layer("EnvironmentalHub_Radiation_Result", Color.DodgerBlue)
result_attrs = Rhino.DocObjects.ObjectAttributes()
result_attrs.LayerIndex = result_layer
result_attrs.Name = "Ladybug annual radiation / Seattle smoke / kWh per m2"
mesh_id = doc.Objects.AddMesh(mesh, result_attrs)
doc.Layers[input_layer].IsVisible = False
io = GH.Kernel.GH_DocumentIO(definition)
if not io.SaveQuiet(workflow_path):
    raise RuntimeError("RAD-EXPORT-001: Saving verified workflow failed")
sample = Rhino.FileIO.File3dm()
sample.Settings.ModelUnitSystem = doc.ModelUnitSystem
sample.Objects.AddBrep(rhino_object.Geometry, Rhino.DocObjects.ObjectAttributes())
sample.Objects.AddMesh(mesh, Rhino.DocObjects.ObjectAttributes())
sample_path = os.path.join(work, "radiation_smoke.3dm")
if not sample.Write(sample_path, 8):
    raise RuntimeError("RAD-EXPORT-002: Saving fixture model failed")
Rhino.RhinoApp.RunScript("_Zoom _Extents", False)
doc.Views.Redraw()
capture = Rhino.Display.ViewCapture()
capture.Width = 1200
capture.Height = 800
capture.DrawGrid = False
capture.DrawAxes = False
capture.DrawGridAxes = False
bitmap = capture.CaptureToBitmap(doc.Views.ActiveView)
preview_path = os.path.join(work, "rhino_preview.png")
bitmap.Save(preview_path, System.Drawing.Imaging.ImageFormat.Png)
bitmap.Dispose()
receipt.update({"rhino_input_object_id": str(object_id),
                "rhino_result_mesh_id": str(mesh_id),
                "input_binding": "Rhino object geometry snapshot; selection adapter pending",
                "repeat_run_max_absolute_difference": delta,
                "repeatability_verified": True, "mesh_value_alignment_verified": True,
                "fixture_model": sample_path, "preview": preview_path,
                "scientific_validation": "Stock Ladybug repeatability only; broader benchmarks pending"})
with open(os.path.join(work, "runtime_result.json"), "w", encoding="utf-8") as f:
    json.dump(receipt, f, ensure_ascii=False, indent=2)
print(json.dumps({"status": "RUNTIME_VERIFIED", "input_object": str(object_id),
                  "values": len(new_values), "repeat_delta": delta,
                  "preview": preview_path}))
