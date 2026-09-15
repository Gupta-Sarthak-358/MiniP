import json
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.simulator.live_data import SIM, LOCATIONS
from backend.model import predict as P
from backend.monitor import drift as DRIFT
from backend.simulator.real_replay import REPLAY, META as REAL_META
from pydantic import BaseModel

class IncidentIn(BaseModel):
    location: str = "station"
    kind: str = "accident"
    severity: int = 2
    dur_steps: int = 4

app = FastAPI(title="Real-Time Traffic & Parking Predictor")
# DEMO ONLY: open CORS lets the file:// dashboard and any origin call the API.
# For deployment, restrict to the served frontend origin.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONT = os.path.join(BASE, "frontend")

def need_location(location: str) -> str:
    if location not in LOCATIONS:
        raise HTTPException(status_code=404, detail=f"unknown location '{location}'. See /api/locations.")
    return location

def cong_label(c):
    if c < 25: return "Low"
    if c < 50: return "Moderate"
    if c < 70: return "High"
    return "Severe"

@app.get("/")
def index():
    return FileResponse(os.path.join(FRONT, "index.html"))

@app.get("/api/locations")
def locations():
    return [{"id": k, "label": v["label"], "capacity": v["capacity"]} for k, v in LOCATIONS.items()]

@app.get("/api/health")
def health():
    return {"ok": True, "now": SIM.now.isoformat(), "locations": len(LOCATIONS)}

@app.get("/api/current-status")
def current(location: str = "mall"):
    need_location(location)
    c = SIM.current(location)
    return {**c, "congestion_label": cong_label(c["congestion"]),
            "last_updated": SIM.now.isoformat()}

@app.get("/api/prediction")
def prediction(location: str = "mall"):
    need_location(location)
    cur = SIM.current(location)
    try:
        preds = P.predict_row(cur)
    except Exception as e:
        # model not trained yet -> naive fallback
        preds = [{"horizon_min": h, "available": cur["available"], "vehicles": cur["vehicle_count"],
                  "congestion": cur["congestion"], "congestion_label": cong_label(cur["congestion"]),
                  "lo": max(0, cur["available"] - 15), "hi": min(cur["capacity"], cur["available"] + 15),
                  "fallback": True, "error": str(e)} for h in [15, 30, 45, 60]]
    # critical window: first horizon where occupancy > 90%
    crit = None
    for p in preds:
        if (cur["capacity"] - p["available"]) / cur["capacity"] > 0.90:
            crit = p["horizon_min"]; break
    return {"location": location, "now": cur, "predictions": preds,
            "critical_in_min": crit, "last_updated": SIM.now.isoformat(),
            "interval_method": preds[0].get("interval", "unknown") if preds else "unknown",
            "calibration": P.conformal_info()}

@app.get("/api/history")
def history(location: str = "mall", points: int = Query(40, ge=1, le=300)):
    need_location(location)
    return SIM.history(location, points)

@app.get("/api/events")
def events():
    return SIM.events

@app.get("/api/explain")
def explain(location: str = "mall"):
    need_location(location)
    cur = SIM.current(location)
    try:
        return {"factors": P.explain(cur)}
    except Exception as e:
        return {"factors": [], "error": str(e)}

@app.get("/api/recommendation")
def recommendation():
    # rank locations by predicted available in 30min
    rows = []
    for loc in LOCATIONS:
        cur = SIM.current(loc)
        try:
            pr = P.predict_row(cur)[1]  # 30min
            avail30 = pr["available"]
        except Exception:
            avail30 = cur["available"]
        rows.append({"location": loc, "label": LOCATIONS[loc]["label"],
                     "now_available": cur["available"], "pred30_available": round(float(avail30), 1),
                     "congestion": cur["congestion"], "congestion_label": cong_label(cur["congestion"])})
    rows.sort(key=lambda r: -r["pred30_available"])
    best = rows[0]
    warn = [r for r in rows if (LOCATIONS[r["location"]]["capacity"] - r["pred30_available"]) / LOCATIONS[r["location"]]["capacity"] > 0.85]
    return {"ranking": rows, "recommended": best,
            "message": f"Recommended parking: {best['label']} ({best['pred30_available']} slots expected in 30 min).",
            "warnings": [f"{r['label']} expected critical in ~30 min" for r in warn]}

@app.post("/api/step")
def step(steps: int = Query(1, ge=1, le=8)):
    # monitored-serving loop (D08): per sub-step, forecast -> advance -> pair -> tick,
    # so every ground-truth step is paired with the forecast made 2 steps earlier.
    for _ in range(steps):
        try:
            for loc in LOCATIONS:
                DRIFT.note_prediction(loc, P.predict_row(SIM.current(loc))[1]["available"])
        except Exception:
            pass
        SIM.step(1)
        REPLAY.tick(1)
        DRIFT.tick()
        for loc in LOCATIONS:
            try:
                DRIFT.note_actual(loc, SIM.current(loc)["available"])
            except Exception:
                pass
    return {"ok": True, "now": SIM.now.isoformat(), "drift": DRIFT.status()}

@app.post("/api/incident")
def inject(inc: IncidentIn):
    need_location(inc.location)
    if inc.kind not in ("accident", "closure", "storm_shock"):
        raise HTTPException(status_code=422, detail="kind must be accident|closure|storm_shock")
    ok = SIM.inject_incident(inc.location, inc.kind, inc.severity, inc.dur_steps)
    return {"ok": ok, "incident": inc.model_dump(), "now": SIM.now.isoformat()}

@app.get("/api/real-zone")
def real_zone():
    """Birmingham NCP replay through the same contract (D14). ML validation: E06."""
    return {"meta": REAL_META, "now": REPLAY.current(),
            "forecast": REPLAY.forecast(), "last_updated": SIM.now.isoformat()}

_METRICS_CACHE = {}

def _load_json(name):
    if name not in _METRICS_CACHE:
        try:
            with open(os.path.join(BASE, "models", name)) as f:
                _METRICS_CACHE[name] = json.load(f)
        except Exception:
            _METRICS_CACHE[name] = {}
    return _METRICS_CACHE[name]

@app.get("/api/metrics")
def metrics():
    """Real walk-forward numbers for the UI (MAE chips, calibration footer)."""
    ev = _load_json("eval_walkforward.json")
    conf = _load_json("conformal.json")
    real = _load_json("real_eval.json")
    get = lambda *ks: ev.get(ks[0], {}).get(ks[1], {}) if len(ks) == 2 else {}
    return {
        "veh_mae30": get("rf_veh", "vehicles_30").get("MAE"),
        "veh_skill30": get("rf_veh", "vehicles_30").get("skill_vs_persist"),
        "avail_mae30": get("rf_av", "available_30").get("MAE"),
        "avail_skill30": get("rf_av", "available_30").get("skill_vs_persist"),
        "coverage30": (conf.get("30") or {}).get("empirical_coverage"),
        "real_skill30": (real.get("rf") or {}).get("skill30"),
    }

@app.get("/api/drift")
def drift_status():
    return DRIFT.status()

@app.post("/api/drift/reset")
def drift_reset(location: str = "mall"):
    DRIFT.reset(None if location == "all" else location)
    return {"ok": True}

if os.path.isdir(FRONT):
    app.mount("/static", StaticFiles(directory=FRONT), name="static")
