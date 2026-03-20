# -*- coding: utf-8 -*-
import json
from pathlib import Path

p = Path("outputs/dashboard.json")

def fmt_minutes(total):
    if total is None:
        return "Not set"
    h = total // 60
    m = total % 60
    return f"{h}h {m}m"

def show():
    if not p.exists():
        print("Run report first.")
        return

    d = json.loads(p.read_text(encoding="utf-8"))

    r = d.get("recovery", {})
    e = d.get("energy", {})
    ph = d.get("phase", {})
    pat = d.get("patterns", {})
    t = d.get("timing", {})

    print("\n==============================")
    print("HOME")
    print("==============================")
    print("Phase:", ph.get("phase"))
    print("Energy:", e.get("state_label"))
    print("Guidance:", e.get("guidance"))

    print("\nActions")
    print("- .\\details.ps1")
    print("- .\\hub.ps1")

    print("\n==============================")
    print("TIMING")
    print("==============================")
    print("Wake time:", t.get("wake_time") or "Not set")
    print("Nap start:", t.get("nap_start_time") or "Not set")
    print("Nap end:", t.get("nap_end_time") or "Not set")
    print("Nap credit:", str(t.get("nap_credit_minutes", 0)) + " min")
    print("Effective awake:", fmt_minutes(t.get("effective_awake_minutes")))

    print("\n==============================")
    print("RECOVERY")
    print("==============================")
    print("State:", r.get("state_label"))
    print("Meaning:", r.get("meaning"))
    print("Guidance:", r.get("guidance"))

    print("\nSignals")
    for s in r.get("drivers", []):
        print("-", s)

    print("\n==============================")
    print("PATTERN WATCH")
    print("==============================")
    print(pat.get("summary"))

    patterns = pat.get("patterns", [])
    if patterns:
        for item in patterns:
            print("\n*", item.get("title"))
            print("  Pattern Presence:", item.get("pattern_presence_label"))
            print("  Meaning:", item.get("meaning"))
            print("  Note:", item.get("note"))
            print("  Detail:", item.get("detail"))
    else:
        print("No active patterns.")

    memory = pat.get("memory", [])
    if memory:
        print("\nMemory")
        for m in memory:
            print("-", m.get("summary"))

    print("\n==============================")
    print("PHASE DETAIL")
    print("==============================")
    print("Condition:", ph.get("condition"))
    print("Sense:", ph.get("sense"))
    print("Quote:", ph.get("quote"))

show()
