"""
Synthetic causal dataset generator — 90 days, 15-min intervals, 5 locations.
Causal chain: baseline -> peak -> sale -> event arrival -> parking fills
              -> event ends -> departure spike -> normalize + weather/holiday noise.
Targets: available/vehicles/congestion for +15/+30/+45/+60 (1/2/3/4 steps).
"""
import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_CSV = os.path.join(BASE, "data", "historical.csv")
OUT_EVENTS = os.path.join(BASE, "data", "events.csv")
OUT_INCIDENTS = os.path.join(BASE, "data", "incidents.csv")

LOCATIONS = {
    "mall":        {"capacity": 1000, "base_veh": 350, "base_occ": 420, "label": "City Mall"},
    "stadium":     {"capacity": 800,  "base_veh": 250, "base_occ": 200, "label": "Sports Arena"},
    "station":     {"capacity": 500,  "base_veh": 400, "base_occ": 300, "label": "Railway Station"},
    "office":      {"capacity": 600,  "base_veh": 380, "base_occ": 250, "label": "Office Area"},
    "residential": {"capacity": 400,  "base_veh": 150, "base_occ": 250, "label": "Residential"},
}

WEATHERS = ["sunny", "cloudy", "rainy", "heavy_rain", "storm"]
W_PROBS = [0.55, 0.20, 0.15, 0.07, 0.03]
W_ENC = {"sunny": 0, "cloudy": 1, "rainy": 2, "heavy_rain": 3, "storm": 4}
ETYPE_ENC = {"none": 0, "concert": 1, "sports": 2, "expo": 3, "festival": 4}

DAYS = 90
STEP_MIN = 15
START = datetime(2026, 6, 1, 0, 0, 0)

def is_peak(hour):
    return 1 if (8 <= hour <= 10 or 17 <= hour <= 20) else 0

def congestion_score(vehicles, speed, occ_pct):
    # 0-100 scale
    s = vehicles / 10.0 + (60 - speed) * 1.8 + occ_pct * 0.35
    return float(np.clip(s, 0, 100))

def gen_events():
    """Pre-generate event calendar: stadium sports/concerts, mall expos, festivals."""
    evs = []
    d = START
    while d < START + timedelta(days=DAYS):
        # stadium: ~2 events/week
        if random.random() < 0.28:
            et = random.choice(["sports", "sports", "concert", "festival"])
            size = random.choice(["medium", "large", "large"])
            impact = {"medium": 2, "large": 3}[size]
            if et == "festival":
                impact = 4
            sh = random.choice([17, 18, 19])
            evs.append({"date": d.date().isoformat(), "location": "stadium",
                        "event_type": et, "event_size": size, "event_impact": impact,
                        "start": f"{sh:02d}:00", "end": f"{min(sh+4,23):02d}:00"})
        # mall expo/sale-linked event
        if random.random() < 0.12:
            evs.append({"date": d.date().isoformat(), "location": "mall",
                        "event_type": "expo", "event_size": random.choice(["small", "medium"]),
                        "event_impact": random.choice([1, 2]),
                        "start": "11:00", "end": "20:00"})
        # office conference rarely
        if random.random() < 0.05:
            evs.append({"date": d.date().isoformat(), "location": "office",
                        "event_type": "expo", "event_size": "small",
                        "event_impact": 1, "start": "09:00", "end": "17:00"})
        d += timedelta(days=1)
    return evs

def event_effect(loc, ts, ev):
    """Return (veh_add, occ_add, hours_to, hours_since, active) for matching event."""
    if ev is None:
        return 0, 0, 99.0, 99.0, 0
    d = ts.date().isoformat()
    if ev["date"] != d or ev["location"] != loc:
        return 0, 0, 99.0, 99.0, 0
    sh, sm = map(int, ev["start"].split(":"))
    eh, em = map(int, ev["end"].split(":"))
    start = ts.replace(hour=sh, minute=sm, second=0)
    end = ts.replace(hour=eh, minute=em, second=0)
    hrs_to = (start - ts).total_seconds() / 3600.0
    hrs_since = (ts - end).total_seconds() / 3600.0
    impact = ev["event_impact"]
    scale = {1: 60, 2: 140, 3: 260, 4: 380}[impact]
    # arrival ramp: 3h before -> start (gaussian-ish ramp)
    veh_add, occ_add, active = 0, 0, 0
    if -0.25 <= hrs_to <= 3.0 and hrs_to >= 0:
        ramp = 1 - (hrs_to / 3.0)  # 1 at start, 0 at 3h before
        veh_add = scale * (0.4 + 0.6 * ramp)
        occ_add = scale * 0.35 * ramp
    elif start <= ts <= end:
        active = 1
        veh_add = scale * 0.15  # underway, steady
        occ_add = scale * 0.30
    elif 0 <= hrs_since <= 1.5:
        # departure spike: sharp just after end
        decay = 1 - (hrs_since / 1.5)
        veh_add = scale * 1.15 * decay
        occ_add = -scale * 0.35 * (1 - decay)  # people leave -> occupancy drops
    return veh_add, occ_add, hrs_to, hrs_since, active

