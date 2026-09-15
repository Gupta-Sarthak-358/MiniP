"""Real-zone validation (E06, D14): Birmingham NCP Market lot (UCI id=482, UK OGL).
Cleans sensor glitches, resamples to the project 15-min grid, replays it live,
and runs walk-forward RF-vs-naive on REAL history with reduced features
(time + occupancy + lags only — real feed has no traffic/weather/events).
Run: Mnemo/.venv/Scripts/python.exe -m backend.model.real_zone
"""
import os, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from backend.model import cvutils as C

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIG = os.path.join(BASE, "docs", "figures")
MODEL_DIR = os.path.join(BASE, "models")
REAL = os.path.join(BASE, "data", "real")
LOT = "BHMBCCMKT01"  # fullest coverage (1312 readings) + highest variance (CV 0.61)
FEATS = ["hour", "day_of_week", "is_weekend", "is_peak_hour", "occupied",
         "available", "occupancy_pct", "lag1", "lag2", "lag4", "roll4"]

def build_series():
    df = pd.read_csv(os.path.join(REAL, "dataset.csv"), parse_dates=["LastUpdated"])
    s = df[df.SystemCodeNumber == LOT].sort_values("LastUpdated").copy()
    cap = int(s["Capacity"].iloc[0])
    s = s.set_index("LastUpdated")
    # sensor glitches: negative + >105% cap readings -> NaN, then interpolate
    occ = s["Occupancy"].astype(float)
    occ[(occ < 0) | (occ > cap * 1.05)] = np.nan
    occ = occ.resample("15min").mean().interpolate(limit=2)
    out = pd.DataFrame({"timestamp": occ.index, "occupied": occ.values, "capacity": cap})
    out["occupied"] = out["occupied"].clip(0, cap)
    out["available"] = out["capacity"] - out["occupied"]
    out["occupancy_pct"] = out["occupied"] / out["capacity"] * 100
    out["hour"] = out["timestamp"].dt.hour + out["timestamp"].dt.minute / 60
    out["day_of_week"] = out["timestamp"].dt.weekday
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)
    out["is_peak_hour"] = (((out["hour"] >= 8) & (out["hour"] <= 10)) |
                           ((out["hour"] >= 17) & (out["hour"] <= 20))).astype(int)
    for L in (1, 2, 4):
        out[f"lag{L}"] = out["available"].shift(L)
    out["roll4"] = out["available"].shift(1).rolling(4).mean()
    for h in C.HORIZONS:
        out[f"available_{h}"] = out["available"].shift(-h // 15)
    out = out.dropna().reset_index(drop=True)
    out.to_csv(os.path.join(REAL, "bham_replay.csv"), index=False)
    print(f"real series: {len(out)} rows, {out.timestamp.min()}..{out.timestamp.max()}, "
          f"occ {out.occupancy_pct.min():.0f}-{out.occupancy_pct.max():.0f}%")
    return out

def run_eval(df):
    origins = C.make_origins(df, 3, 7)  # 3 folds x 7 days (shorter real series)
    agg = {}
    for fi, (_, ts, te_) in enumerate(origins):
        tr, te = C.split_fold(df, ts, te_)
        print(f"fold {fi+1}/3: train {len(tr)} test {len(te)}")
        Xtr, Xte = C.fill_train_only(tr, te, FEATS)
        preds = {"persistence": {h: te["available"].values for h in C.HORIZONS}}
        # HistAvg hour x dow from train
        ha = {}
        for h in C.HORIZONS:
            m = tr.groupby(["day_of_week", "hour"])[f"available_{h}"].mean()
            idx = pd.MultiIndex.from_arrays([te["day_of_week"], te["hour"]])
            p = m.reindex(idx).values
            ha[h] = np.where(np.isnan(p), tr[f"available_{h}"].mean(), p)
        preds["histavg"] = ha
        rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=2,
                                   n_jobs=-1, random_state=42)
        rf.fit(Xtr, tr[[f"available_{h}" for h in C.HORIZONS]].values)
        pr = rf.predict(Xte)
        preds["rf"] = {h: pr[:, i] for i, h in enumerate(C.HORIZONS)}
        for name, d in preds.items():
            for h, p in d.items():
                agg.setdefault((name, h), []).append(C.mae(te[f"available_{h}"].values, p))
    table = {}
    for (name, h), lst in sorted(agg.items()):
        table.setdefault(name, {})[str(h)] = round(float(np.mean(lst)), 2)
    ref = table["persistence"]
    for name in table:
        table[name]["skill30"] = round(1 - table[name]["30"] / ref["30"], 4)
    json.dump(table, open(os.path.join(MODEL_DIR, "real_eval.json"), "w"), indent=2)
    names = ["persistence", "histavg", "rf"]
    x = np.arange(len(C.HORIZONS))
    plt.figure(figsize=(8, 4.5))
    for i, m in enumerate(names):
        plt.plot(C.HORIZONS, [table[m][str(h)] for h in C.HORIZONS], marker="o", label=m)
    plt.xlabel("Horizon (min)"); plt.ylabel("MAE (slots, REAL Birmingham lot)")
    plt.title("Sim-to-real check: same pattern on real sensors"); plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "real_validation.png"), dpi=120)
    print(json.dumps(table, indent=2))

if __name__ == "__main__":
    run_eval(build_series())
