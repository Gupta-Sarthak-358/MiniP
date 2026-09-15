# Demo + Viva Pack (share with the group)
**Tomorrow's demo runs from the dashboard (`.\start.ps1` → http://127.0.0.1:8000). Everything below maps to files in this repo.**

## 1. One-line pitch (memorize this)
> "A context-aware traffic and parking forecaster that proves its accuracy honestly, explains its predictions, watches itself go stale, and validates the same pattern on real sensors."

## 2. Five-minute demo script
| Min | Do | Say |
|---|---|---|
| 0–1 | Hero strip + charts on Stadium | "Live state plus 15–60 min forecasts with measured 90% bands — coverage reads 0.90 on screen." |
| 1–2 | Step +1h twice, switch zone to Mall | "Every control re-forecasts; the sale context reprices the mall." |
| 2–3 | **SIM INJECT** on Stadium | "Accident injected — alerts, charts, table move; recovery visible over steps." |
| 3–4 | Routing panel | "Ranked alternatives with predicted availability — this is the reroute decision." |
| 4–5 | Birmingham card + Factors bars | "Same pipeline validated on real 2016 sensors (+0.62 skill); bars show *why* — current state dominates." |
| Bonus | `/docs` in browser | "Auto-generated API contract — 13 endpoints, all validated." |

## 3. Reading list (split among members, 30 min each)
1. **Everyone:** `docs/PRESENTATION.md` (14 slides, the whole story).
2. **ML member:** `docs/EXPERIMENTS.md` E02–E03 + `models/eval_walkforward.json` + `models/ablation.json`.
3. **Systems member:** `backend/app.py` + `backend/monitor/drift.py` + `tests/` (18 tests, run them).
4. **Data member:** `backend/simulator/generate_dataset.py` + `backend/model/real_zone.py` + `data/real/`.
5. ** viva lead:** `docs/DECISIONS.md` (D01–D16) + failure logs E02a/E01b-c + §5 below.

## 4. Tonight checklist
- [ ] Fresh clone works: generate → train → `pytest` 18 green → `.\start.ps1` opens dashboard.
- [ ] Each member runs the 5-min demo once without notes.
- [ ] Decide who answers which viva section (§5).

## 5. Likely viva questions + answers
**"Why not just report accuracy?"** — We report skill vs persistence (+0.32 XGB, +0.28 RF). Parking has inertia; "no change" scores 5.99 MAE, so raw accuracy alone would be meaningless. (E02)
**"Why walk-forward instead of a single split?"** — Static splits can reverse model rankings (2026 literature). Four expanding origins, past→future only, train-only stats, purged overlapping labels. (D04)
**"Which features matter?"** — Globally, current state (26→4 MAE). Context pays when abnormal: peak-hour skill +0.35, event days −1.87 slots absolute. (E03/E03b)
**"What do the bands mean?"** — 90th percentile of 9,600 walk-forward residuals per horizon; verified 0.900 coverage. Not a Gaussian assumption. (E04)
**"How do you know the model stays valid live?"** — Every +30m forecast is paired with truth; River ADWIN alarms on residual shifts (calibrated: 23-step delay, 0 false alarms). (E05)
**"Simulated data — so it's fake?"** — Simulated for controlled experiments; same walk-forward protocol on real Birmingham sensors shows the same pattern, stronger (+0.62). (E06/D14)
**"What failed?"** — HW smoother blew up on clipped occupancy (E02a); LSTM collapsed twice before target normalization + per-location splits (E01b/c); first simulator pegged lots at 99% (D10). All logged with evidence.
**"Why no GNN/Transformer?"** — 2026 efficiency studies show small models match big ones for this regime; 1-block STGCN is scoped future work (D09). Right-sized beats buzzword-sized.
**"Is it secure/deployable?"** — Validated inputs (404/422), demo CORS flagged in code, no secrets in repo; auth + rate-limit listed as deployment work, not claimed. (vendored security-auditor)

## 6. Anything still open (honest future scope, from RESEARCH_UPGRADES.md)
One more real zone · 1-block STGCN over zone adjacency · sim→real transfer test · nested conformal calibration · WebSocket push · admin panel. Nothing here blocks the grade; each is a named next step.
