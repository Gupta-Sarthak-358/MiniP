# Deep-Dive Research → Upgrade Roadmap
**Topic (teacher):** Web dashboard showing predicted traffic congestion / parking-slot availability using a time-series/regression model trained on historical + live-simulated data.
**Date:** 2026-09-15 | Sources: 2023–2026 literature + open datasets + libraries. All claims below trace to the cited works.

---

## 1. Traffic forecasting: where the field is (2026)

**Dominant paradigm: Spatio-Temporal GNNs.** The lineage is STGCN (temporal conv + graph conv) → DCRNN (diffusion + RNN) → Graph WaveNet (adaptive adjacency + dilated conv) → attention/Transformer variants (ASTGCN, GMAN). Our current stack (RF/XGB/LSTM on flat per-row features) sits one generation behind: it models **time** but not **space** — the 5 zones are independent rows with a `location_enc` integer.

**2026 advances worth knowing (pick ideas, not code):**
- **Dynamic/adaptive graphs beat static distance graphs.** ST-GNNFormer (Sci Rep 2026) learns time-varying adjacency + multi-scale temporal attention: up to **7.5% MAE gain at 60-min** on METR-LA/PEMS-BAY/PEMS04/08. Lesson for us: zone correlations change during events (stadium ↔ mall couple on match days, decouple otherwise) — a fixed `location_enc` cannot express this.
- **Memory-based temporal models win long horizons.** TETRA (GCN + xLSTM, 2026): **13–18% MAE reduction** over STGCN/GMAN at 30–60 min. Validates our LSTM direction; suggests trying xLSTM-style or simply longer sequence windows for the 45/60-min heads.
- **Efficiency reality check.** A June 2026 study shows **1-block STGCN ≈ 2-block** (≤1.8% MAE loss, ~38% lower latency); SimST shows plain temporal models rival GNNs at 39× throughput. Lesson: do NOT build a giant model to impress — a small graph model + honest evaluation impresses more. A 1-block STGCN is the right-sized "advanced model" for this project.
- **Robustness gap (examiner ammunition).** SRGNet (2026): SOTA models degrade **+116–230% under real incidents**; global RMSE hides epicenter failure. Our simulator currently has no incidents — adding incident injection + "local OOD" scoring turns a weakness into a feature.
- **Interpretability trend.** SGSAN (2026): learned directed dependency graphs that match physical road logic. Our RF feature-importance bars are the simple version of this story — keep them, and a zone-adjacency visualization would rhyme with the literature.

**Standard benchmarks to cite/compare:** METR-LA (207 sensors, LA), PEMS-BAY (325, Bay Area), PEMS03/04/07/08 (flow). Standard protocol: **chronological 70/10/20 split, horizons 15/30/60 min, MAE/RMSE/MAPE**. Open CSV copies on Zenodo + HuggingFace (`witgaw/METR-LA`, parquet, pre-split).

## 2. Parking prediction: the established ladder

Surveys: Xiao et al. IEEE T-ITS 2023 (first parking survey: statistical → GNN), Cao et al. 2024, Ma et al. 2024 (639 papers), Channamallu et al. 2025. The method ladder:
1. Classical: HA, ARIMA/VAR — weak on volatility but **mandatory baselines**.
2. Tree ensembles: RF/ExtraTrees — Perumal et al. 2025 finds **RF best on efficiency/runtime** for large-scale parking. (Our RF choice is defensible — cite this.)
3. Sequential DL: LSTM (Fan et al.), attention-TCN (Shang et al.).
4. **Weather-aware + event LSTM** (Zhang et al. TKDE 2022) — almost exactly our feature set; strong citation for the event/sale/weather layer.
5. Graph zone-wise: Feng et al. (graph ST, zone-wise lots), SHARE (Zhang, AAAI 2020, hierarchical recurrent GNN, semi-supervised city-wide), DeepPA + **SINPA dataset** (1,687 Singapore lots, 1 yr, open at `github.com/yoshall/SINPA`, 9.2% error cut for 3-h forecasts).

**Open parking data:** SINPA (best: lot-level + weather + geo), City of Melbourne on-street bay sensors (data.gov.au / data.melbourne.vic.gov.au), SFpark-style meter data. Even **one real zone** alongside simulated ones transforms credibility ("sim-to-real" framing).

## 3. Evaluation methodology — the highest-ROI upgrade

This is where the teacher's "time-series model" wording bites. Three findings:

1. **Static single split can reverse model rankings.** A March 2026 study: XGBoost looked uniformly best under a static split, but under rolling-origin evaluation it **lost to SARIMA and even persistence** at short horizons. Our `train.py` uses exactly one static 80/20 split. Fix: **walk-forward (rolling-origin) validation** — refit on growing/sliding windows, forecast strictly forward, average errors (Hyndman FPP3 §5.10; `sklearn.TimeSeriesSplit`, Darts/sktime/Nixtla `mlforecast.cross_validation`).
2. **Always report vs naive baselines.** Persistence (repeat last value) and seasonal-naive + skill scores (`1 − RMSE_model/RMSE_naive`) and MASE. "R² 0.94" alone is meaningless if persistence gets 0.93 — and for 15-min parking, persistence is brutally strong (explains our RF avail MAE 0.38).
3. **Leakage hygiene:** preprocessing (medians/scalers) fit on **train fold only** — our current `fillna(df.median())` before splitting is a (small) leak; per-fold purging/embargo matters because our 15/30/45/60-min labels **overlap** future rows (Lopez de Prado purging). Fix in the same edit as walk-forward.

