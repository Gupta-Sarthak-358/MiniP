# Real-Time Traffic & Parking Availability Predictor — Full Project Statement (PS)

> A context-aware intelligent transportation system that forecasts traffic congestion and parking availability by combining temporal, spatial, environmental, and event-driven signals, then converts those forecasts into actionable mobility recommendations.

Date: 2026-09-15
Location: `C:\Users\satvi\Desktop\minip`

---

## 1. Project Overview

Web-based intelligent transportation system that predicts traffic congestion levels and parking-slot availability for a location over the next time intervals (15 / 30 / 45 / 60 min).

Combines:
- Historical traffic/parking data
- Simulated real-time sensor data (stateful, causally-driven)
- Time-based patterns (hour, dow, peak, weekend)
- Weather, holidays, weekends
- Sale / promotional days + sale_intensity
- Public events (sports, concert, expo, festival) + timing + size + impact
- Location-specific behavior (mall vs stadium vs office vs station vs residential)

ML / time-series model processes inputs and predicts future traffic and available parking. Results on interactive dashboard showing current + predicted.

## 2. Problem Statement

Urban areas have unpredictable congestion and parking shortages. Current-status-only systems are insufficient.

Example:
- 5:00 PM: 30 spaces free. But concert at 6:00 PM nearby -> spaces drop rapidly.
- Traffic moderate now, but large event ending 9:00 PM -> severe congestion soon.

Need: predict what is likely to happen, not just report now, using historical patterns + upcoming context.

## 3. Main Objective

Develop web-based ML system predicting congestion and/or parking using historical + simulated real-time data with context (time, weather, holidays, sales, events).

Answer:
- How congested in 30 min?
- How many slots in 1 hour?
- Will availability drop due to upcoming event?
- Which location least congested?
- Best time to reach parking?
- How do event/sale affect demand?

## 4. Core Idea

### A. Traffic Prediction
- traffic volume, avg speed, congestion score (0-4), congestion category (Low/Moderate/High/Severe)

Example: Current Medium -> +30min High -> +60min High

### B. Parking Prediction
- occupied, available, occupancy %

Example: Capacity 500, Current 128 -> +30min 94 -> +60min 51

Implement both. Parking as primary regression target, traffic/congestion as secondary.

## 5. Innovation: Context-Aware Prediction

Not just `hour + day + historical avg`. Learn special-day effects.

- Normal Monday 8AM High, 12PM Medium, 5PM High, 10PM Low
- Monday + Major Sale: 12PM High, 5PM Very High, 8PM Very High
- Saturday + Concert 6PM-10PM: 4PM Medium, 6PM Very High, 10PM Very High, 11PM Medium

Model learns: Friday + 6PM + Mall + Mega Sale + Rain + Nearby Concert => demand UP, congestion UP.

## 6. Features / Data Inputs

### Time Features
`timestamp, hour, minute, day_of_week (0-6), is_weekend (0/1), month, is_peak_hour (0/1: 8-10, 17-20), is_night`

### Traffic Features
`vehicle_count, prev_vehicle_count, avg_speed, road_occupancy, hist_avg_volume, prev_congestion`

### Parking Features
`capacity, occupied, available, occupancy_pct, inflow_15min, outflow_15min, avg_duration_min`

## 7. Special-Day Features (Major Feature)

| Feature | Example values | Why it matters |
|---|---|---|
| is_holiday | 0/1 | changes patterns |
| holiday_type | national/festival/regional/none | different behavior |
| is_weekend | 0/1 | different travel |
| is_sale_day | 0/1 | shopping areas crowded |
| sale_intensity | 0-3 (0 none,1 small,2 med,3 major) | normal vs mega sale |
| is_event_day | 0/1 | concerts/matches/expo |
| event_type | concert/sports/expo/none | different demand |
| event_size | small/medium/large | larger -> more vehicles |
| event_start_time | 18:00 | traffic rises before |
| event_end_time | 22:00 | post-event spike |
| weather | sunny/rainy/heavy_rain/storm | changes behavior |
| is_school_day | 0/1 | useful near edu areas |
| event_impact | 0-4 (0 normal,1 small,2 med,3 large,4 festival) | estimated impact |

Holidays: national, festival, regional, public.
Sales: Black-Friday style, end-of-season, festival, mall anniversary, flash, mega.
Events: concert, cricket/football, exhibition, conference, festival, college event, gathering.

## 8. Event Timing Is Critical

Don't just use `is_event_day`. Use timing + relative features:
- `event_start, event_end, hours_to_event, hours_since_event, is_arrival_window, is_departure_window, is_event_active`

