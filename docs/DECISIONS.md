# Decision Log — Real-Time Traffic & Parking Predictor
Every consequential choice, with date, rationale, rejected alternatives, and evidence.
Format: `## Dnn — title (YYYY-MM-DD)` + Status. Newest at bottom.

## D01 — Use Mnemo .venv (Python 3.11, CUDA, RTX 4050) as the project interpreter (2026-09-15)
Status: accepted. Rationale: torch 2.5.1+cu121 + xgboost 3.2 + sklearn + FastAPI preinstalled; GPU verified (`torch.cuda.is_available()==True`, RTX 4050 Laptop). Rejected: system Python (no xgboost, CPU-only). Evidence: `backend/model/train.py` prints `XGB_device: cuda`; `lstm_train.py` prints `device: cuda (NVIDIA GeForce RTX 4050 Laptop GPU)`.

## D02 — RandomForest (multi-output) as the serving model; XGB-GPU + LSTM as challengers (2026-09-15)
Status: accepted. Rationale: RF gives 15/30/45/60-min multi-output in one fit, fast CPU inference, native uncertainty via tree spread, no GPU needed at serve time. XGB-GPU and LSTM tracked as challengers in `models/metrics.json` / `lstm_metrics.json`. Literature: Perumal et al. 2025 finds RF best on efficiency/runtime for large-scale parking prediction.

## D03 — Selective skill vendoring, no executed installers (2026-09-15)
Status: accepted. Rationale: `install.ps1` bulk-installs 175+ skills into global config (bloat + trust surface). Vendored 12/175+ skills project-local under `.opencode/skills/` after reading each fully. All guidance-only, no payloads. Record: `.opencode/skills/SKILLS.md`.

## D04 — Walk-forward (rolling-origin) evaluation replaces single static split (2026-09-15)
Status: accepted. Rationale: static 80/20 can reverse model rankings (Mar 2026 PM10 study: XGBoost best static, loses to SARIMA/persistence under rolling origin). Protocol: expanding-window origins, strictly past→future, train-only preprocessing, purge of overlapping-label rows. Implements RESEARCH_UPGRADES Tier 0.1/0.4.

## D05 — Mandatory naive + classical baselines (2026-09-15)
Status: accepted. Rationale: point metrics are meaningless without persistence / seasonal-naive / historical-average and skill scores; teacher topic says "time-series/regression model", so SARIMAX/Holt-Winters baselines are required checkboxes. Implements Tier 0.2/0.3.

## D06 — Incident injection as first-class simulator feature (2026-09-15)
Status: accepted. Rationale: literature (SRGNet 2026) shows SOTA degrades +116–230% under incidents and global RMSE hides epicenter failure. Simulator + dataset gain `is_incident`/`incident_severity`; dashboard demo + local-epicenter scoring. Implements Tier 1.3.

## D07 — Conformal (EnbPI-style) intervals replace Gaussian tree-std bands (2026-09-15)
Status: accepted. Rationale: `±1.96·tree_std` assumes Gaussian errors — uncalibrated. Validation-residual quantiles give intervals with measurable empirical coverage, reported on dashboard. Implements Tier 2.1.

## D08 — River ADWIN drift monitoring on prediction residuals (2026-09-15)
Status: accepted. Rationale: turns "continuous inference" into a monitored online loop (predict → residual → ADWIN → alarm → retrain). `river` 0.26.1 installed into Mnemo venv. Implements Tier 2.2.

## D09 — 1-block STGCN ceiling for spatial modeling; no deep GNN stacks (2026-09-15)
Status: accepted (deferred build). Rationale: June 2026 study — 1-block ≈ 2-block STGCN (≤1.8% loss, ~38% lower latency); 3-block ≥2× cost for <0.5%. Spatial upgrade stays right-sized. Tier 1.2, scheduled after ablations confirm spatial signal value.

## D10 — Proportional-turnover parking dynamics after ratchet diagnosis (2026-09-15)
Status: accepted. Evidence: occupancy audit showed ALL zones pegged at ~99% (available ≈ 0–5) — departures (cap×0.045) couldn't balance arrivals, so lots filled in ~30 steps and never drained; parking prediction was trivial and the dashboard dead. Fix: departures ∝ occupancy (0.16 day / 0.08 night / 0.26 station short-stay ≈ 1.5 h avg stay). Post-fix: mall 75, office 81, residential 49, stadium 53, station 84 (ranges 25–100%). Train↔serve parity: identical formula in `generate_dataset.py` and `live_data.py`.

## D11 — SES replaces seasonal Holt-Winters as classical baseline (2026-09-15)
Status: accepted. Evidence: E02a — seasonal HW mis-specified for event-driven clipped series (MAE 192 → 7.7 after fixes, still broken). SES (adaptive persistence) is the honest classical comparator for inertia-dominated data. Kept AR(24) as the autoregressive classical rep.

## D12 — LSTM: standardized targets + per-location splits (2026-09-15)
Status: accepted. Evidence: E01b (raw targets stall gradients, R² −0.12) and E01c (global cut = cross-site test on station). Both fixes in `lstm_train.py`; final val MAE 7.9 / R² 0.994. Failure modes kept in log as methodology evidence.

## D13 — Conditional-slice analysis alongside global ablation (2026-09-15)
Status: accepted. Rationale: global MAE averages rare events away (E03: context ≈ +0.00 globally). Slices (event/incident/sale/peak) show where context pays (peak +0.35 skill). Both reported; neither hidden. Script: `backend/model/slice_analysis.py`.

## D14 — Real zone = Birmingham NCP Market lot, replay + offline validation (2026-09-15)Status: accepted. Candidates: SINPA/HF (research-grade but windowed npz, no absolute timestamps — timeline reconstruction unreliable; 593 MB val file downloaded, inspected, then deleted; cited, not integrated), SFpark/Dataverse (403 on API — dropped), LA Express Park (300–600 MB/month — oversized), Melbourne live feed (snapshot-only history — dropped). Winner: **UCI id=482 Parking Birmingham** (same data as the Kaggle copy, direct no-auth download, UK OGL, 1.4 MB): lot BHMBCCMKT01, cap 577, full 73-day coverage, occupancy 2–573 (highest variance, CV 0.61). Sensor glitches (negative / >105% readings) clipped and reported. Scope (bounded): replay endpoint + dashboard card through the same API contract (persistence forecast, honestly labeled) + offline walk-forward E06. NOT served by the sim-trained model (domain shift by construction). Caveats stated: daytime-only (08:00–16:30), 2016, ~30-min native grid resampled to 15-min.

## D15 - Build new dashboard on the stitch shell, keep live behavior (2026-09-15)
Status: accepted. Rationale: designer delivered full ATC console matching our tokens/spec. Rebuilt frontend/index.html on their verbatim shell (tokens, tiers, components) and wired every region to real APIs via build_frontend*.py scripts (anchors asserted, kept in Temp). Chart.js replaces static SVG so data stays live; mock fictions (facility names, MAE 1.84, UTC clock, external logo) replaced with measured values. Mobile: single responsive file (sidebar hidden <lg), matching the mobile mock stacking.
