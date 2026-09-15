"""Training-serving parity: live simulator features must cover every model feature.
Catches the classic skewed-pipeline bug where train and serve disagree on semantics.
"""
import json, os

def test_feature_parity():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    meta = json.load(open(os.path.join(base, "models", "meta.json")))
    from backend.simulator.live_data import SIM
    cur = SIM.current("mall")
    missing = [f for f in meta["features"] if f not in cur]
    assert not missing, f"serve missing features used in training: {missing}"
    # spot-check encoding domains match generator
    assert cur["weather_enc"] in (0, 1, 2, 3, 4)
    assert cur["event_type_enc"] in (0, 1, 2, 3, 4)

def test_predict_row_contract():
    from backend.simulator.live_data import SIM
    from backend.model.predict import predict_row
    for loc in ("mall", "stadium", "station", "office", "residential"):
        preds = predict_row(SIM.current(loc))
        assert [p["horizon_min"] for p in preds] == [15, 30, 45, 60]
        assert all(isinstance(p["available"], (int, float)) and not isinstance(p["available"], bool) for p in preds)  # JSON-safe scalars, slots are ints
        assert all(float(p["available"]).is_integer() for p in preds)  # no fractional parking slots
