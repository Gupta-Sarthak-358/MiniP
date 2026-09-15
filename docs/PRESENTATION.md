# Real-Time Traffic & Parking Predictor — Presentation Deck
*Present from this file. Images render on GitHub. Numbers trace to `models/*.json`; stories trace to `docs/EXPERIMENTS.md` (E01–E06) and `docs/DECISIONS.md` (D01–D14). Full text: `docs/REPORT.md`.*

---

## Slide 1 — Title
**Real-Time Traffic & Parking Availability Predictor**
*A context-aware, uncertainty-aware, drift-monitored forecasting system — validated on simulated + real sensor data.*
Team · Course · Date

> Say: "We don't just predict parking — we prove the predictions are honest, explain them, and watch the model stay valid live."

---

## Slide 2 — Problem (why current-status isn't enough)
At 5 PM a lot shows 30 free spaces — but a 6 PM concert empties it by 7. Current-status dashboards can't see that coming. We forecast **15/30/45/60 min ahead**, conditioned on time, weather, sales, events and incidents.
Details: `PROJECT_PS.md`.

---

## Slide 3 — System pipeline
```
Real Birmingham sensors + causal simulator
        ↓
Features: time · occupancy · weather · events · sales · incidents
        ↓
Train (RF / XGB-GPU / LSTM) — train-only stats, no peeking
        ↓
Walk-forward test vs 5 baselines (persistence is the one to beat)
        ↓
Serve: FastAPI → dashboard (forecast + bands + heatmap + advice)
        ↓
Monitor: every forecast checked 30 min later → ADWIN drift alarm → retrain
```

> Say: "Data flows one way, time always moves forward, and every claim is measured on unseen data."

---

## Slide 4 — Headline result: the dumb baseline nearly wins
![Walk-forward MAE vs horizon](figures/eval_horizons.png)

**What it means:** "Persistence" = guessing *no change*. At 30 min it's wrong by only ~6 slots — because parking has inertia. Our XGBoost (4.07) and Random Forest (4.31) beat it, and everything else ties or loses. Error grows with horizon for every model, as physics demands.
Numbers: `models/eval_walkforward.json` · Story: E02.

> Say: "We proved we beat 'do nothing' instead of just quoting accuracy — most student projects never check this."

---

## Slide 5 — Who beats "nothing changes"?
![Skill vs persistence at 30 min](figures/baselines_skill.png)

**What it means:** bars above zero = genuinely useful; below = worse than guessing. Only the context-aware ML models clear the bar. Seasonal patterns and plain averages fail — our simulated weeks (like real life) aren't self-similar.
Story: E02 · Decision: D04/D05.

---

## Slide 6 — Ablation: which information helps?
![Ablation over feature groups](figures/ablation_mae.png)

**What it means:** knowing the *current* situation does almost everything (error 26 → 4). Weather/events/sales add ~nothing **on average** — because events are rare and averages hide them. So we asked *when* they help (next slide). Don't hide flat results; explain them.
Numbers: `models/ablation.json` · Story: E03.

> Say: "This is the experiment our assessor asked for — and it surprised us, which is why we kept digging."

---

## Slide 7 — Context pays exactly when conditions are abnormal
![Conditional slices: RF vs persistence](figures/conditional_mae.png)

**What it means:** rush hour → model wins by 35%. Event days → everyone's error doubles (chaos is hard) but we lose by ~2 fewer slots — exactly when users need us. Incident slice is small (n=39, stated openly).
Numbers: `models/slice_analysis.json` · Story: E03b · Decision: D13.

---

## Slide 8 — Honest uncertainty, not decoration
![Conformal calibration](figures/coverage.png)

**What it means:** bands come from 9,600 real past mistakes (90th percentile per horizon), not a formula. Width grows 6→13 slots into the future; reality lands inside exactly 90.0% of the time. The dashboard prints the method + coverage next to the bands.
Numbers: `models/conformal.json` · Story: E04 · Decision: D07.

---

## Slide 9 — The model watches itself go stale
![Residual stream: clean → incident](figures/drift.png)

**What it means:** every forecast is checked 30 min later. A sustained road closure doubles mistakes (6.7 → 13.8); the ADWIN monitor alarms ~23 steps after onset with zero false alarms on clean stretches. Demo: burn in → Inject incident → banner.
Story: E05 · Decision: D08 · Endpoint: `/api/drift`.

---

## Slide 10 — Validated on real sensors, not just simulation
![Real Birmingham validation](figures/real_validation.png)

**What it means:** same experiment on a real Birmingham car park (UCI id=482, UK Open Government Licence): persistence 20.7 → RF 7.8 (**skill +0.62**). Real sensors are ~3× noisier than sim — and the ML edge is ~2× bigger. Same pattern, stronger. Live replay card on the dashboard streams this lot.
Numbers: `models/real_eval.json` · Story: E06 · Decision: D14.

> Say: "Simulated for controlled experiments, validated against a real zone — that answers 'but your data is fake'."

---

## Slide 11 — Failures we kept (viva gold)
- Textbook smoother **blew up** (error 192) on clipped occupancy → diagnosed, replaced (E02a).
- LSTM scored **worse than average** twice (unnormalized targets; wrong data split) → fixed (E01b/c).
- First simulator had **every lot permanently full** (arrival/drain bug) → rebalanced (D10).
- Drift alarms **never fired** (renamed River API + pairing bug) → found, fixed, calibrated (E05).

> Say: "Each failure is logged with evidence in EXPERIMENTS.md — ask us about any of them."

---

## Slide 12 — Live demo (5 min)
1. Cards + 15–60 min forecast with 90% bands (coverage chip). 2. Heatmap. 3. **Inject incident** → spike → recovery. 4. Sustained incident → **drift banner**. 5. Explain bars. 6. Birmingham real-zone card.

---

## Slide 13 — Limits & next steps (honest, specific)
Daytime-only 2016 real data · single real lot · zones learn independently (scoped next step: 1-block STGCN over a zone graph, D09) · in-fold conformal calibration → nested · no auth/rate-limit (demo CORS flagged in code).

---

## Slide 14 — Where everything lives
`docs/REPORT.md` (report) · `docs/EXPERIMENTS.md` (E01–E06 + failures) · `docs/DECISIONS.md` (D01–D14) · `docs/figures/` (these 7 charts) · `models/*.json` (exact numbers) · `tests/` (17 green) · `RESEARCH_UPGRADES.md` (literature) · `PROJECT_PS.md` (spec). Regenerate anything via `README.md` setup (big `*.pkl`/CSV files are git-ignored by design).
