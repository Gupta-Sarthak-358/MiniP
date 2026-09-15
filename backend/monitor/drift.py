"""Online drift monitoring (D08): River ADWIN over per-location |residual| stream.
Pairs each +30min prediction with the ground truth that arrives 2 steps later.
Not a research-grade detector deployment — an honest monitored-serving loop demo:
predict -> residual -> ADWIN -> alarm -> operator retrains.
"""
from collections import deque, defaultdict
from river.drift import ADWIN

_predicted = defaultdict(deque)   # loc -> deque[(due_step, pred30)]
_detectors = {}
_stats = defaultdict(lambda: {"n": 0, "mae_num": 0.0, "drift": False, "changes": 0})
_clock = {"step": 0}

def _det(loc):
    if loc not in _detectors:
        _detectors[loc] = ADWIN()
    return _detectors[loc]

def _fired(det):
    # River >=0.15 renamed change_detected -> drift_detected; accept both.
    for attr in ("drift_detected", "change_detected"):
        if hasattr(det, attr):
            v = getattr(det, attr)
            return bool(v() if callable(v) else v)
    return False

def note_prediction(loc, pred30):
    """Call each step with the fresh +30min forecast (due in 2 steps)."""
    _predicted[loc].append((_clock["step"] + 2, float(pred30)))
    while len(_predicted[loc]) > 4:
        _predicted[loc].popleft()

def note_actual(loc, actual):
    """Call each step with the current ground truth; pairs with due predictions."""
    dq = _predicted[loc]
    while dq and dq[0][0] <= _clock["step"]:
        _, p = dq.popleft()
        err = abs(float(actual) - p)
        d = _det(loc)
        d.update(err)
        s = _stats[loc]
        s["n"] += 1
        s["mae_num"] += err
        if _fired(d):
            s["drift"] = True
            s["changes"] += 1

def tick():
    _clock["step"] += 1

WARMUP = 20  # pairings before an alarm is surfaced (cold-start guard)

def status():
    return {loc: {"n_paired": s["n"],
                  "recent_mae": round(s["mae_num"] / s["n"], 2) if s["n"] else None,
                  "drift": bool(s["drift"] and s["n"] >= WARMUP),
                  "drift_raw": s["drift"], "drift_events": s["changes"]}
            for loc, s in _stats.items()}

def reset(loc=None):
    if loc is None:
        _detectors.clear(); _stats.clear(); _predicted.clear()
    else:
        _detectors.pop(loc, None); _stats.pop(loc, None); _predicted.pop(loc, None)
