"""Load trained models, predict 15/30/45/60 + explanation.
Uncertainty: conformal intervals from walk-forward validation residuals (D07,
models/conformal.json); Gaussian tree-std only as fallback when uncalibrated.
"""
import os, json
import numpy as np
import joblib

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE, "models")

_avail = None; _veh = None; _meta = None; _metrics = None; _conf = None
_ZIPS = ("models_rf_avail.zip", "models_rf_veh.zip", "models_rest.zip")

def _load_bin(name):
    """Load a model binary: raw file first, else transparently from shipped zips
    (repo tracks *.zip because GitHub blocks the raw >100MB pickles)."""
    p = os.path.join(MODEL_DIR, name)
    if os.path.exists(p):
        return joblib.load(p)
    import zipfile
    for zn in _ZIPS:
        zp = os.path.join(MODEL_DIR, zn)
        if os.path.exists(zp):
            try:
                with zipfile.ZipFile(zp) as zh:
                    if name in zh.namelist():
                        with zh.open(name) as f:
                            return joblib.load(f)
            except Exception:
                continue
    raise FileNotFoundError(f"{name} missing (looked in {MODEL_DIR} + zips). "
                            "Run backend/model/train.py or models/unpack.py.")

def load():
    global _avail, _veh, _meta, _metrics, _conf
    if _avail is None:
        _avail = _load_bin("model_avail.pkl")
        _veh = _load_bin("model_veh.pkl")
        _meta = json.load(open(os.path.join(MODEL_DIR, "meta.json")))
        try:
            _metrics = json.load(open(os.path.join(MODEL_DIR, "metrics.json")))
        except Exception:
            _metrics = {}
        try:
            _conf = json.load(open(os.path.join(MODEL_DIR, "conformal.json")))
        except Exception:
            _conf = {}
    return _avail, _veh, _meta, _metrics

def conformal_info():
    load()
    return _conf or {}

def features():
    return load()[2]["features"]

def cong_from_veh_avail(vehicles, speed, occ_pct):
    return float(np.clip(vehicles / 10.0 + (60 - speed) * 1.8 + occ_pct * 0.35, 0, 100))

def cong_label(c):
    if c < 25: return "Low"
    if c < 50: return "Moderate"
    if c < 70: return "High"
    return "Severe"

def predict_row(feat: dict):
    avail_m, veh_m, meta, metrics = load()
    F = meta["features"]
    x = np.array([[float(feat.get(k, 0)) for k in F]])
    pa = avail_m.predict(x)[0]  # 4 values
    pv = veh_m.predict(x)[0]
    # uncertainty: std across trees (average over 4 outputs -> per-horizon approx via per-estimator)
    try:
        all_a = np.array([t.predict(x)[0] for t in avail_m.estimators_])  # (n_est, 4) for RF? actually list per output
    except Exception:
        all_a = None
    # RandomForest multi-output estimators_ shape is (n_est, n_out); handle both
    if all_a is not None:
        try:
            std_a = all_a.std(axis=0)
            if np.ndim(std_a) == 0:
                std_a = np.full(4, float(std_a))
        except Exception:
            std_a = np.full(4, 12.0)
    else:
        std_a = np.full(4, 12.0)
    std_a = np.clip(std_a, 4, 40)
    cap = float(feat.get("capacity", 500))
    conf = conformal_info()
    out = []
    for i, h in enumerate([15, 30, 45, 60]):
        a = float(np.clip(pa[i], 0, cap))
        v = float(max(0, pv[i]))
        # congestion proxy: blend model-free formula with current speed decay
        occ_pct = (cap - a) / cap * 100 if cap else 0
        c = cong_from_veh_avail(v, float(feat.get("avg_speed", 30)), occ_pct)
        q = (conf.get(str(h), {}) or {}).get("q90")
        if q is None:  # fallback: uncalibrated Gaussian tree-std (documented as such)
            q = float(1.96 * float(std_a[i]))
            method = "tree-std (uncalibrated)"
        else:
            method = "conformal-q90 (walk-forward calibrated)"
        out.append({"horizon_min": h, "available": float(round(a, 1)),
                    "vehicles": float(round(v, 1)), "congestion": float(round(c, 1)),
                    "congestion_label": cong_label(c),
                    "lo": float(round(max(0, a - float(q)), 1)),
                    "hi": float(round(min(cap, a + float(q)), 1)),
                    "interval": method})
    return out

def explain(feat: dict, top_k=6):
    _, _, meta, metrics = load()
    fim = metrics.get("feature_importance", [])
    # scale bar by importance, boost context features present
    vals = []
    for name, imp in fim[:top_k]:
        v = float(feat.get(name, 0))
        vals.append({"feature": name, "importance": round(float(imp), 4), "value": v})
    return vals
