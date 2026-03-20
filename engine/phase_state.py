import json
from pathlib import Path
from datetime import datetime

PHASE_STATE_PATH = Path("data/phase_state.json")

def _default_state():
    return {
        "wake_time": None,
        "nap_credit_minutes": 0,
        "nap_start_time": None,
        "nap_end_time": None
    }

def load_phase_state():
    if not PHASE_STATE_PATH.exists():
        return _default_state()

    try:
        data = json.loads(PHASE_STATE_PATH.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            return _default_state()
    except Exception:
        return _default_state()

    base = _default_state()
    base.update(data)
    return base

def parse_clock(value):
    if not value:
        return None

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%H:%M:%S",
        "%H:%M"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if fmt in ("%H:%M:%S", "%H:%M"):
                now = datetime.now()
                dt = dt.replace(year=now.year, month=now.month, day=now.day)
            return dt
        except Exception:
            pass

    return None

def compute_nap_credit_minutes(state):
    start = parse_clock(state.get("nap_start_time"))
    end = parse_clock(state.get("nap_end_time"))

    if start is None or end is None:
        return int(state.get("nap_credit_minutes", 0) or 0)

    mins = int((end - start).total_seconds() / 60)
    if mins < 0:
        mins = 0
    return mins

def compute_effective_awake_minutes():
    state = load_phase_state()
    wake_dt = parse_clock(state.get("wake_time"))
    if wake_dt is None:
        return None

    nap_credit = compute_nap_credit_minutes(state)
    now = datetime.now()
    delta_minutes = int((now - wake_dt).total_seconds() / 60)
    effective = max(0, delta_minutes - nap_credit)
    return effective
