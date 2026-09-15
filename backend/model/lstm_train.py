"""LSTM temporal model (PyTorch + CUDA). Sequence of past 12x15min -> predict available_30.
Uses Mnemo .venv torch 2.5.1+cu121. Run: Mnemo/.venv/Scripts/python.exe backend/model/lstm_train.py
"""
import os, json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(BASE, "data", "historical.csv")
MODEL_DIR = os.path.join(BASE, "models")
SEQ = 12
FEATS = ["hour","day_of_week","is_weekend","is_peak_hour","is_night","is_holiday",
    "is_sale_day","sale_intensity","is_event_day","event_type_enc","event_size_enc",
    "event_impact","hours_to_event","hours_since_event","is_event_active",
    "weather_enc","temperature","vehicle_count","avg_speed","occupied","available",
    "occupancy_pct","location_enc","capacity","is_incident","incident_severity"]

class LSTMReg(nn.Module):
    def __init__(self, d_in, h=128, layers=2, drop=0.2):
        super().__init__()
        self.lstm = nn.LSTM(d_in, h, layers, batch_first=True, dropout=drop)
        self.head = nn.Sequential(nn.Linear(h, 64), nn.ReLU(), nn.Dropout(0.1), nn.Linear(64, 1))
    def forward(self, x):
        o, _ = self.lstm(x)
        return self.head(o[:, -1, :]).squeeze(-1)

def make_seq(arr, target, seq=SEQ):
    X, y = [], []
    for i in range(seq, len(arr)):
        X.append(arr[i-seq:i]); y.append(target[i])
    return np.array(X, np.float32), np.array(y, np.float32)

def main(epochs=12, batch=512):
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device: {dev} ({torch.cuda.get_device_name(0) if dev=='cuda' else 'cpu'})")
    df = pd.read_csv(CSV).sort_values(["location", "timestamp"]).reset_index(drop=True)
    # per-location sequences to avoid leakage across zones; scalers fit on
    # POOLED TRAIN PORTIONS only (per-loc 80/20 -> pool). D04.
    raw = {loc: (g[FEATS].values.astype(np.float32),
                 g["available_30"].values.astype(np.float32))
           for loc, g in df.groupby("location")}
    scaler = StandardScaler()
    scaler.fit(np.concatenate([v[0][:int(len(v[0]) * 0.8)] for v in raw.values()]))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "lstm_scaler.pkl"))
    # standardize TARGETS too: post-rebalance available swings 0..cap and raw-scale
    # Huber/MSE gradients stall otherwise (E01b: R2 -0.12 on raw targets)
    y_scaler = StandardScaler()
    y_scaler.fit(np.concatenate([v[1][:int(len(v[1]) * 0.8)] for v in raw.values()]).reshape(-1, 1))
    joblib.dump(y_scaler, os.path.join(MODEL_DIR, "lstm_yscaler.pkl"))
    Xs, ys = [], []
    for loc, (a_raw, t_raw) in raw.items():
        a = scaler.transform(a_raw)
        t = y_scaler.transform(t_raw.reshape(-1, 1)).ravel()
        X, y = make_seq(a, t)
        Xs.append(X); ys.append(y)
    # E01c fix: split per-location 80/20 THEN pool. A global cut tested on an
    # entirely unseen location (station) — a harder cross-site task, not the
    # temporal-forecast task. Pool per-loc splits to test future-given-past.
    Xtrs, ytrs, Xtes, ytes = [], [], [], []
    for X, y in zip(Xs, ys):
        c = int(len(X) * 0.8)
        Xtrs.append(X[:c]); ytrs.append(y[:c]); Xtes.append(X[c:]); ytes.append(y[c:])
    X = np.concatenate(Xtrs + Xtes); y = np.concatenate(ytrs + ytes)
    n = len(X); cut = sum(map(len, Xtrs))
    tr = TensorDataset(torch.from_numpy(X[:cut]), torch.from_numpy(y[:cut]))
    te = TensorDataset(torch.from_numpy(X[cut:]), torch.from_numpy(y[cut:]))
    trl = DataLoader(tr, batch_size=batch, shuffle=True)
    tel = DataLoader(te, batch_size=2048)
    m = LSTMReg(len(FEATS)).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    loss = nn.HuberLoss()
    for ep in range(epochs):
        m.train(); tot = 0
        for xb, yb in trl:
            xb, yb = xb.to(dev), yb.to(dev)
            opt.zero_grad(); l = loss(m(xb), yb); l.backward()
            torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
            opt.step(); tot += l.item()*len(xb)
        m.eval(); ps = []
        with torch.no_grad():
            for xb, _ in tel:
                ps.append(m(xb.to(dev)).cpu().numpy())
        ps = np.concatenate(ps)
        # inverse-transform to slots for honest metrics
        ps_slots = y_scaler.inverse_transform(ps.reshape(-1, 1)).ravel()
        y_slots = y_scaler.inverse_transform(y[cut:].reshape(-1, 1)).ravel()
        mae = mean_absolute_error(y_slots, ps_slots)
        print(f"epoch {ep+1}/{epochs} train_loss {tot/cut:.4f} val_MAE {mae:.3f}")
    rmse = mean_squared_error(y_slots, ps_slots) ** 0.5
    r2 = r2_score(y_slots, ps_slots)
    print(f"LSTM val MAE {mae:.3f} RMSE {rmse:.3f} R2 {r2:.4f}")
    torch.save(m.state_dict(), os.path.join(MODEL_DIR, "lstm_avail30.pt"))
    json.dump({"mae": float(mae), "rmse": float(rmse), "r2": float(r2), "device": dev, "seq": SEQ},
              open(os.path.join(MODEL_DIR, "lstm_metrics.json"), "w"), indent=2)

if __name__ == "__main__":
    main()
