# Real-Time Traffic & Parking Availability Predictor

Context-aware ML system forecasting congestion + parking (15/30/45/60 min) from time, location, weather, holidays, sales, events. See `PROJECT_PS.md` for full PS. Full report: `docs/REPORT.md`. Slide deck: `docs/PRESENTATION.md`.

## Fresh-clone setup (teammates — read this first)

Big files (`data/historical.csv`, raw `models/*.pkl`) are git-ignored and **regenerated** — never committed (GitHub blocks >100 MB). Small data, docs, metrics and figures ARE committed. **Trained models ship as split zips** (`models/models_rf_*.zip`, `models_rest.zip`, each <100 MB) which `predict.py` loads transparently — zero setup. **The generated dataset ships as `data/historical.csv.zip`** (1.2 MB) so teammates can skip generation too (unzip or just rerun the 40 s generator). Use `PY` = your Python (Mnemo `.venv` if you have it, else any 3.11 + `pip install -r requirements.txt`):

```powershell
PY backend\simulator\generate_dataset.py   # ~40 s  -> data/historical.csv
PY backend\model\train.py                  # ~5-10 min -> models/*.pkl + metrics
PY -m backend.model.real_zone              # ~2 min -> real-zone validation artifacts
PY -m pytest tests/ -q                     # 17 tests, must all pass
PY -m uvicorn backend.app:app --reload --port 8000
# optional: PY backend\model\lstm_train.py (needs torch/CUDA for speed)
```

Open http://127.0.0.1:8000 — or start from the deck: `docs/PRESENTATION.md`.

## Structure

```
backend/
  app.py                 FastAPI + APIs + serves frontend
  model/train.py         RF + Linear + XGB-GPU training (train-only stats)
  model/evaluate.py      walk-forward + baselines + conformal calibration
  model/ablation.py      cumulative feature-group ablations
  model/slice_analysis.py conditional slices (when context pays)
  model/lstm_train.py    CUDA LSTM challenger (optional)
  model/real_zone.py     Birmingham real-zone build + validation
  model/predict.py       serving (conformal intervals + explanations)
  simulator/generate_dataset.py  causal 90-day dataset (+incidents)
  simulator/live_data.py stateful live sim (+incident injection)
  simulator/real_replay.py Birmingham sensor replay feed
  monitor/drift.py       River ADWIN residual monitoring
frontend/index.html      dashboard (forecast, heatmap, incidents, drift, real zone)
docs/                    REPORT, PRESENTATION, EXPERIMENTS, DECISIONS, figures/
tests/                   17 regression tests
```

## APIs

- `GET /api/health`
- `GET /api/locations`
- `GET /api/current-status?location=mall` (404 on unknown id)
- `GET /api/prediction?location=mall`
- `GET /api/history?location=mall&points=40` (1-300)
- `GET /api/events`
- `GET /api/recommendation`
- `GET /api/explain?location=mall`
- `POST /api/step?steps=1` (1-8) advance simulator
- `POST /api/incident` inject accident/closure/storm_shock demo
- `GET /api/drift` ADWIN monitor status · `POST /api/drift/reset`
- `GET /api/real-zone` Birmingham replay + persistence forecast

## Tests

```powershell
& "C:\Users\satvi\Desktop\Mnemo\.venv\Scripts\python.exe" -m pytest tests/ -q
```

18 tests: `test_api.py` (success / 404-validation / clamp / step-persistence / recommendation),
`test_feature_parity.py` (training-serving parity + JSON-safe contract),
`test_ops.py` (incident inject, drift status, conformal interval contract, metrics endpoint),
`test_real.py` (replay contract + real-eval artifact).

## Evaluation & report (Tier 0 + ablations, all reproducible)

```powershell
& "C:\Users\satvi\Desktop\Mnemo\.venv\Scripts\python.exe" -m backend.model.evaluate   # walk-forward + baselines + conformal
& "C:\Users\satvi\Desktop\Mnemo\.venv\Scripts\python.exe" -m backend.model.ablation   # feature-group ablations
& "C:\Users\satvi\Desktop\Mnemo\.venv\Scripts\python.exe" -m backend.model.slice_analysis  # conditional slices
& "C:\Users\satvi\Desktop\Mnemo\.venv\Scripts\python.exe" -m backend.model.real_zone  # Birmingham real-zone validation
```

Read: `docs/REPORT.md` (full report) · `docs/PRESENTATION.md` (slide deck) ·
`docs/FRONTEND_SPEC.md` (designer handoff for the dashboard redesign) ·
`docs/EXPERIMENTS.md` (E01–E06 + failure logs) · `docs/DECISIONS.md` (D01–D14) ·
`docs/figures/` (7 charts) · `RESEARCH_UPGRADES.md` (lit review → plan).

## Skills (`.opencode/skills/`, vendored + vetted 2026-09-15)

12 selective excerpts, project-local (no global install, no executed installers).
Sources: jshsakura/awesome-opencode-skills (fastapi, frontend, ui, a11y, websocket, security, python, ml, tests)
+ finfin/awesome-frontend-skills (frontend-ui-engineering, ui-animation).
Security: every SKILL.md read in full before vendoring — guidance-only, no executable payloads,
no exfiltration, no prompt-injection markers. `install.ps1|py` reviewed, never run.
See `.opencode/skills/SKILLS.md`.
