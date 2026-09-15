"""Shared walk-forward CV utilities (D04/D05). Strict past->future, train-only stats, label purging."""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(BASE, "data", "historical.csv")
MAX_H = 60  # longest forecast horizon, minutes (for purging)

GROUPS = {
    "time": ["hour", "day_of_week", "is_weekend", "is_peak_hour", "is_night",
             "location_enc", "capacity"],
    "state": ["vehicle_count", "avg_speed", "occupied", "available", "occupancy_pct"],
    "weather": ["weather_enc", "temperature"],
    "event": ["is_event_day", "event_type_enc", "event_size_enc", "event_impact",
              "hours_to_event", "hours_since_event", "is_event_active"],
    "sale_holiday": ["is_sale_day", "sale_intensity", "is_holiday"],
    "incident": ["is_incident", "incident_severity"],
}
ALL_FEATURES = [f for g in GROUPS.values() for f in g]
HORIZONS = [15, 30, 45, 60]

def load_df():
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)

def make_origins(df, n_folds=4, test_days=5):
    """Expanding-window origins over global time. Returns [(train_end, test_start, test_end)]."""
    tmin, tmax = df["timestamp"].min(), df["timestamp"].max()
    test_len = pd.Timedelta(days=test_days)
    total_test = test_len * n_folds
    first_test_start = tmax - total_test
    out = []
    for k in range(n_folds):
        ts = first_test_start + k * test_len
        te = ts + test_len
        out.append((ts, ts, te))  # train = everything < ts (purged below)
    return out

def split_fold(df, test_start, test_end):
    te_mask = (df["timestamp"] >= test_start) & (df["timestamp"] < test_end)
    te = df[te_mask].copy()
    tr = df[df["timestamp"] < test_start].copy()
    # PURGE: train rows whose 60-min label window overlaps the test block (D04)
    tr = tr[tr["timestamp"] + pd.Timedelta(minutes=MAX_H) <= test_start].copy()
    return tr, te

def fill_train_only(tr, te, cols):
    med = tr[cols].median(numeric_only=True)
    return tr[cols].fillna(med).values, te[cols].fillna(med).values

def mae(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.mean(np.abs(a - b)))

def rmse(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.sqrt(np.mean((a - b) ** 2)))

# ---------------- baselines ----------------
def pred_persistence(te, col_now, horizons=HORIZONS):
    return {h: te[col_now].values for h in horizons}

def pred_ha(tr, te, target_prefix):
    """Historical average per (location, dow, hour)."""
    key = ["location", "day_of_week", "hour"]
    out = {}
    for h in HORIZONS:
        yc = f"{target_prefix}_{h}"
        m = tr.groupby(key)[yc].mean()
        idx = pd.MultiIndex.from_arrays([te["location"], te["day_of_week"], te["hour"]])
        p = m.reindex(idx).values
        glob = tr[yc].mean()
        out[h] = np.where(np.isnan(p), glob, p)
    return out

def pred_seasonal_naive(df_past, te, target_prefix, lag_days=7):
    """Forecast t+h = value at (t+h-7d); lookup restricted to timestamps <= origin t."""
    idx = df_past.set_index(["location", "timestamp"])
    now_col = "available" if target_prefix == "available" else "vehicle_count"
    out = {h: [] for h in HORIZONS}
    for _, r in te.iterrows():
        for h in HORIZONS:
            ref = r["timestamp"] + pd.Timedelta(minutes=h) - pd.Timedelta(days=lag_days)
            try:
                v = idx.loc[(r["location"], ref)][now_col]
                if isinstance(v, pd.Series):
                    v = v.iloc[0]
            except KeyError:
                v = r[now_col]
            out[h].append(float(v))
    return {h: np.array(v) for h, v in out.items()}

def skill(mae_m, mae_ref):
    return float(1 - mae_m / mae_ref) if mae_ref else 0.0
