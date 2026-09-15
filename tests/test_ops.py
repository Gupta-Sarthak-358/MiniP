"""Ops tests: incident injection, drift monitor, conformal serving contract.
Run: Mnemo/.venv/Scripts/python.exe -m pytest tests/ -q
"""
import json, os
from fastapi.testclient import TestClient
from backend.app import app

c = TestClient(app)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_incident_validation():
    assert c.post("/api/incident", json={"location": "atlantis"}).status_code == 404
    r = c.post("/api/incident", json={"location": "mall", "kind": "meteor"})
    assert r.status_code == 422

def test_incident_flow_marks_zone():
    r = c.post("/api/incident", json={"location": "office", "kind": "closure",
                                      "severity": 3, "dur_steps": 4})
    assert r.status_code == 200 and r.json()["ok"] is True
    c.post("/api/step", params={"steps": 1})
    cur = c.get("/api/current-status", params={"location": "office"}).json()
    assert cur["is_incident"] == 1 and cur["incident_severity"] == 3

def test_drift_status_shape():
    c.post("/api/step", params={"steps": 2})
    d = c.get("/api/drift").json()
    assert isinstance(d, dict)
    for loc, s in d.items():
        assert {"n_paired", "recent_mae", "drift", "drift_events"} <= set(s)

def test_conformal_intervals_calibrated():
    conf = json.load(open(os.path.join(BASE, "models", "conformal.json")))
    assert set(conf) == {"15", "30", "45", "60"}
    qs = [conf[str(h)]["q90"] for h in (15, 30, 45, 60)]
    assert qs == sorted(qs) and all(q > 0 for q in qs)  # width grows with horizon
    p = c.get("/api/prediction", params={"location": "mall"}).json()
    assert p["interval_method"].startswith("conformal")
    assert p["calibration"]["30"]["empirical_coverage"] >= 0.85

def test_metrics_endpoint():
    m = c.get('/api/metrics').json()
    assert m['avail_mae30'] > 0 and 0 <= m['avail_skill30'] <= 1
    assert m['coverage30'] >= 0.85 and m['real_skill30'] > 0.3
