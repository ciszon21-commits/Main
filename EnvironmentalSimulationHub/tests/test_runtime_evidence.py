"""Check preserved runtime evidence; these do not pretend to execute a solver."""
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RuntimeEvidenceTests(unittest.TestCase):
    def test_physical_result_matches_original_transport(self):
        result = json.loads((ROOT / "samples/radiation_smoke/runtime_result.json").read_text(encoding="utf-8"))
        raw = json.loads((ROOT / "docs/evidence/radiation_retry_transport.json").read_text(encoding="utf-8"))
        content = raw["calls"][0]["response"]["result"]["content"]
        original = json.loads(next(c["text"] for c in content if c["type"] == "text"))["payload"]
        self.assertEqual(result["status"], "RUNTIME_VERIFIED")
        self.assertEqual(result["values"], original["values"])
        self.assertTrue(all(math.isfinite(v) and v >= 0 for v in result["values"]))
        self.assertEqual(len(result["values"]), result["result_mesh_faces"])
        self.assertEqual(result["statistics"]["mean"], sum(result["values"]) / len(result["values"]))
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["repeatability_verified"])
        self.assertEqual(result["repeat_run_max_absolute_difference"], 0)

    def test_saved_workflow_matches_checkpoint(self):
        definition = ROOT / "workflows/radiation/radiation_main.gh"
        checkpoint = ROOT / "docs/evidence/radiation_verified_checkpoint.gh"
        self.assertGreater(definition.stat().st_size, 0)
        self.assertEqual(definition.read_bytes(), checkpoint.read_bytes())
        self.assertGreater((ROOT / "samples/radiation_smoke/radiation_smoke.3dm").stat().st_size, 0)

    def test_audit_has_no_hidden_scan_failure(self):
        audit = json.loads((ROOT / "docs/evidence/asset_inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["scan_returncode"], 0, audit["scan_stderr"])
        self.assertEqual(audit["scan_stderr"], "")
        solvers = json.loads((ROOT / "docs/evidence/solver_audit.json").read_text(encoding="utf-8"))
        self.assertTrue(all(s["exit_code"] == 0 for s in solvers["solvers"].values()))
        self.assertEqual(solvers["OpenFOAM"]["status"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
