"""Conditional-slice analysis: WHERE does context help?
Global MAE averages away rare events. Compare final RF vs persistence on slices:
all / event-day / incident / sale-day / peak-hour rows of the held-out tail.
Run: Mnemo/.venv/Scripts/python.exe -m backend.model.slice_analysis
"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIG = os.path.join(BASE, "docs", "figures")
MODEL_DIR = os.path.join(BASE, "models")

def mae(a, b):
    return float(np.mean(np.abs(np.asarray(a, float) - np.asarray(b, float))))

def main():
    meta = json.load(open(os.path.join(MODEL_DIR, "meta.json")))
    F = meta["features"]
    rf = joblib.load(os.path.join(MODEL_DIR, "model_avail.pkl"))
    df = pd.read_csv(os.path.join(BASE, "data", "historical.csv"),
                     parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    df = df[(df["occupied"] >= 0) & (df["occupied"] <= df["capacity"])]
    n = len(df); cut = int(n * 0.8)
    tr, te = df.iloc[:cut], df.iloc[cut:].copy()
    med = tr[F].median(numeric_only=True)
    Xte = te[F].fillna(med).values
    te = te.copy()
    te["rf30"] = rf.predict(Xte)[:, 1]
    slices = {
        "all": te.index,
        "event-day": te.index[te["is_event_day"] == 1],
        "incident": te.index[te["is_incident"] == 1],
        "sale-day": te.index[te["is_sale_day"] == 1],
        "peak-hour": te.index[te["is_peak_hour"] == 1],
    }
    out = {}
    for name, idx in slices.items():
        s = te.loc[idx]
        out[name] = {"n": len(s),
                     "rf_MAE": round(mae(s["available_30"], s["rf30"]), 3) if len(s) else None,
                     "persist_MAE": round(mae(s["available_30"], s["available"]), 3) if len(s) else None}
        if out[name]["rf_MAE"] is not None:
            out[name]["rf_skill_vs_persist"] = round(1 - out[name]["rf_MAE"] / out[name]["persist_MAE"], 4)
    json.dump(out, open(os.path.join(MODEL_DIR, "slice_analysis.json"), "w"), indent=2)
    names = [k for k in slices if out[k]["n"]]
    x = np.arange(len(names))
    plt.figure(figsize=(9, 4.5))
    plt.bar(x - 0.2, [out[k]["persist_MAE"] for k in names], 0.4, label="Persistence")
    plt.bar(x + 0.2, [out[k]["rf_MAE"] for k in names], 0.4, label="RF-full")
    plt.xticks(x, [f"{k}\n(n={out[k]['n']})" for k in names])
    plt.ylabel("MAE @30min (slots)"); plt.title("Context pays off exactly when conditions are abnormal")
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "conditional_mae.png"), dpi=120)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
