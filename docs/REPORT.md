# Real-Time Traffic & Parking Availability Predictor — Project Report

## 1. Problem & objectives
Urban congestion and parking shortages are hard to manage with current-status-only systems: by the time a lot reads "full", the demand surge that filled it is over. This project predicts **traffic congestion and parking-slot availability 15/30/45/60 minutes ahead**, conditioned on time, location, weather, holidays, sales, public events **and incidents**, and serves the forecasts through a live web dashboard with calibrated uncertainty, recommendations, and drift monitoring.

Research question: *which information actually improves short-horizon parking/traffic forecasts, measured under an honest temporal protocol?*

## 2. Data
- **Historical (simulated, causal):** `data/historical.csv` — 43,180 rows, 90 days × 15-min × 5 zones (mall, stadium, station, office, residential). Generator (`backend/simulator/generate_dataset.py`) implements a causal chain (baseline → peak → sale → event arrival → fill → exodus → normalize) plus weather, holidays, and **41 injected incidents** (accident/closure/storm_shock, severity 1–3). Parking follows proportional-turnover dynamics (D10: departures ∝ occupancy ≈ 1.5 h avg stay), giving realistic occupancy spans (mall 75%, office 81%, residential 49%, stadium 53%, station 84%; ranges 25–100%).
- **Live (simulated sensors):** `backend/simulator/live_data.py` — stateful stepper with identical physics (train↔serve parity), scripted concert + mega-sale, and an `inject_incident` demo hook.
- **Real (sensor replay):** Birmingham NCP Market lot, UCI ML Repository id=482 (UK Open Government Licence), Oct–Dec 2016, cap 577, resampled to the 15-min grid (`data/real/bham_replay.csv`, script `backend/model/real_zone.py`). Sensor glitches (negative / >105% readings) clipped and reported. Served live via `/api/real-zone` + dashboard card, honestly labeled replay (D14/E06).
- Targets: `available_{15,30,45,60}`, `vehicles_{15,30,45,60}`, congestion score 0–100.

## 3. Methods
- **Baselines (required for honesty):** persistence, historical-average (loc×dow×hour), 7-day seasonal-naive, AR(24) per zone (OLS, direct per-horizon), SES/level-only exponential smoothing. A seasonal Holt-Winters attempt is documented as a **diagnosed failure** (E02a): unbounded smoothers extrapolate through the 0/capacity boundary.
- **ML:** LinearRegression (reference), RandomForest multi-output 15–60 min (**serving model**: one fit, CPU inference, native spread), XGBoost-300 on CUDA, LSTM-128 (seq 12) on RTX 4050 with standardized targets + per-location splits (failure log E01b/c kept).
- **Uncertainty:** conformal q90 intervals from walk-forward RF residuals (D07), replacing uncalibrated Gaussian bands. Widths: 6.2/9.0/11.3/13.4 slots; empirical coverage 0.900.
- **Monitoring:** River ADWIN over paired +30-min residuals per zone (D08); operating point delta=0.002, 20-pairing warmup; calibrated detection delay 23 steps, 0 clean false alarms (E05).

## 4. Evaluation protocol (the methodology upgrade)
4 expanding walk-forward origins × 5-day test blocks, strictly past→future; train-only imputation; **purge** of train rows whose 60-min label overlaps the test block; MAE/RMSE per horizon + **skill vs persistence**. Rationale: static splits can reverse model rankings (2026 literature); persistence is the mandatory comparator for inertia-dominated parking.

## 5. Results
### 5.1 Walk-forward, `available_30` (MAE slots / skill)
| Model | MAE | Skill |
|---|---|---|
| Persistence | 5.99 | 0.00 |
| SES | 5.99 | 0.00 |
| Linear | 5.78 | +0.04 |
| AR(24) | 6.79 | −0.13 |
| **RF-100** | **4.31** | **+0.28** |
| **XGB-300-cuda** | **4.07** | **+0.32** |
| HistAvg | 26.3 | −3.40 |
| Seasonal-naive | 30.3 | −4.06 |
Only context-aware ML beats persistence on parking. `vehicles_30`: RF 32.9 (+0.42) vs persistence 57.2 — traffic is strongly learnable. Figures: `docs/figures/eval_horizons.png`, `baselines_skill.png`.
*(Full table: `models/eval_walkforward.json`. Static-split numbers in `models/metrics.json` kept for the before/after-methodology story.)*

