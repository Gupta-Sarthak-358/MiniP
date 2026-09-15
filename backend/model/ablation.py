"""Ablation over cumulative feature groups (assessor's headline request).
Which information actually helps? RF-80, same 4 walk-forward folds as evaluate.py.
Run: Mnemo/.venv/Scripts/python.exe -m backend.model.ablation  (~10 min)
"""
import os, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from backend.model import cvutils as C

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIG = os.path.join(BASE, "docs", "figures")
MODEL_DIR = os.path.join(BASE, "models")

CONFIGS = [
    ("time", ["time"]),
    ("+state", ["time", "state"]),
    ("+weather", ["time", "state", "weather"]),
    ("+event", ["time", "state", "weather", "event"]),
    ("+sale/hol", ["time", "state", "weather", "event", "sale_holiday"]),
    ("+incident (full)", ["time", "state", "weather", "event", "sale_holiday", "incident"]),
]
TARGETS = [("available_30", "available"), ("vehicles_30", "vehicles"), ("available_60", "available")]

def main():
    df = C.load_df()
    origins = C.make_origins(df, 4, 5)
    res = {name: {t: [] for t, _ in TARGETS} for name, _ in CONFIGS}
    for fi, (_, ts, te_) in enumerate(origins):
        tr, te = C.split_fold(df, ts, te_)
        print(f"fold {fi+1}/4: train {len(tr)} test {len(te)}")
        for name, groups in CONFIGS:
            cols = [f for g in groups for f in C.GROUPS[g]]
            Xtr, Xte = C.fill_train_only(tr, te, cols)
            for tcol, prefix in TARGETS:
                m = RandomForestRegressor(n_estimators=80, min_samples_leaf=2,
                                          n_jobs=-1, random_state=42).fit(Xtr, tr[tcol].values)
                p = m.predict(Xte)
                res[name][tcol].append(C.mae(te[tcol].values, p))
    out = {name: {t: round(float(np.mean(v)), 3) for t, v in d.items()} for name, d in res.items()}
    # deltas vs time-only
    for name in out:
        for t, _ in TARGETS:
            base = out["time"][t]
            out[name][t + "_delta"] = round(out[name][t] - base, 3)
    json.dump(out, open(os.path.join(MODEL_DIR, "ablation.json"), "w"), indent=2)

    names = [n for n, _ in CONFIGS]
    x = np.arange(len(names))
    plt.figure(figsize=(10, 5))
    for i, (t, prefix) in enumerate(TARGETS):
        ys = [out[n][t] for n in names]
        plt.bar(x + (i - 1) * 0.25, ys, 0.25, label=t)
    plt.xticks(x, names, rotation=12); plt.ylabel("Walk-forward MAE (RF-80)")
    plt.title("Ablation: which information actually helps?"); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "ablation_mae.png"), dpi=120)
    print(json.dumps(out, indent=2))
    print("saved ablation.json, ablation_mae.png")

if __name__ == "__main__":
    main()
