"""Train + evaluate: LinearRegression (baseline), RandomForest multi-output (main),
XGBoost-GPU (advanced, uses Mnemo .venv + CUDA when available), HGB fallback. Time-split, no shuffle."""
import os, json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(BASE, "data", "historical.csv")
MODEL_DIR = os.path.join(BASE, "models")

FEATURES = ["hour","day_of_week","is_weekend","is_peak_hour","is_night",
    "is_holiday","is_sale_day","sale_intensity","is_event_day",
    "event_type_enc","event_size_enc","event_impact","hours_to_event",
    "hours_since_event","is_event_active","is_incident","incident_severity",
    "weather_enc","temperature",
    "vehicle_count","avg_speed","occupied","available","occupancy_pct",
    "location_enc","capacity"]
Y_AVAIL = ["available_15","available_30","available_45","available_60"]
Y_VEH = ["vehicles_15","vehicles_30","vehicles_45","vehicles_60"]
Y_CONG = ["congestion_15","congestion_30","congestion_45","congestion_60"]

def metrics(y, p):
    return {"MAE": float(mean_absolute_error(y, p)),
            "RMSE": float(mean_squared_error(y, p) ** 0.5),
            "R2": float(r2_score(y, p))}

def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    df = pd.read_csv(CSV)
    df = df.sort_values("timestamp").reset_index(drop=True)
    # validation: 0<=occupied<=capacity etc.
    df = df[(df["occupied"] >= 0) & (df["occupied"] <= df["capacity"])]
    n = len(df); cut = int(n * 0.8)
    tr, te = df.iloc[:cut], df.iloc[cut:]
    # D04: imputers fit on TRAIN ONLY (no test statistics leak into training)
    med = tr[FEATURES].median(numeric_only=True)
    tr = tr.copy(); te = te.copy()
    tr[FEATURES] = tr[FEATURES].fillna(med)
    te[FEATURES] = te[FEATURES].fillna(med)
    Xtr, Xte = tr[FEATURES].values, te[FEATURES].values

    out = {}
    # --- available models ---
    lr_a = LinearRegression().fit(Xtr, tr[Y_AVAIL].values)
    rf_a = RandomForestRegressor(n_estimators=150, max_depth=None, min_samples_leaf=2,
                                 n_jobs=-1, random_state=42).fit(Xtr, tr[Y_AVAIL].values)
    try:
        from xgboost import XGBRegressor
        try:
            import torch
            use_cuda = torch.cuda.is_available()
        except Exception:
            use_cuda = False
        xgb_kwargs = dict(n_estimators=500, max_depth=7, learning_rate=0.05,
                          subsample=0.9, colsample_bytree=0.9, n_jobs=-1,
                          random_state=42, tree_method="hist",
                          device="cuda" if use_cuda else "cpu")
        print(f"XGBoost device: {xgb_kwargs['device']} (cuda_available={use_cuda})")
        xgb_a = XGBRegressor(**xgb_kwargs)
        # XGB single-output: train on 30min for comparison
        xgb_a.fit(Xtr, tr[["available_30"]].values)
        pa_xgb = xgb_a.predict(Xte)
        out["XGB_avail30"] = metrics(te[["available_30"]].values, pa_xgb.reshape(-1, 1))
        out["XGB_device"] = xgb_kwargs["device"]
        adv_name, adv_avail30 = "xgboost-" + xgb_kwargs["device"], pa_xgb
        joblib.dump(xgb_a, os.path.join(MODEL_DIR, "xgb_avail30.pkl"))
    except Exception as e:
        print("xgboost not available, using HistGradientBoosting:", e)
        hgb_a = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.08,
                                              max_depth=7, random_state=42)
        hgb_a.fit(Xtr, tr["available_30"].values)
        pa_hgb = hgb_a.predict(Xte)
        out["HGB_avail30"] = metrics(te["available_30"].values, pa_hgb)
        adv_name = "hgb"

    for name, m in [("LinearRegression", lr_a), ("RandomForest", rf_a)]:
        p = m.predict(Xte)
        # report on 30-min column (index 1)
        out[f"{name}_avail30"] = metrics(te[Y_AVAIL].values[:, 1], p[:, 1])
        out[f"{name}_avail_all"] = metrics(te[Y_AVAIL].values.ravel(), p.ravel())

    # --- vehicles models ---
    lr_v = LinearRegression().fit(Xtr, tr[Y_VEH].values)
    rf_v = RandomForestRegressor(n_estimators=150, min_samples_leaf=2,
                                 n_jobs=-1, random_state=42).fit(Xtr, tr[Y_VEH].values)
    for name, m in [("LinearRegression", lr_v), ("RandomForest", rf_v)]:
        p = m.predict(Xte)
        out[f"{name}_veh30"] = metrics(te[Y_VEH].values[:, 1], p[:, 1])

    # pick best avail30 by MAE among LR/RF (+xgb/hgb if present)
    print(json.dumps(out, indent=2))

    joblib.dump(rf_a, os.path.join(MODEL_DIR, "model_avail.pkl"))
    joblib.dump(rf_v, os.path.join(MODEL_DIR, "model_veh.pkl"))
    joblib.dump(lr_a, os.path.join(MODEL_DIR, "baseline_avail.pkl"))

    # feature importance (mean over 4 outputs)
    imp = rf_a.feature_importances_
    fim = sorted(zip(FEATURES, map(float, imp)), key=lambda x: -x[1])

    meta = {"features": FEATURES, "y_avail": Y_AVAIL, "y_veh": Y_VEH, "y_cong": Y_CONG,
            "advanced": adv_name, "train_rows": cut, "test_rows": n - cut}
    json.dump(meta, open(os.path.join(MODEL_DIR, "meta.json"), "w"), indent=2)
    json.dump({"metrics": out, "feature_importance": fim},
              open(os.path.join(MODEL_DIR, "metrics.json"), "w"), indent=2)
    print("saved models + metrics. top features:", fim[:8])

if __name__ == "__main__":
    main()