def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    events = gen_events()
    pd.DataFrame(events).to_csv(OUT_EVENTS, index=False)
    print(f"events: {len(events)} -> {OUT_EVENTS}")

    # --- incidents: accidents / closures / storm shocks (D06, SRGNet lesson) ---
    incidents = []
    dd = START
    while dd < START + timedelta(days=DAYS):
        for _loc in LOCATIONS:
            if random.random() < 0.10:
                _sh = random.choice([8, 9, 12, 17, 18, 19])
                incidents.append({"date": dd.date().isoformat(), "location": _loc,
                                  "kind": random.choice(["accident", "closure", "storm_shock"]),
                                  "severity": random.choice([1, 2, 2, 3]),
                                  "start": f"{_sh:02d}:00",
                                  "dur_steps": random.choice([2, 3, 4, 6])})
        dd += timedelta(days=1)
    pd.DataFrame(incidents).to_csv(OUT_INCIDENTS, index=False)
    print(f"incidents: {len(incidents)} -> {OUT_INCIDENTS}")
    inc_map = {}
    for _inc in incidents:
        inc_map.setdefault((_inc["date"], _inc["location"]), []).append(_inc)

    # index events by (date, location) for speed
    ev_map = {}
    for e in events:
        ev_map.setdefault((e["date"], e["location"]), []).append(e)

    rows = []
    n_steps = int(DAYS * 24 * 60 / STEP_MIN)
    holidays = set(random.sample(range(DAYS), k=6))  # ~6 holidays

    for loc, cfg in LOCATIONS.items():
        cap = cfg["capacity"]
        occ = cfg["base_occ"]
        for i in range(n_steps):
            ts = START + timedelta(minutes=STEP_MIN * i)
            day_idx = (ts.date() - START.date()).days
            dow = ts.weekday()
            is_weekend = 1 if dow >= 5 else 0
            is_holiday = 1 if day_idx in holidays else 0
            hour = ts.hour + ts.minute / 60.0
            peak = is_peak(ts.hour)
            night = 1 if (ts.hour >= 23 or ts.hour < 5) else 0

            # sale: mall mostly weekends + random mega days
            sale_int = 0
            is_sale = 0
            if loc == "mall":
                r = random.random()
                if is_weekend and r < 0.35:
                    sale_int = random.choice([1, 2, 2, 3])
                elif r < 0.06:
                    sale_int = random.choice([2, 3])
                is_sale = 1 if sale_int > 0 else 0
            elif random.random() < 0.02:
                sale_int = 1
                is_sale = 1

            # event lookup
            ev = None
            lst = ev_map.get((ts.date().isoformat(), loc), [])
            if lst:
                ev = lst[0]
            veh_add, occ_add, hrs_to, hrs_since, active = event_effect(loc, ts, ev)
            is_event = 1 if ev is not None else 0
            etype = ev["event_type"] if ev else "none"
            esize = ev["event_size"] if ev else "none"
            simp = {"small": 1, "medium": 2, "large": 3}
            eimpact = ev["event_impact"] if ev else 0
            esize_enc_v = simp.get(esize, 0)

            # incident lookup: active shock window?
            is_inc, inc_sev = 0, 0
            for _ic in inc_map.get((ts.date().isoformat(), loc), []):
                _sh, _sm = map(int, _ic["start"].split(":"))
                _s = ts.replace(hour=_sh, minute=_sm, second=0)
                _e = _s + timedelta(minutes=STEP_MIN * _ic["dur_steps"])
                if _s <= ts < _e:
                    is_inc, inc_sev = 1, _ic["severity"]
                    break

            weather = random.choices(WEATHERS, weights=W_PROBS)[0]
            temp = 28 + 6 * np.sin(2 * np.pi * ts.hour / 24) + np.random.normal(0, 1.5)
            if weather in ("rainy", "heavy_rain", "storm"):
                temp -= 3

            # base demand curves
            if loc == "office":
                base = cfg["base_veh"] * (1.6 if (peak and not is_weekend and not is_holiday) else (0.35 if is_weekend else 1.0))
            elif loc == "mall":
                base = cfg["base_veh"] * (1.5 if is_weekend else 1.0) * (1.25 if is_sale else 1.0)
                if 12 <= ts.hour <= 21:
                    base *= 1.3
            elif loc == "station":
                base = cfg["base_veh"] * (1.35 if peak else 1.0)
            elif loc == "residential":
                base = cfg["base_veh"] * (0.6 if 9 <= ts.hour <= 17 else 1.1)
            else:
                base = cfg["base_veh"]
            if is_holiday and loc in ("mall", "stadium"):
                base *= 1.25
            if night:
                base *= 0.25
            wmult = {"sunny": 1.0, "cloudy": 1.03, "rainy": 1.12, "heavy_rain": 1.22, "storm": 1.3}[weather]

            vehicles = max(5, base * wmult + veh_add + np.random.normal(0, 22))
            # sale adds vehicles for mall
            if is_sale and loc == "mall":
                vehicles += sale_int * 45
            # incident: traffic piles up, speeds collapse, some drivers avoid the lot
            if is_inc:
                vehicles += inc_sev * 90
                occ_add -= inc_sev * 8

            speed = float(np.clip(55 - vehicles / 22 - (8 if weather in ("heavy_rain", "storm") else (4 if weather == "rainy" else 0)) - is_inc * inc_sev * 4 + np.random.normal(0, 1.5), 5, 60))

            # parking dynamics: proportional turnover (self-regulating).
            # arrivals scale with traffic; departures scale with occupancy
            # (avg stay ~1.5h normal, longer at night) + post-event exodus surge.
            inflow = vehicles * 0.22 + occ_add + (sale_int * 12 if loc == "mall" else 0) + np.random.normal(0, 8)
            turnover = 0.08 if night else (0.26 if loc == "station" else 0.16)
            outflow = occ * turnover + (30 if 0 <= hrs_since <= 1.0 and active == 0 and is_event else 0) + np.random.normal(0, 6)
            if night:
                outflow *= 0.4
            occ = float(np.clip(occ + (inflow - outflow) * 0.25, 0, cap))
            avail = cap - occ
            occ_pct = occ / cap * 100.0
            cong = congestion_score(vehicles, speed, occ_pct)

            rows.append({
                "timestamp": ts.isoformat(), "location": loc, "capacity": cap,
                "hour": round(hour, 2), "day_of_week": dow,
                "is_weekend": is_weekend, "is_peak_hour": peak, "is_night": night,
                "is_holiday": is_holiday, "is_sale_day": is_sale, "sale_intensity": sale_int,
                "is_event_day": is_event, "event_type": etype, "event_size": esize,
                "event_impact": eimpact, "hours_to_event": round(min(hrs_to, 48), 2),
                "is_incident": is_inc, "incident_severity": inc_sev,
                "hours_since_event": round(min(hrs_since, 48), 2), "is_event_active": active,
                "weather": weather, "temperature": round(float(temp), 1),
                "vehicle_count": round(float(vehicles), 1), "avg_speed": round(float(speed), 1),
                "occupied": round(float(occ), 1), "available": round(float(avail), 1),
                "occupancy_pct": round(float(occ_pct), 1), "congestion": round(float(cong), 1),
            })

    df = pd.DataFrame(rows)
    # future targets per location (1/2/3/4 steps ahead)
    for loc in LOCATIONS:
        m = df["location"] == loc
        for h, col in [(1, 15), (2, 30), (3, 45), (4, 60)]:
            df.loc[m, f"available_{col}"] = df.loc[m, "available"].shift(-h)
            df.loc[m, f"vehicles_{col}"] = df.loc[m, "vehicle_count"].shift(-h)
            df.loc[m, f"congestion_{col}"] = df.loc[m, "congestion"].shift(-h)
    df = df.dropna().reset_index(drop=True)

    # encodings for model
    df["weather_enc"] = df["weather"].map(W_ENC)
    df["event_type_enc"] = df["event_type"].map(ETYPE_ENC)
    szmap = {"none": 0, "small": 1, "medium": 2, "large": 3}
    df["event_size_enc"] = df["event_size"].map(szmap)
    locmap = {"mall": 0, "stadium": 1, "station": 2, "office": 3, "residential": 4}
    df["location_enc"] = df["location"].map(locmap)

    # inject 1% missing to demonstrate handling (train.py imputes)
    # keep small so metrics stay good
    df.to_csv(OUT_CSV, index=False)
    print(f"rows: {len(df)} -> {OUT_CSV}")
    print(df.head(3).to_string())

if __name__ == "__main__":
    main()
