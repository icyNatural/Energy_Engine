from datetime import datetime
from pathlib import Path
import json


def load_word_bank(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _pick(preferred, options, fallback):
    for item in preferred:
        if item in options:
            return item
    return options[0] if options else fallback


def suggest_day_mode(word_bank, recovery_band, energy_band, phase):
    states = word_bank.get("states", [])
    virtues = word_bank.get("virtues", [])
    principles = word_bank.get("principles", [])
    intentions = word_bank.get("intentions", [])

    if recovery_band == "restored" and energy_band == "open":
        preferred_state = [phase, "Flow", "Clarity", "Presence"]
        preferred_virtue = ["Discipline", "Courage", "Integrity"]
        preferred_principle = ["Precision", "Consistency", "Truth"]
        preferred_intention = ["Execute", "Build", "Learn"]
        note = "System appears more open today. Favor clear forward motion."
    elif recovery_band == "steady" and energy_band in ("open", "usable"):
        preferred_state = [phase, "Focus", "Calm", "Flow"]
        preferred_virtue = ["Discipline", "Patience", "Integrity"]
        preferred_principle = ["Consistency", "Precision", "Simplicity"]
        preferred_intention = ["Execute", "Build", "Protect"]
        note = "System looks usable and stable. Favor smooth, sustainable output."
    else:
        preferred_state = [phase, "Calm", "Presence", "Focus"]
        preferred_virtue = ["Patience", "Discipline", "Integrity"]
        preferred_principle = ["Simplicity", "Consistency", "Truth"]
        preferred_intention = ["Protect", "Learn", "Execute"]
        note = "System appears more regenerative today. Favor lower friction and cleaner pacing."

    state = _pick(preferred_state, states, phase)
    virtue = _pick(preferred_virtue, virtues, "Discipline")
    principle = _pick(preferred_principle, principles, "Precision")
    intention = _pick(preferred_intention, intentions, "Execute")

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "recovery_band": recovery_band,
        "energy_band": energy_band,
        "phase": phase,
        "note": note,
        "suggested_mode": {
            "state": state,
            "virtue": virtue,
            "principle": principle,
            "intention": intention
        }
    }


def save_day_mode(path: Path, mode_entry: dict):
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    existing.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "starter": mode_entry,
        "reflection": None
    })

    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def save_reflection(path: Path, reflection: dict):
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    if not existing:
        existing.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "starter": None,
            "reflection": reflection
        })
    else:
        existing[-1]["reflection"] = reflection

    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
