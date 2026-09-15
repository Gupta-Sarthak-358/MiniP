"""Walk-forward evaluation (D04/D05): expanding origins, train-only stats, purging,
naive + classical + ML models, per-horizon MAE/RMSE/skill, conformal calibration (D07).
Run: Mnemo/.venv/Scripts/python.exe backend/model/evaluate.py  (~10-15 min)
"""
import os, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from backend.model import cvutils as C

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIG = os.path.join(BASE, "docs", "figures")
MODEL_DIR = os.path.join(BASE, "models")
LOCS = ["mall", "stadium", "station", "office", "residential"]
LOCS_CAP = {"mall": 1000, "stadium": 800, "station": 500, "office": 600, "residential": 400}
STEP = 15

def fit_ar24(series, lags=24):
    y = np.asarray(series, float)
    X = np.column_stack([y[lags - k - 1: len(y) - k - 1] for k in range(lags)])
    X = np.column_stack([np.ones(len(X)), X])
    return X

def ar_predict(tr_loc, te_loc, col, horizons, lags=24):
    """Direct AR(lags) per horizon via OLS. Returns {h: preds}."""
    ytr = tr_loc[col].values
    Xtr = fit_ar24(ytr, lags)
    out = {}
    full = np.concatenate([ytr, te_loc[col].values])
    ntr = len(ytr)
    for h in C.HORIZONS:
        s = h // STEP
        yt = ytr[lags + s:] if s else ytr[lags:]
        Xt = Xtr[: len(yt)]
        beta, *_ = np.linalg.lstsq(Xt, yt, rcond=None)
        preds = []
        for k in range(len(te_loc)):
            win = full[ntr + k - lags: ntr + k]
            if len(win) < lags:
                win = np.concatenate([np.full(lags - len(win), win[0]), win])
            preds.append(beta[0] + win[::-1] @ beta[1:])
        out[h] = np.array(preds)
    return out

def ses_forecast(tr_loc, n_test, col="available", cap=None):
    """Classical exponential-smoothing reference (level-only SES).
    E02a lesson: full seasonal Holt-Winters is mis-specified here — the series is
    event-driven with clipped boundaries, so seasonal MLE overfits noise and the
    trend extrapolates through the boundary (MAE 100+). SES = adaptive persistence:
    honest, robust, and the right classical comparator for inertia-dominated data."""
    from statsmodels.tsa.holtwinters import SimpleExpSmoothing
    try:
        fit = SimpleExpSmoothing(tr_loc[col].values).fit(optimized=True)
        fc = np.asarray(fit.forecast(n_test + 8), float)
        return np.clip(fc, 0, cap) if cap is not None else fc
    except Exception:
        return None

