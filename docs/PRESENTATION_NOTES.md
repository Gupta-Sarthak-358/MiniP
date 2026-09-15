# Speaker Script — what to say per slide (≈10 min total)
*Companion to `docs/PRESENTATION.md` (the shown deck). Know the bold facts cold; everything else is backup.*

## Slide 1 — Title (30 s)
Say: "We built a traffic and parking forecaster — but the project isn't the forecast, it's the proof around it: honest measurement, explanations, live monitoring, and validation on real sensors."
Know: teacher's topic was dashboard + time-series/regression on historical + live-simulated data. We cover every word of it.

## Slide 2 — Problem (45 s)
Say: "Current-status dashboards report the present. At 5 PM, 30 free spaces looks fine — but the 6 PM concert empties the lot by 7. We predict 15 to 60 minutes ahead, conditioned on events, sales, weather and incidents."
Transition: "Here's how the system is put together."

## Slide 3 — Pipeline (60 s)
Say: "Data flows one way, time always moves forward, and every claim is measured on unseen data. Note the last box — most projects stop at 'serve'; ours keeps checking itself live."
Know: 5 zones + Birmingham replay; features = time, occupancy, weather, events, sales, incidents; serving model RF-150, challengers XGB/LSTM on CUDA.

## Slide 4 — Data (30 s)
Say: "43,000 rows of causal simulation for controlled experiments, plus a real Birmingham car park for credibility. Parking follows realistic turnover — lots breathe between 25 and 100%, they don't sit pegged at full."
Backup: cap 577, Oct–Dec 2016, resampled to 15-min; sensor glitches clipped and reported.

## Slide 5 — Protocol (60 s)
Say: "Static train-test splits can reverse model rankings — that's a published 2026 finding — so we never use them. Four expanding windows, past trains future, imputation fit on train only, labels near the boundary purged."
If asked "what's purging?": "A training row whose 60-minute label reaches into the test block is deleted — otherwise the model trains on answers."

## Slide 6 — Headline result (90 s, the core)
Say: "The dumbest baseline — guessing no change — misses by only 6 slots, because parking has inertia. Our XGBoost misses by 4. Everything else ties or loses. That gap, +0.32 skill, is the honest win. And on traffic, which actually moves, Random Forest cuts error 42%."
Know: persistence 5.99, XGB 4.07, RF 4.31, vehicles 57.2→32.9. If pressed on LSTM: static val MAE 7.9, R² 0.994 — temporal evidence, challenger status.

## Slide 7 — Skill chart (30 s)
Say: "Only context-aware ML clears zero. Weekly-seasonal logic fails — real weeks aren't self-similar. A negative result we kept instead of hiding."

## Slide 8 — Ablation (45 s)
Say: "Knowing the current situation does almost everything. Weather and events add nothing on average — because events are rare and averages hide them. So we asked *when* they help."
Transition: "That's the next slide, and it's the most interesting one."

## Slide 9 — Slices (60 s)
Say: "Rush hour: 35% better than guessing. Event days: chaos doubles everyone's error, but we lose by two fewer slots — exactly when users need us. Incident sample is small, n=39, and we say so openly."
Know: peak 4.23/6.46, event 7.40/9.26, incident 7.35/8.67, sale 5.75/6.57.

## Slide 10 — Uncertainty (45 s)
Say: "No Gaussian assumptions. We measured 9,600 real past mistakes and took the 90th percentile per horizon — 6 to 13 slots widening into the future — then verified reality lands inside exactly 90% of the time. The dashboard prints the coverage next to the bands."

## Slide 11 — Drift (45 s)
Say: "Every forecast is checked 30 minutes later. A sustained closure doubles our mistakes, and the monitor alarms 23 steps in with zero false alarms on clean stretches. Then the operator retrains — that's the loop most projects never build."

## Slide 12 — Real validation (45 s)
Say: "Same experiment on real Birmingham sensors: persistence 20.7, our model 7.8 — skill +0.62. Real data is three times noisier, and our edge is twice as big. Simulated for control, validated for credibility."

## Slide 13 — Demo handoff (live, 5 min)
"Now the system itself." Follow `docs/DEMO_AND_VIVA.md` §2 minute-by-minute. If anything glitches live: "The report has the frozen numbers; the dashboard is live and occasionally honest about it."

## Slide 14 — Failures (60 s, viva gold — linger here)
Say: "A textbook smoother blew up to 192 error on clipped occupancy. The neural net scored worse than guessing average — twice. Our first simulator jammed every lot at 99% full. And the drift alarms silently never fired for a week due to a renamed API. Each is logged with evidence — ask us about any of them."
This slide answers "what went wrong" before they ask. Confidence, not apology.

## Slide 15 — Limits + artifacts (30 s, close)
Say: "Daytime-only 2016 real data, one real lot, zones still learn independently — the scoped next step is a 1-block graph network. Everything is reproducible from the repo: report, logs, figures, 18 green tests."
End: "Questions — the numbers behind any slide are one file away."
