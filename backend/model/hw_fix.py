"""Recompute ONLY the Holt-Winters block of evaluate.py (damped-trend fix, E02a)
and patch models/eval_walkforward.json + figures. Reuses identical folds.
Run: Mnemo/.venv/Scripts/python.exe -m backend.model.hw_fix
"""
import os, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from backend.model import cvutils as C
from backend.model.evaluate import ses_forecast

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIG = os.path.join(BASE, "docs", "figures")
MODEL_DIR = os.path.join(BASE, "models")
LOCS = ["mall", "stadium", "station", "office", "residential"]

def main():
    df = C.load_df()
    origins = C.make_origins(df, 4, 5)
    errs = {h: [] for h in C.HORIZONS}
    for fi, (_, ts, te_) in enumerate(origins):
        tr, te = C.split_fold(df, ts, te_)
        print(f"fold {fi+1}: train {len(tr)} test {len(te)}")
        for loc in LOCS:
            trl = tr[tr.location == loc].sort_values("timestamp").reset_index(drop=True)
            tel = te[te.location == loc].sort_values("timestamp").reset_index(drop=True)
            fc = ses_forecast(trl, len(tel), cap={"mall": 1000, "stadium": 800, "station": 500, "office": 600, "residential": 400}[loc])
            if fc is None:
                fc = tel["available"].values + 0  # persistence fallback
                for h in C.HORIZONS:
                    errs[h].extend(list(np.abs(tel[f"available_{h}"].values - fc)))
            else:
                # align: F[j] = tr_max + (j+1)*15min; want T_k + h, T_k = te_min + 15k
                gap = int(round((tel["timestamp"].min() - trl["timestamp"].max()).total_seconds() / 900))
                for h in C.HORIZONS:
                    s = h // 15
                    idx = np.arange(len(tel)) + s + gap - 1
                    idx = np.clip(idx, 0, len(fc) - 1)
                    p = fc[idx]
                    errs[h].extend(list(np.abs(tel[f"available_{h}"].values - p)))
    hw = {f"available_{h}": {"MAE": round(float(np.mean(errs[h])), 3),
                             "RMSE": round(float(np.sqrt(np.mean(np.square(errs[h])))), 3)}
          for h in C.HORIZONS}
    ref = json.load(open(os.path.join(MODEL_DIR, "eval_walkforward.json")))
    hw["available_30"]["skill_vs_persist"] = round(
        C.skill(hw["available_30"]["MAE"], ref["persistence_av"]["available_30"]["MAE"]), 4)
    ref["hw_av"] = hw
    json.dump(ref, open(os.path.join(MODEL_DIR, "eval_walkforward.json"), "w"), indent=2)
    print(json.dumps(hw, indent=2))
    # refresh figures
    labels = {"persistence_av": "Persistence", "ha_av": "HistAvg", "seasonal_av": "SeasNaive",
              "ar24_av": "AR(24)", "hw_av": "ExpSmooth", "lr_av": "Linear", "rf_av": "RF-100"}
    plt.figure(figsize=(9, 5))
    for m in ["persistence_av", "ha_av", "seasonal_av", "ar24_av", "hw_av", "lr_av", "rf_av"]:
        ys = [ref[m][f"available_{h}"]["MAE"] for h in C.HORIZONS]
        plt.plot(C.HORIZONS, ys, marker="o", label=labels[m])
    if "xgb_av30" in ref:
        plt.scatter([30], [ref["xgb_av30"]["available_30"]["MAE"]], s=80, label="XGB-300", zorder=5)
    plt.xlabel("Horizon (min)"); plt.ylabel("MAE (slots)")
    plt.title("Walk-forward MAE vs horizon (available slots)")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "eval_horizons.png"), dpi=120)
    plt.figure(figsize=(9, 4))
    names = ["ha_av", "seasonal_av", "ar24_av", "hw_av", "lr_av", "rf_av"]
    vals = [ref[m]["available_30"].get("skill_vs_persist", 0) for m in names]
    plt.bar([labels[m] for m in names], vals)
    plt.axhline(0, color="k"); plt.ylabel("Skill vs persistence @30min")
    plt.title("Who beats 'nothing changes'? (skill > 0)"); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "baselines_skill.png"), dpi=120)
    print("patched eval_walkforward.json + figures")

if __name__ == "__main__":
    main()
