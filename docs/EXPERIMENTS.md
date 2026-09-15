# Experiment Log — model findings, tables, figures
Append-only. Each entry: config → protocol → results → figure → takeaway.
Static-split results (E01) predate walk-forward adoption (see D04); kept for the report's "before/after methodology" story.

## E01 — Static 80/20 split: Linear vs RF vs XGB-GPU vs LSTM (2026-09-15, Mnemo venv, CUDA)
- Data: `data/historical.csv`, 43,180 rows, 5 zones, 15-min steps, targets 15/30/45/60.
- Protocol: single chronological split (WEAK — see D04).
- `available_30`: Linear MAE 0.468 / R² 0.481 · RF MAE 0.384 / R² 0.560 · **XGB-cuda MAE 0.360 / R² 0.608** · **LSTM-cuda MAE 0.119 / RMSE 1.293 / R² 0.872**.
- `vehicles_30`: Linear MAE 54.7 / R² 0.834 · RF MAE 33.1 / R² 0.940.
- Top feature: `available` (importance 0.995) — persistence dominates short-horizon parking (expected; motivates D05 naive baselines).
- Artifacts: `models/metrics.json`, `models/lstm_metrics.json`.

## E02 — Walk-forward evaluation + baselines (2026-09-15; figures: eval_horizons.png, baselines_skill.png)
- Protocol (D04): 4 expanding origins × 5-day test blocks, train-only medians, purge of train rows whose 60-min label overlaps the test block. Artifacts: `models/eval_walkforward.json`.
- `available_30` walk-forward MAE / skill-vs-persistence: Persistence **5.99** (ref) · SES 5.99 (0.00) · Linear 5.78 (+0.04) · AR(24) 6.79 (−0.13) · **RF-100 4.31 (+0.28)** · **XGB-300-cuda 4.07 (+0.32)** · HistAvg 26.3 · Seasonal-naive(7d) 30.3.
- `vehicles_30`: Persistence 57.2 · HistAvg 37.1 (+0.35) · AR(24) 60.1 · **RF 32.9 (+0.42)**. Traffic is strongly learnable; parking short-horizon is inertia-dominated — ML's edge concentrates where dynamics move (see E03 slices).
- Takeaway: the ONLY models beating persistence on parking are the context-aware ML ones; classical smoothers tie it, weekly-seasonal logic fails (sim weeks aren't self-similar — honest negative result).

## E02a — FAILURE LOG: unbounded smoothers on clipped occupancy (kept deliberately)
- Attempt 1: Holt-Winters additive trend+seasonal → MAE **192** (trend extrapolates through the 0/capacity boundary).
- Attempt 2: damped trend + clip + purge-gap alignment → MAE 7.7 flat (level diverges at the boundary pile-up).
- Diagnosis: pre-rebalance data had zones pegged at ~99% occupancy; HW level went negative (−23) while truth clipped at 0.
- Resolution: (1) rebalanced simulator turnover (D10) so occupancy spans 25–100%; (2) classical slot filled by level-only SES (adaptive persistence, MAE 5.99). Lesson recorded in `ses_forecast` docstring.

## E01b/E01c — FAILURE LOG: LSTM training (kept deliberately)
- E01b: raw-scale targets → gradients stall, val R² **−0.12**. Fix: standardize targets + grad clip (D12).
- E01c: global 80/20 cut tested on an entirely unseen LOCATION (station) — a cross-site task, not forecasting. Fix: per-location 80/20 then pool (D12). Final LSTM-cuda: val MAE 7.9 slots, R² 0.994.

## E03 — Ablation over cumulative feature groups, RF-80 walk-forward (figure: ablation_mae.png)
- `available_30` MAE: time-only 26.35 → +state **4.42** (Δ−21.9) → +weather 4.44 → +event 4.45 → +sale/hol 4.42 → +incident 4.43.
- `vehicles_30`: 37.1 → 33.9 → 33.9 → 33.5 → 33.3 → 33.2. `available_60`: 26.3 → 6.32 → … → 6.26.
- Headline: current-state features do ~everything GLOBALLY; context adds ~nothing on average — because events are rare. The assessor's "0.03%" warning, confirmed empirically…
- …BUT conditional slices (E03b, `models/slice_analysis.json`, figure conditional_mae.png) show WHERE context pays: peak-hour skill **+0.35** (4.23 vs 6.46), event-day absolute gain **1.87 slots** (7.40 vs 9.26), incident +0.15 (n=39, small sample — stated, not hidden), sale-day +0.12. Context pays exactly when conditions are abnormal.

## E04 — Conformal interval calibration (D07; `models/conformal.json`)
- EnbPI-style: q90 of RF walk-forward residuals per horizon. q90 slots: 15→**6.2**, 30→**9.0**, 45→**11.3**, 60→**13.4**; empirical coverage **0.900** at all horizons (n=9600 each; in-fold calibration — stated caveat, nested calibration is follow-up).
- Dashboard now reports method + coverage instead of uncalibrated Gaussian bands. Figure: coverage.png.

## E05 — Drift-monitor calibration (D08; figure: drift.png)- Offline replay, stadium: 40 clean steps → sustained sev-3 closure. Residual MAE **6.7 → 13.8** (2× degradation — incidents genuinely blindside the model).
- ADWIN sweep: detection delay **23 steps** after onset at delta 0.002–0.1; clean-stretch false alarms **0** at delta ≤ 0.01. Operating point: delta=0.002 + 20-pairing warmup (cold-start guard).
- Debugging trail (kept): River 0.26 renamed `change_detected`→`drift_detected` (silent AttributeError swallowed by serving try/except — found because alarms never fired); per-sub-step pairing fix (multi-step calls paired only 1 residual); warmup guard added after a day-boundary regime change caused a (correct but premature) alarm.
- Demo protocol: burn in ~30 clean steps → Inject incident → alarm in ~25 steps (~2 min on auto-5s).

## E06 � Sim-to-real check on Birmingham sensors (D14; figure: real_validation.png)
- Real series: BHMBCCMKT01, cap 577, resampled to 15-min (data/real/bham_replay.csv); 3 walk-forward folds x 7 days; reduced features (time + occupancy + lags). Artifacts: models/real_eval.json.
- available_30 MAE: persistence **20.67** | HistAvg 25.41 | **RF 7.81 (skill +0.62)**. Real sensors are ~3x noisier than sim � and ML's edge is ~2x bigger (+0.62 vs +0.32). Same pattern as simulation, stronger.
- Live: /api/real-zone replay + dashboard card (persistence forecast, labeled). Sim-trained model deliberately NOT applied (domain shift); cross-test is scheduled follow-up.

## E07 - Stitch ATC design implemented and wired live (figure: stitch screen.png)
- Source: stitch_traffic_and_parking_dashboard/ (desktop+mobile code.html, token sheet, CSS vars, PRD brief). Implemented as frontend/index.html on the verbatim design shell: same tokens, layout tiers, alert lane, hero pillars, SHAP panel, routing list, saturation grid, replay card, footer.
- Honesty adjustments vs mock: static SVGs replaced with live Chart.js (same styling); fictional facility names/values replaced with real API data; MAE chip + footer calibration served by new /api/metrics (real walk-forward numbers); SHAP relabeled RF importance (we are not SHAP); horizon toggles switch hero-03 focus; external logo URL replaced with local inline SVG; sidebar responsive-hidden below lg.
- Verified: node --check on both inline scripts, page serves 200 with all hooks, 18/18 pytest green.