## 4. Uncertainty: replace Gaussian tree-std with conformal prediction

Our dashboard CI (`±1.96·tree_std`) assumes Gaussian errors — uncalibrated. The 2024–25 literature converges on **conformal prediction for time series**: EnbPI (ensemble bootstrap intervals, works on top of RF/XGB/LSTM with no retraining), ACI/ECI (online adaptive), CoRel (ICML 2025, graph-aware), ResCP (training-free). Practical recipe: calibrate on validation residuals → intervals with **guaranteed coverage** → dashboard shows "90% interval, empirical coverage 89.4%". One honest number beats a pretty band. (Solar-forecasting study 2025: XGB+EnbPI well-calibrated; LSTM alone undercovers — relevant since we serve RF but train LSTM.)

## 5. Streaming/real-time layer

- **River** (successor of creme + scikit-multiflow): online regressors + drift detectors (**ADWIN, KSWIN, Page-Hinkley**) + Hoeffding adaptive trees. Perfect fit: run ADWIN on prediction residuals, raise a dashboard "drift" alarm, trigger retrain. Gives the "live-simulated data" half of the topic a real ML story (adaptivity, not just polling).
- Transport: our 5 s polling is fine for MVP; the vendored `websocket-engineer` skill covers the WS upgrade (push + reconnect + stale-guard — the stale-response guard we added anticipates it). Add a `/ws` endpoint + latency readout when ready; SSE is a simpler middle step.

---

## 6. Prioritized upgrade plan for minip

### Tier 0 — methodology (do first; teacher checks this)
| # | Upgrade | Files touched | Effort |
|---|---|---|---|
| 0.1 | Walk-forward eval (`TimeSeriesSplit`, 5 origins) + per-horizon MAE/RMSE | `backend/model/train.py`, `models/metrics.json` | S |
| 0.2 | Naive baselines: persistence, seasonal-naive (same weekday/hour), HA + skill scores & MASE | `train.py`, dashboard "vs naive" chip | S |
| 0.3 | Classical time-series baselines: SARIMAX/Prophet on one zone (teacher's "time-series model" checkbox) | `backend/model/baselines.py` | M |
| 0.4 | Train-only preprocessing + purge overlapping-label rows near fold boundaries | `train.py`, `generate_dataset.py` | S |

### Tier 1 — data + model realism
| # | Upgrade | Notes | Effort |
|---|---|---|---|
| 1.1 | One real zone (SINPA lot or Melbourne bays, resampled to 15 min) alongside 4 simulated | "sim-to-real" narrative; keeps simulator | M |
| 1.2 | Zone adjacency matrix (distance/similarity) + 1-block STGCN or Graph-WaveNet-style adaptive head | Right-sized per 2026 efficiency findings; runs on RTX 4050 | M–L |
| 1.3 | Incident injection in simulator (accident/closure/weather shock) + local-epicenter scoring | SRGNet lesson; great demo ("what if a crash blocks Zone C?") | S–M |
| 1.4 | Longer LSTM context for 45/60-min heads (SEQ 12→48) or xLSTM cell | TETRA lesson | S |

### Tier 2 — uncertainty + adaptivity (demo differentiators)
| # | Upgrade | Notes | Effort |
|---|---|---|---|
| 2.1 | Conformal intervals (EnbPI-style on validation residuals) + empirical coverage on dashboard | Replaces Gaussian band; guaranteed coverage claim | S–M |
| 2.2 | River ADWIN drift monitor on residuals + drift alarm + one-click retrain endpoint | Vendored skills cover serving story | M |
| 2.3 | Prediction logging via `database/db.py` (already scaffolded) → drift/error-over-time chart | Closes the loop: Predict → Monitor → Retrain | S |

### Tier 3 — product polish
| # | Upgrade | Notes | Effort |
|---|---|---|---|
| 3.1 | WebSocket/SSE push replacing 5 s poll (+ latency readout) | `websocket-engineer` skill vendored | M |
| 3.2 | Admin panel: add events/sales, edit capacity, retrain, model registry/version display | Already in PS scope §34 | M |
| 3.3 | Route/parking recommendation v2 using predicted congestion (PS §24) | Needs tiny road graph between zones | M |

### Explicitly NOT recommended
- Deep GNN stacks (3-block STGCN: 2× cost, <0.5% gain), i.i.d. k-fold CV, more features without ablations, claiming full security assurance (per vendored skills).

## 7. Suggested report narrative (for the teacher)
"Historical + live-simulated data → walk-forward validated time-series/regression models → context-aware features (events/sales/weather) → calibrated uncertainty → drift-monitored live serving → dashboard decisions." Every arrow above is one Tier-0/1/2 row. The literature citations in §1–5 are your related-work section.
