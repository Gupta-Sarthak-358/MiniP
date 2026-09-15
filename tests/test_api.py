"""API regression tests: success path, validation-failure path, simulator persistence.
Run: Mnemo/.venv/Scripts/python.exe -m pytest tests/ -q
"""
from fastapi.testclient import TestClient
from backend.app import app

c = TestClient(app)

def test_locations():
    r = c.get("/api/locations")
    assert r.status_code == 200
    ids = {l["id"] for l in r.json()}
    assert {"mall", "stadium", "station", "office", "residential"} <= ids

def test_current_success():
    r = c.get("/api/current-status", params={"location": "mall"})
    assert r.status_code == 200
    b = r.json()
    assert 0 <= b["available"] <= b["capacity"]
    assert b["congestion_label"] in ("Low", "Moderate", "High", "Severe")

def test_unknown_location_404():
    for ep in ("/api/current-status", "/api/prediction", "/api/history", "/api/explain"):
        r = c.get(ep, params={"location": "atlantis"})
        assert r.status_code == 404, ep
        assert "detail" in r.json()

def test_prediction_shape():
    r = c.get("/api/prediction", params={"location": "stadium"})
    assert r.status_code == 200
    b = r.json()
    assert [p["horizon_min"] for p in b["predictions"]] == [15, 30, 45, 60]
    for p in b["predictions"]:
        assert p["lo"] <= p["available"] <= p["hi"]

def test_history_clamped():
    assert c.get("/api/history", params={"location": "mall", "points": 0}).status_code == 422
    assert c.get("/api/history", params={"location": "mall", "points": 301}).status_code == 422

def test_step_advances_time():
    t0 = c.get("/api/health").json()["now"]
    assert c.post("/api/step", params={"steps": 2}).status_code == 200
    t1 = c.get("/api/health").json()["now"]
    assert t1 > t0
    assert c.post("/api/step", params={"steps": 99}).status_code == 422

def test_recommendation_ranks_all():
    b = c.get("/api/recommendation").json()
    assert len(b["ranking"]) == 5
    assert b["ranking"][0]["pred30_available"] >= b["ranking"][-1]["pred30_available"]
    assert "Recommended parking" in b["message"]

def test_explain_factors():
    b = c.get("/api/explain", params={"location": "mall"}).json()
    assert len(b["factors"]) > 0
    assert all("feature" in f and "importance" in f for f in b["factors"])