def run(n_folds=4, test_days=5):
    os.makedirs(FIG, exist_ok=True)
    df = C.load_df()
    origins = C.make_origins(df, n_folds, test_days)
    try:
        import torch
        use_cuda = torch.cuda.is_available()
    except Exception:
        use_cuda = False

    agg = {}   # model -> target -> h -> [mae list]
    resid = {h: [] for h in C.HORIZONS}  # RF avail residuals for conformal
    actuals = {h: [] for h in C.HORIZONS}

    for fi, (tr_end, ts, te_) in enumerate(origins):
        print(f"--- fold {fi+1}/{n_folds}: test {ts.date()}..{te_.date()} ---")
        tr, te = C.split_fold(df, ts, te_)
        print(f"  train {len(tr)} test {len(te)} (purged)")
        Xtr, Xte = C.fill_train_only(tr, te, C.ALL_FEATURES)
        past = df[df["timestamp"] < ts]  # leak-free history for seasonal-naive

        preds = {}
        preds["persistence_av"] = C.pred_persistence(te, "available")
        preds["persistence_veh"] = C.pred_persistence(te, "vehicle_count")
        preds["seasonal_av"] = C.pred_seasonal_naive(past, te, "available")
        preds["ha_av"] = C.pred_ha(tr, te, "available")
        preds["ha_veh"] = C.pred_ha(tr, te, "vehicles")

        # AR(24) per location
        ar_av = {h: np.zeros(len(te)) for h in C.HORIZONS}
        ar_vh = {h: np.zeros(len(te)) for h in C.HORIZONS}
        pos = {idx: k for k, idx in enumerate(te.index.values)}
        for loc in LOCS:
            trl = tr[tr.location == loc].sort_values("timestamp")
            tel = te[te.location == loc].sort_values("timestamp")
            pa = ar_predict(trl, tel, "available", C.HORIZONS)
            pv = ar_predict(trl, tel, "vehicle_count", C.HORIZONS)
            for k, idx in enumerate(tel.index.values):
                for h in C.HORIZONS:
                    ar_av[h][pos[idx]] = pa[h][k]
                    ar_vh[h][pos[idx]] = pv[h][k]
        preds["ar24_av"] = ar_av
        preds["ar24_veh"] = ar_vh

        # SES classical reference (see ses_forecast docstring for why not full HW)
        hw_av = {}
        for loc in LOCS:
            trl = tr[tr.location == loc].sort_values("timestamp").reset_index(drop=True)
            tel = te[te.location == loc].sort_values("timestamp").reset_index(drop=True)
            cap = LOCS_CAP[loc]
            fc = ses_forecast(trl, len(tel), cap=cap)
            if fc is None:
                hw_av[loc] = None
            else:
                # align: F[j] = tr_max + (j+1)*15min (purge gap); want T_k + h
                gap = int(round((tel["timestamp"].min() - trl["timestamp"].max()).total_seconds() / 900))
                hw_av[loc] = {h: fc[np.clip(np.arange(len(tel)) + h // STEP + gap - 1, 0, len(fc) - 1)] for h in C.HORIZONS}
        hw_full = {h: np.zeros(len(te)) for h in C.HORIZONS}
        for loc in LOCS:
            m = (te.location == loc).values
            if hw_av[loc] is None:
                for h in C.HORIZONS:
                    hw_full[h][m] = te.loc[te.location == loc, "available"].values
            else:
                for h in C.HORIZONS:
                    hw_full[h][m] = hw_av[loc][h]
        preds["hw_av"] = hw_full

        # ML models
        lr_a = LinearRegression().fit(Xtr, tr[[f"available_{h}" for h in C.HORIZONS]].values)
        rf_a = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, n_jobs=-1,
                                     random_state=42).fit(Xtr, tr[[f"available_{h}" for h in C.HORIZONS]].values)
        lr_v = LinearRegression().fit(Xtr, tr[[f"vehicles_{h}" for h in C.HORIZONS]].values)
        rf_v = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, n_jobs=-1,
                                     random_state=42).fit(Xtr, tr[[f"vehicles_{h}" for h in C.HORIZONS]].values)
        pa_rf = rf_a.predict(Xte); pv_rf = rf_v.predict(Xte)
        pa_lr = lr_a.predict(Xte); pv_lr = lr_v.predict(Xte)
        preds["rf_av"] = {h: pa_rf[:, i] for i, h in enumerate(C.HORIZONS)}
        preds["rf_veh"] = {h: pv_rf[:, i] for i, h in enumerate(C.HORIZONS)}
        preds["lr_av"] = {h: pa_lr[:, i] for i, h in enumerate(C.HORIZONS)}

        try:
            from xgboost import XGBRegressor
            xa = XGBRegressor(n_estimators=300, max_depth=7, learning_rate=0.05,
                              subsample=0.9, colsample_bytree=0.9, tree_method="hist",
                              device="cuda" if use_cuda else "cpu", random_state=42)
            xa.fit(Xtr, tr["available_30"].values)
            preds["xgb_av30"] = {30: xa.predict(Xte)}
        except Exception as e:
            print("  XGB skipped:", str(e)[:100])

        # score + collect residuals
        ycol_of = {"persistence_av": "available", "seasonal_av": "available",
                   "ha_av": "available", "ar24_av": "available", "hw_av": "available",
                   "lr_av": "available", "rf_av": "available", "xgb_av30": "available",
                   "persistence_veh": "vehicles", "ha_veh": "vehicles",
                   "ar24_veh": "vehicles", "rf_veh": "vehicles"}
        for name, d in preds.items():
            prefix = ycol_of[name]
            for h, p in d.items():
                ycol = f"available_{h}" if prefix == "available" else f"vehicles_{h}"
                y = te[ycol].values
                key = (name, ycol)
                agg.setdefault(key, []).append((C.mae(y, p), C.rmse(y, p)))
                if name == "rf_av":
                    resid[h].extend(list(np.asarray(y, float) - np.asarray(p, float)))
                    actuals[h].extend(list(np.asarray(y, float)))

    # aggregate
    table = {}
    for (name, ycol), lst in sorted(agg.items()):
        ms = np.mean([a for a, _ in lst]); rs = np.mean([b for _, b in lst])
        table.setdefault(name, {})[ycol] = {"MAE": round(float(ms), 3), "RMSE": round(float(rs), 3)}
    # skill vs persistence @30
    for tgt, pm in (("available_30", "persistence_av"), ("vehicles_30", "persistence_veh")):
        ref = table[pm][tgt]["MAE"]
        for name in table:
            if tgt in table[name]:
                table[name][tgt]["skill_vs_persist"] = round(C.skill(table[name][tgt]["MAE"], ref), 4)
    json.dump(table, open(os.path.join(MODEL_DIR, "eval_walkforward.json"), "w"), indent=2)

    # conformal calibration (D07): quantiles of RF walk-forward residuals
    conf = {}
    for h in C.HORIZONS:
        r = np.abs(np.array(resid[h], float))
        q90 = float(np.quantile(r, 0.90))
        cov = float(np.mean(r <= q90))
        conf[str(h)] = {"q90": round(q90, 2), "empirical_coverage": round(cov, 4), "n": len(r)}
    json.dump(conf, open(os.path.join(MODEL_DIR, "conformal.json"), "w"), indent=2)

    # ---- figures ----
    models_av = ["persistence_av", "ha_av", "seasonal_av", "ar24_av", "hw_av", "lr_av", "rf_av"]
    labels = {"persistence_av": "Persistence", "ha_av": "HistAvg", "seasonal_av": "SeasNaive",
              "ar24_av": "AR(24)", "hw_av": "ExpSmooth", "lr_av": "Linear", "rf_av": "RF-100"}
    plt.figure(figsize=(9, 5))
    for m in models_av:
        ys = [table[m][f"available_{h}"]["MAE"] for h in C.HORIZONS]
        plt.plot(C.HORIZONS, ys, marker="o", label=labels[m])
    if "xgb_av30" in table:
        plt.scatter([30], [table["xgb_av30"]["available_30"]["MAE"]], s=80, label="XGB-300", zorder=5)
    plt.xlabel("Horizon (min)"); plt.ylabel("MAE (slots)"); plt.title("Walk-forward MAE vs horizon (available slots)")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "eval_horizons.png"), dpi=120)

    plt.figure(figsize=(9, 4))
    names = ["ha_av", "seasonal_av", "ar24_av", "hw_av", "lr_av", "rf_av"]
    vals = [table[m]["available_30"].get("skill_vs_persist", 0) for m in names]
    plt.bar([labels[m] for m in names], vals)
    plt.axhline(0, color="k"); plt.ylabel("Skill vs persistence @30min")
    plt.title("Who beats 'nothing changes'? (skill > 0)"); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "baselines_skill.png"), dpi=120)

    print(json.dumps(table, indent=2))
    print("conformal:", json.dumps(conf, indent=2))
    print("saved eval_walkforward.json, conformal.json, eval_horizons.png, baselines_skill.png")

if __name__ == "__main__":
    run()
