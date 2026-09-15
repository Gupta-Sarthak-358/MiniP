"""Real-zone replay (D14): Birmingham NCP Market lot streams through the same API
contract as simulated zones, clearly labeled as replay. Forecasts served here are
persistence (honest for a replay feed); the ML validation lives in E06/models/real_eval.json.
"""
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(BASE, "data", "real", "bham_replay.csv")

META = {"location": "birmingham", "label": "Birmingham NCP Market (REAL replay)",
        "capacity": 577, "source": "UCI ML Repository id=482 / Birmingham City Council (UK OGL)",
        "period": "2016-10-04..2016-12-19, 08:00-16:30", "is_real": True}

class Replay:
    def __init__(self):
        self.df = pd.read_csv(CSV, parse_dates=["timestamp"])
        self.i = 0

    def tick(self, steps=1):
        self.i = (self.i + steps) % len(self.df)

    def current(self):
        r = self.df.iloc[self.i]
        avail = float(r["available"])
        return {"timestamp": r["timestamp"].isoformat() if hasattr(r["timestamp"], "isoformat") else str(r["timestamp"]),
                "location": "birmingham", "capacity": int(r["capacity"]),
                "occupied": round(float(r["occupied"]), 1), "available": round(avail, 1),
                "occupancy_pct": round(float(r["occupancy_pct"]), 1),
                "congestion_label": "Low" if r["occupancy_pct"] < 50 else ("Moderate" if r["occupancy_pct"] < 75 else ("High" if r["occupancy_pct"] < 90 else "Severe")),
                "is_real": True, "replay_index": int(self.i), "replay_len": len(self.df)}

    def forecast(self):
        c = self.current()  # persistence: replay's honest forecast
        return [{"horizon_min": h, "available": c["available"], "method": "persistence (real replay)"}
                for h in (15, 30, 45, 60)]

REPLAY = Replay()
