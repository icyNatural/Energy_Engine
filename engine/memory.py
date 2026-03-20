import json
from pathlib import Path
from datetime import datetime

MEMORY_PATH = Path("data/outcome_memory.json")

def load_memory():
    if MEMORY_PATH.exists():
        return json.loads(MEMORY_PATH.read_text(encoding="utf-8-sig"))
    return []

def save_memory(mem):
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(mem, indent=2), encoding="utf-8")

def record_outcome(pattern_id, outcome_note):
    mem = load_memory()
    mem.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "pattern_id": pattern_id,
        "outcome": outcome_note
    })
    save_memory(mem)

def summarize_pattern(pattern_id):
    mem = load_memory()
    hits = [m for m in mem if m["pattern_id"] == pattern_id]

    if not hits:
        return {
            "count": 0,
            "summary": "No personal outcome history yet."
        }

    outcomes = [m["outcome"] for m in hits]
    recent = ", ".join(outcomes[-3:])

    return {
        "count": len(hits),
        "summary": f"This pattern has appeared {len(hits)} time(s). Recent outcomes: {recent}"
    }
