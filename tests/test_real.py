"""Real-zone replay contract tests (D14/E06)."""
import os
from fastapi.testclient import TestClient
from backend.app import app

c = TestClient(app)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_real_zone_shape_and_source():
    b = c.get("/api/real-zone").json()
    assert b["meta"]["is_real"] is True
    assert "Birmingham" in b["meta"]["source"] and "OGL" in b["meta"]["source"]
    assert 0 <= b["now"]["available"] <= b["now"]["capacity"] == 577
    assert [f["horizon_min"] for f in b["forecast"]] == [15, 30, 45, 60]
    assert all("persistence" in f["method"] for f in b["forecast"])

def test_real_zone_advances_on_step():
    i0 = c.get("/api/real-zone").json()["now"]["replay_index"]
    c.post("/api/step", params={"steps": 3})
    i1 = c.get("/api/real-zone").json()["now"]["replay_index"]
    assert i1 != i0

def test_real_eval_artifact():
    import json
    t = json.load(open(os.path.join(BASE, "models", "real_eval.json")))
    assert t["rf"]["skill30"] > 0.3  # ML clearly beats persistence on real sensors
    assert t["persistence"]["30"] > t["rf"]["30"]