Learned pattern:
```
16:30 people start arriving
17:30 traffic increasing
18:00 event begins
19:00 parking nearly full
21:45 ending soon
22:00 major departure
22:15 traffic spike
23:00 normalize
```

## 9. Weather Features

`weather (sunny/cloudy/rainy/heavy_rain/storm), temperature_C, rainfall_mm, visibility_km`

Simplified: normal / rainy / heavy_rain / storm. Rain increases congestion, changes parking demand.

## 10. Location Features

Zones:
- Zone A: City Mall (weekend/sale peak)
- Zone B: Stadium (extreme around match)
- Zone C: Railway Station (steady + train peaks)
- Zone D: Office Area (weekday AM/PM peak)
- Zone E: Residential (night high parking)

`location_id, location_type, capacity` as features (one-hot / ordinal).

## 11. Dataset Structure

| Timestamp | Location | Vehicles | Avg Speed | Occupied | Capacity | Holiday | Sale | Event | Weather |
|---|---|---|---|---|---|---|---|---|---|
| 08:00 | Mall | 420 | 32 | 380 | 500 | 0 | 0 | 0 | Normal |
| 18:00 | Mall | 720 | 18 | 470 | 500 | 0 | 1 | 0 | Normal |
| 19:00 | Mall | 850 | 12 | 492 | 500 | 0 | 1 | 0 | Normal |
| 18:00 | Stadium | 900 | 10 | 480 | 500 | 0 | 0 | 1 | Normal |

Target: `future_available_30min` and/or `future_congestion_score`.

In this repo: `data/historical.csv` generated by `backend/simulator/generate_dataset.py`.

## 12. Target Variable

- Option 1 Parking: `available_slots_30min` (e.g. now 120 -> 83)
- Option 2 Traffic: `traffic_volume_30min` (e.g. now 500 -> 720)
- Option 3 Congestion Score 0-4: 0 none,1 low,2 moderate,3 high,4 severe -> regression

This build predicts all three for +15/+30/+45/+60: `available`, `vehicles`, `congestion`.

## 13. ML Approach

- Baseline: LinearRegression (simple, explainable)
- Main: RandomForestRegressor (nonlinear, mixed features, feature importance)
- Advanced: XGBoost (if installed, else fallback to RF / HistGradientBoosting)
- Time-series option (future): ARIMA/SARIMA/Prophet/LSTM — not needed for MVP. Well-engineered RF > unnecessary LSTM.

Compare models, pick best by MAE/RMSE/R2.

## 14. Regression Note

Linear: `y_hat = b0 + b1*x`, R2, least squares minimizes squared residuals. Actual project uses RF/XGBoost (nonlinear). Visualize predicted vs actual + residuals in evaluation.

## 15. Prediction Horizons

Dashboard shows:
```
Now -> 145 slots / Moderate
+15 -> 131 / High
+30 -> 110 / High
+45 -> 82 / Severe
+60 -> 57 / High
```
With confidence interval: `73 +- 12 (61-85)` using tree std.

## 16. Simulated Real-Time Data (Stateful, Causal)

No IoT needed. Live simulator every N sec:
```
500 -> 515 -> 527 -> 545 -> 570 vehicles
150 -> 146 -> 142 -> 137 -> 129 available
```
Causal chain: Baseline -> +Peak -> +Sale -> +Event arrival -> parking fills -> event ends -> departure spike -> normalize.

Implemented in `backend/simulator/live_data.py`.

Simulator timeline demo:
```
16:00 Normal
17:00 Attendees arriving
18:00 Occupancy sharp rise
19:00 High congestion
20:00 Event underway
22:00 Ends
22:15 Exit spike
23:00 Toward normal
```

## 17. Real-Time Architecture

```
Historical Dataset -> Preprocessing -> Feature Engineering -> ML Training -> Trained Model
Live Simulator + Event/Weather DB -> Prediction Engine -> Backend API -> Web Dashboard
```

See `backend/app.py` (FastAPI) + `backend/model/predict.py`.

## 18-23. Web Dashboard

Header: REAL-TIME TRAFFIC & PARKING PREDICTOR + Last updated.

Cards: Traffic (HIGH), Parking (128 Available), Prediction (30min HIGH).

Graphs (Chart.js):
- Traffic history line (4-9PM)
- Actual vs predicted + future
- Available slots Now->Future (500..0)
- Event indicator: UPCOMING EVENT, venue, time, impact, forecast (230 -> 150 -> 47)
- Sale indicator: MEGA SALE, location, impact
- Heatmap: Zone A green Low 78%, B yellow 42%, C orange 15%, D red 5% (Leaflet or CSS grid for MVP)

Implemented in `frontend/index.html`.

