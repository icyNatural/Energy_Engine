from pathlib import Path
import json
from engine.storage import load_list, save_json
from engine.recovery import build_recovery_report
from engine.energy import build_energy_report
from engine.phase import phase_from_effective_awake
from engine.patterns import build_pattern_report
from engine.phase_state import load_phase_state, compute_effective_awake_minutes

DATA_PATH = Path("data/daily_metrics.json")
OUTPUT_DIR = Path("outputs")

def latest_metrics():
    rows = load_list(DATA_PATH)
    if not rows:
        return None, []
    return rows[-1], rows

def cmd_report():
    row, all_rows = latest_metrics()

    if not row:
        print("No daily metrics found.")
        return

    phase_state = load_phase_state()
    effective_awake = row.get("effective_awake_minutes")

    if effective_awake is None:
        effective_awake = compute_effective_awake_minutes()

    row_for_report = dict(row)
    row_for_report["effective_awake_minutes"] = effective_awake
    row_for_report["nap_credit_minutes"] = phase_state.get("nap_credit_minutes", row.get("nap_credit_minutes", 0))

    recovery = build_recovery_report(row_for_report, all_rows)
    energy = build_energy_report(row_for_report)
    phase = phase_from_effective_awake(effective_awake)
    patterns = build_pattern_report(row_for_report, all_rows)

    dashboard = {
        "recovery": recovery,
        "energy": energy,
        "phase": phase,
        "patterns": patterns,
        "timing": {
            "wake_time": phase_state.get("wake_time"),
            "nap_start_time": phase_state.get("nap_start_time"),
            "nap_end_time": phase_state.get("nap_end_time"),
            "nap_credit_minutes": phase_state.get("nap_credit_minutes", 0),
            "effective_awake_minutes": effective_awake
        }
    }

    OUTPUT_DIR.mkdir(exist_ok=True)

    save_json(OUTPUT_DIR / "recovery_report.json", recovery)
    save_json(OUTPUT_DIR / "energy_report.json", energy)
    save_json(OUTPUT_DIR / "phase_report.json", phase)
    save_json(OUTPUT_DIR / "pattern_report.json", patterns)
    save_json(OUTPUT_DIR / "dashboard.json", dashboard)

    print("\nRECOVERY")
    print(json.dumps(recovery, indent=2))

    print("\nENERGY")
    print(json.dumps(energy, indent=2))

    print("\nPHASE")
    print(json.dumps(phase, indent=2))

    print("\nPATTERNS")
    print(json.dumps(patterns, indent=2))

    print("\nTIMING")
    print(json.dumps(dashboard["timing"], indent=2))

    print("\nSaved dashboard -> outputs/dashboard.json")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python app.py report")
        return

    command = sys.argv[1].lower()

    if command == "report":
        cmd_report()
    else:
        print("Unknown command.")

if __name__ == "__main__":
    main()
