from datetime import datetime
from config import OUTCOME_MEMORY_PATH
from engine.storage import load_list, save_json


def load_outcomes():
    return load_list(OUTCOME_MEMORY_PATH)


def save_outcomes(rows):
    save_json(OUTCOME_MEMORY_PATH, rows)


def record_outcome(date, reflection, patterns, recovery_band, energy_band, phase):
    rows = load_outcomes()

    entry = {
        "date": date,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "recovery_band": recovery_band,
        "energy_band": energy_band,
        "phase": phase,
        "patterns": [p.get("id") for p in patterns if isinstance(p, dict)],
        "overall_feeling": reflection.get("overall_feeling"),
        "matched_mode": reflection.get("matched_mode"),
        "workload_high": reflection.get("workload_high"),
        "illness_watch": reflection.get("illness_watch"),
        "rebounded_next_day": reflection.get("rebounded_next_day"),
        "caffeine_masked": reflection.get("caffeine_masked"),
        "notes": reflection.get("notes", "")
    }

    rows = [r for r in rows if r.get("date") != date]
    rows.append(entry)
    rows = sorted(rows, key=lambda x: x.get("date", ""))

    save_outcomes(rows)
    return entry


def summarize_pattern_memory(pattern_id):
    rows = load_outcomes()
    matched = [r for r in rows if pattern_id in r.get("patterns", [])]

    if not matched:
        return {
            "pattern_id": pattern_id,
            "count": 0,
            "summary": "No prior outcome memory for this pattern."
        }

    low_capacity = sum(1 for r in matched if r.get("overall_feeling") in ["heavy", "foggy", "drained", "low"])
    illness_watch = sum(1 for r in matched if r.get("illness_watch") is True)
    rebound = sum(1 for r in matched if r.get("rebounded_next_day") is True)

    parts = [f"{len(matched)} prior occurrence(s)"]
    if low_capacity:
        parts.append(f"{low_capacity} linked with lower-capacity feeling")
    if illness_watch:
        parts.append(f"{illness_watch} linked with illness-watch")
    if rebound:
        parts.append(f"{rebound} followed by rebound next day")

    return {
        "pattern_id": pattern_id,
        "count": len(matched),
        "summary": "; ".join(parts) + "."
    }
