"""Stateful causal live simulator. Mirrors generate_dataset logic but steps live."""
import random
from datetime import datetime, timedelta
import numpy as np

LOCATIONS = {
    "mall":        {"capacity": 1000, "base_veh": 350, "base_occ": 420, "label": "City Mall"},
    "stadium":     {"capacity": 800,  "base_veh": 250, "base_occ": 200, "label": "Sports Arena"},
    "station":     {"capacity": 500,  "base_veh": 400, "base_occ": 300, "label": "Railway Station"},
    "office":      {"capacity": 600,  "base_veh": 380, "base_occ": 250, "label": "Office Area"},
    "residential": {"capacity": 400,  "base_veh": 150, "base_occ": 250, "label": "Residential"},
}
W_ENC = {"sunny": 0, "cloudy": 1, "rainy": 2, "heavy_rain": 3, "storm": 4}
ETYPE_ENC = {"none": 0, "concert": 1, "sports": 2, "expo": 3, "festival": 4}
SZMAP = {"none": 0, "small": 1, "medium": 2, "large": 3}

class Simulator:
    def __init__(self):
        # start at a busy Friday 16:00 so demo shows event dynamics quickly
        self.now = datetime(2026, 9, 11, 16, 0, 0)
        self.state = {}
        for loc, cfg in LOCATIONS.items():
            self.state[loc] = {"occ": cfg["base_occ"] * 0.8, "weather": "sunny",
                               "temp": 30.0, "history": []}
        # scripted demo events: stadium concert tonight 18:00-22:00, mall mega sale today
        self.events = [
            {"location": "stadium", "event_type": "concert", "event_size": "large",
             "event_impact": 3, "start": "18:00", "end": "22:00",
             "name": "Live Concert — Sports Arena"},
            {"location": "mall", "event_type": "expo", "event_size": "medium",
             "event_impact": 2, "start": "11:00", "end": "21:00",
             "name": "Mega Sale — City Mall"},
        ]
        self.sale = {"mall": 3}  # mega sale intensity today
        self.incidents = {}  # loc -> {"kind","severity","steps_left"} (D06 demo hook)
        for _ in range(32):  # pre-roll 8h history
            self.step()

    def inject_incident(self, loc, kind="accident", severity=2, dur_steps=4):
        """Dashboard/API hook: SIMULATED INCIDENT demo moment. Returns False on bad id."""
        if loc not in LOCATIONS:
            return False
        self.incidents[loc] = {"kind": kind, "severity": max(1, min(3, severity)),
                               "steps_left": max(1, min(12, dur_steps))}
        return True

    def active_incident(self, loc):
        inc = self.incidents.get(loc)
        if inc and inc["steps_left"] > 0:
            return inc
        return None

    def _event_now(self, loc, ts):
        for e in self.events:
            if e["location"] != loc:
                continue
            sh, sm = map(int, e["start"].split(":"))
            eh, em = map(int, e["end"].split(":"))
            s = ts.replace(hour=sh, minute=sm, second=0)
            en = ts.replace(hour=eh, minute=em, second=0)
            hrs_to = (s - ts).total_seconds() / 3600
            hrs_since = (ts - en).total_seconds() / 3600
            if -1 <= hrs_to <= 12 or -2 <= hrs_since <= 12:
                scale = {1: 60, 2: 140, 3: 260, 4: 380}[e["event_impact"]]
                va = oa = 0; active = 0
                if 0 <= hrs_to <= 3:
                    ramp = 1 - hrs_to / 3
                    va = scale * (0.4 + 0.6 * ramp); oa = scale * 0.35 * ramp
                elif s <= ts <= en:
                    active = 1; va = scale * 0.15; oa = scale * 0.30
                elif 0 <= hrs_since <= 1.5:
                    decay = 1 - hrs_since / 1.5
                    va = scale * 1.15 * decay; oa = -scale * 0.35 * (1 - decay)
                return e, va, oa, hrs_to, hrs_since, active
        return None, 0, 0, 48.0, 48.0, 0

    def _step_one(self, loc):
        cfg = LOCATIONS[loc]; st = self.state[loc]; ts = self.now
        cap = cfg["capacity"]
        peak = 1 if (8 <= ts.hour <= 10 or 17 <= ts.hour <= 20) else 0
        night = 1 if (ts.hour >= 23 or ts.hour < 5) else 0
        dow = ts.weekday(); is_weekend = 1 if dow >= 5 else 0
        sale_int = self.sale.get(loc, 0); is_sale = 1 if sale_int else 0
        e, va, oa, hrs_to, hrs_since, active = self._event_now(loc, ts)
        # weather drift
        if random.random() < 0.06:
            st["weather"] = random.choice(["sunny", "sunny", "cloudy", "rainy"])
        w = st["weather"]
        wmult = {"sunny": 1.0, "cloudy": 1.03, "rainy": 1.12, "heavy_rain": 1.22, "storm": 1.3}[w]
        if loc == "office":
            base = cfg["base_veh"] * (1.6 if peak and not is_weekend else (0.35 if is_weekend else 1.0))
        elif loc == "mall":
            base = cfg["base_veh"] * (1.5 if is_weekend else 1.0) * (1.25 if is_sale else 1.0)
            if 12 <= ts.hour <= 21: base *= 1.3
        elif loc == "station":
            base = cfg["base_veh"] * (1.35 if peak else 1.0)
        elif loc == "residential":
            base = cfg["base_veh"] * (0.6 if 9 <= ts.hour <= 17 else 1.1)
        else:
            base = cfg["base_veh"]
        if night: base *= 0.3
        vehicles = max(5, base * wmult + va + np.random.normal(0, 18))
        if is_sale and loc == "mall": vehicles += sale_int * 45
        inc = self.active_incident(loc)
        is_inc, inc_sev = (0, 0) if inc is None else (1, inc["severity"])
        if inc is not None:
            vehicles += inc_sev * 90
            oa -= inc_sev * 8
            inc["steps_left"] -= 1
        speed = float(np.clip(55 - vehicles / 22 - (4 if w == "rainy" else 0) - is_inc * inc_sev * 4 + np.random.normal(0, 1.2), 5, 60))
        inflow = vehicles * 0.22 + oa + (sale_int * 12 if loc == "mall" else 0) + np.random.normal(0, 6)
        turnover = 0.08 if night else (0.26 if loc == "station" else 0.16)
        outflow = st["occ"] * turnover + (30 if 0 <= hrs_since <= 1.0 and active == 0 and e else 0) + np.random.normal(0, 5)
        if night: outflow *= 0.4
        occ = float(np.clip(st["occ"] + (inflow - outflow) * 0.25, 0, cap))
        st["occ"] = occ
        avail = cap - occ; occ_pct = occ / cap * 100
        cong = float(np.clip(vehicles / 10 + (60 - speed) * 1.8 + occ_pct * 0.35, 0, 100))
        feat = {"timestamp": ts.isoformat(), "location": loc, "capacity": cap,
                "hour": round(ts.hour + ts.minute / 60, 2), "day_of_week": dow,
                "is_weekend": is_weekend, "is_peak_hour": peak, "is_night": night,
                "is_holiday": 0, "is_sale_day": is_sale, "sale_intensity": sale_int,
                "is_event_day": 1 if e else 0, "event_type": e["event_type"] if e else "none",
                "event_size": e["event_size"] if e else "none",
                "event_impact": e["event_impact"] if e else 0,
                "hours_to_event": round(min(max(hrs_to, -5), 48), 2),
                "hours_since_event": round(min(max(hrs_since, -5), 48), 2),
                "is_event_active": active,
                "is_incident": is_inc, "incident_severity": inc_sev,
                "incident_kind": inc["kind"] if inc is not None else "none",
                "weather": w,
                "temperature": round(28 + 4 * np.sin(2 * np.pi * ts.hour / 24), 1),
                "vehicle_count": round(float(vehicles), 1), "avg_speed": round(float(speed), 1),
                "occupied": round(float(occ), 1), "available": round(float(avail), 1),
                "occupancy_pct": round(float(occ_pct), 1), "congestion": round(float(cong), 1),
                "weather_enc": W_ENC[w], "event_type_enc": ETYPE_ENC[e["event_type"]] if e else 0,
                "event_size_enc": SZMAP[e["event_size"]] if e else 0,
                "location_enc": {"mall": 0, "stadium": 1, "station": 2, "office": 3, "residential": 4}[loc]}
        st["history"].append(feat)
        st["history"] = st["history"][-300:]
        return feat

    def step(self, steps=1):
        out = {}
        for _ in range(steps):
            self.now += timedelta(minutes=15)
            for loc in LOCATIONS:
                out[loc] = self._step_one(loc)
        return out

    def current(self, loc):
        return self.state[loc]["history"][-1]

    def history(self, loc, points=40):
        return self.state[loc]["history"][-points:]

SIM = Simulator()