### 5.2 Ablation (RF-80 walk-forward; `ablation_mae.png`, `models/ablation.json`)
`available_30` MAE: time-only 26.35 → **+state 4.42** → +weather 4.44 → +event 4.45 → +sale/hol 4.42 → +incident 4.43. Current-state dominates **globally** — because events are rare.
### 5.3 …but context pays exactly when conditions are abnormal (`conditional_mae.png`, `models/slice_analysis.json`)
| Slice | RF | Persist | Skill |
|---|---|---|---|
| all (n=8636) | 4.31 | 5.95 | +0.28 |
| peak-hour (2520) | 4.23 | 6.46 | **+0.35** |
| event-day (672) | 7.40 | 9.26 | +0.20 (−1.87 slots abs.) |
| incident (39) | 7.35 | 8.67 | +0.15 (small-n stated) |
| sale-day (416) | 5.75 | 6.57 | +0.12 |

## 6. System & dashboard
FastAPI (`backend/app.py`): current/prediction/history/events/explain/recommendation/incident/drift/step/health/**real-zone** endpoints; validated inputs (404/422), 17 regression tests (`tests/`). Dashboard (`frontend/index.html`): status cards, history+forecast charts with 90% bands + coverage readout, heatmap, feature-importance bars, recommendations, incident-inject demo button, ADWIN drift banner, **real Birmingham replay card**, loading/error/empty states, keyboard + reduced-motion support.

## 6b. Sim-to-real validation (E06; `real_validation.png`, `models/real_eval.json`)
Walk-forward (3×7-day folds) on the real Birmingham series with reduced features: persistence 20.67 → HistAvg 25.41 → **RF 7.81 (skill +0.62)**. Real sensors are ~3× noisier than simulation — and the ML edge is ~2× larger. Same pattern, stronger. Caveats: daytime-only 2016 data, ~30-min native grid resampled to 15-min, single lot; sim-trained model deliberately not transferred (scheduled cross-test).

## 7. Demo script (5 min)
1. Show cards + 15–60 min forecast with 90% bands (coverage 0.90 chip). 2. Heatmap all zones. 3. **Inject incident** → congestion spike, forecast drop, recovery. 4. Burn-in → sustained incident → **drift alarm** (~25 steps). 5. Explain bars: why this prediction. 6. Ablation + slice charts: what actually helps, and when.

## 8. Limitations & next steps
Single-simulator data (one real zone, e.g. SINPA/Melbourne bays, is the top credibility upgrade); zones are independent rows — 1-block STGCN over a zone-adjacency graph is the scoped spatial step (D09); conformal calibration is in-fold (nested calibration follow-up); no auth/rate-limit (demo CORS open, flagged in code).

## 9. References (surveyed for RESEARCH_UPGRADES.md)
STGCN/DCRNN/Graph WaveNet lineage; ST-GNNFormer (Sci Rep 2026); TETRA GCN+xLSTM (2026); HG-GFNO (2026); 1-block STGCN efficiency study (2026); SRGNet OOD robustness (2026); Xiao et al. IEEE T-ITS 2023 parking survey; Zhang et al. TKDE 2022 weather/event LSTM; SHARE (AAAI 2020); DeepPA+SINPA; Perumal et al. 2025 (RF efficiency); Hyndman FPP3 (rolling-origin CV); EnbPI/ACI/CoRel conformal prediction; River online ML + ADWIN.

## 10. Artifact map (everything reproducible)
`PROJECT_PS.md` (spec) · `RESEARCH_UPGRADES.md` (literature→plan) · `docs/DECISIONS.md` (D01–D14) · `docs/EXPERIMENTS.md` (E01–E06 + failure logs) · `docs/figures/` (7 PNGs) · `docs/FRONTEND_SPEC.md` (redesign handoff) · `models/` (pkl + metrics/eval/ablation/slice/conformal/real JSON) · `tests/` (17 tests) · `.opencode/skills/` (12 vetted skills).
