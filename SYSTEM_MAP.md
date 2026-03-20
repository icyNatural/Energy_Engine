# SYSTEM MAP

## Core Runtime

### app.py
**Purpose:** Main runtime  
**What it does:** Runs the main report flow and combines recovery, energy, and phase outputs.

### add_day.ps1
**Purpose:** Logs daily data  
**What it does:** Prompts you for daily metrics and saves them into the data store.

## Engine Modules

### engine/recovery.py
**Purpose:** Recovery scoring  
**What it does:** Scores recovery using sleep, HRV, HR, and related signals.

### engine/energy.py
**Purpose:** Energy model  
**What it does:** Estimates daytime usable energy from awake time, nap credit, and activity.

### engine/phase.py
**Purpose:** Phase logic  
**What it does:** Maps effective awake time into phases like Radiance, Flow, Amber, and Descent.

### engine/storage.py
**Purpose:** Data read/write  
**What it does:** Loads and saves JSON data for metrics, reports, and state.

### engine/words.py
**Purpose:** Daily language layer  
**What it does:** Suggests word-based daily modes, framing, and reflection language.

## Notes

- `data/` stores the main input records and saved state.
- `outputs/` stores generated reports.
- This file is the quick memory map for the active V1 system.
