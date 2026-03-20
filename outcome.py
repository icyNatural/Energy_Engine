import sys
from engine.memory import record_outcome

if len(sys.argv) < 3:
    print("Usage: python outcome.py pattern_id note")
    raise SystemExit(1)

pattern = sys.argv[1]
note = " ".join(sys.argv[2:])

record_outcome(pattern, note)
print("Outcome recorded.")