## 24. Recommendation System (Predict -> Explain -> Recommend)

- Don't just say Mall A 20 slots. Say Recommended: Mall B (117 predicted in 30min).
- Warning: Parking at Mall A full in ~20-30 min.
- Route A 87/100 vs Route B 51/100 => Recommend B.

Implemented as `/api/recommendation` heuristic.

## 25. Model Explainability

Show why: Event nearby, Peak hour, Current traffic, Friday, Rain with bars. Use RF feature_importances_. Served via `/api/explain`.

## 26. Backend

```
backend/
  app.py
  model/train.py, predict.py
  simulator/generate_dataset.py, live_data.py
  database/db.py
```

FastAPI. APIs:
- GET /api/current-status?location=
- GET /api/prediction?location=
- GET /api/history?location=&points=
- GET /api/events
- GET /api/locations
- GET /api/recommendation
- GET /api/explain?location=

## 27. Frontend

HTML+CSS+JS + Chart.js + Leaflet (CDN, fallback to CSS grid). Polls backend every 5s.

## 28. Database

SQLite (`traffic.db`):
- observations(timestamp,location,vehicles,speed,occupied,available,weather,...)
- events(name,location,start,end,type,size)
- predictions(timestamp,location,horizon,pred_congestion,pred_available,model_version)

MVP uses CSV + in-memory + SQLite optional.

## 29. Model Training Pipeline

Raw -> Clean/missing -> Feature Eng -> Time-split (no shuffle, train past, test future) -> Train -> Evaluate -> Select best -> Save .pkl -> Deploy.

## 30. Model Evaluation

MAE (avg off, e.g. 12.4 slots), RMSE (penalize large), R2 (variance explained).

Example table (illustrative, replace with real):
| Model | MAE | RMSE | R2 |
| Linear | 32.5 | 44.2 | 0.72 |
| RF | 18.3 | 27.6 | 0.88 |
| XGB | 15.7 | 24.1 | 0.91 |

Report real values from `models/metrics.json`.

## 31-33. Robustness & Security

- Missing: interpolation, ffill, mean/median, document.
- Abnormal: validate 0<=occupied<=capacity, 0<=available<=capacity.
- Security: API validation, admin auth (future), input validation, rate limit, HTTPS in deploy.

## 34. User Roles

- Public: view traffic/parking/predictions, search, events, recommendations.
- Admin (future): add locations/events/sales, capacity, monitor, retrain, metrics.

## 35. Scenario: Mall

Cap 1000, 4PM Avail 340 Medium, Saturday Mega Sale => 5PM 250, 6PM 150, 7PM 75, 8PM 30 => CRITICAL ~8PM. Live data recalculates.

## 36. Scenario: Stadium

Match 7-10PM 30k => 5PM Med/400 -> 6PM High, 6:30 Very High, 7 Severe, 10 Severe, 10:30 Very High, 11 High, 11:30 Medium. Proves event-temporal learning.

## 37. Why Strong

Data Science + ML + Time-series + SWE (API/DB/sim) + Web (dashboard/charts/maps) + Smart-city + Decision support. Not just train+accuracy.

## 38. Stack (this repo)

Python, Pandas, Numpy, Scikit-learn, FastAPI/Uvicorn, SQLite, HTML/CSS/JS, Chart.js, Leaflet.

## 39. Future

Real IoT (camera, ultrasonic, RPi/ESP32), real maps, route rec, parking rec, LSTM/GRU/Transformer, auto event ingestion (sports/concert/holiday APIs).

## 40. MVP Scope

Must-have: dataset, preprocessing, feature eng, event/sale/holiday, regression, simulator, 15/30/60 pred, FastAPI, dashboard, charts, evaluation.
Good: multi-location, heatmap, event viz, recommendation, importance, admin.
Advanced: IoT, live maps, routes, LSTM/XGB compare, auto ingestion.

## 41. Rating / Verdict

| Dimension | Rating |
| Problem relevance | 9/10 |
| ML depth | 8/10 |
| SWE | 8.5/10 |
| Demo | 9/10 |
| Real-world | 9/10 |
| Novelty | 6.5/10 |
| Expansion | 10/10 |
| Overall | 8.5/10 |

Strength: event/sale/holiday context layer. Pitch as context-aware system, not just ML predicting traffic. Make simulator stateful/causal, show uncertainty (73 +-12, critical 7:15-7:45), and Predict->Explain->Recommend.

## Run

```
pip install -r requirements.txt
python backend/simulator/generate_dataset.py
python backend/model/train.py
uvicorn backend.app:app --reload
# open frontend/index.html (or http://127.0.0.1:8000)
```
