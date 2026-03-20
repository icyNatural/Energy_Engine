from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

DAILY_METRICS_PATH = DATA_DIR / "daily_metrics.json"
DAY_MODES_PATH = DATA_DIR / "day_modes.json"
PHASE_STATE_PATH = DATA_DIR / "phase_state.json"
WORD_BANK_PATH = DATA_DIR / "word_bank.json"
OUTCOME_MEMORY_PATH = DATA_DIR / "outcome_memory.json"

RECOVERY_REPORT_PATH = OUTPUT_DIR / "recovery_report.json"
ENERGY_REPORT_PATH = OUTPUT_DIR / "energy_report.json"
PHASE_REPORT_PATH = OUTPUT_DIR / "phase_report.json"
PATTERN_REPORT_PATH = OUTPUT_DIR / "pattern_report.json"
DASHBOARD_REPORT_PATH = OUTPUT_DIR / "dashboard_report.json"
