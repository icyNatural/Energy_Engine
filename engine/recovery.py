from statistics import median
from engine.language_tools import pick_sentence

def clamp(value, low=0, high=100):
    return max(low, min(high, value))

def band_for_score(score):
    if score >= 75:
        return "restored"
    if score >= 55:
        return "steady"
    return "regenerating"

def recovery_message(band, seed="default"):
    if band == "restored":
        return {
            "state_label": "Restored",
            "meaning": "Recovery signals are coming through clearly.",
            "guidance": pick_sentence("guidance_restored", seed)
        }
    if band == "steady":
        return {
            "state_label": "Steady",
            "meaning": "Recovery signals look workable and balanced.",
            "guidance": pick_sentence("guidance_steady", seed)
        }
    return {
        "state_label": "Regenerating",
        "meaning": "Recovery signals are asking for more room.",
        "guidance": pick_sentence("guidance_regenerating", seed)
    }

def safe_metric_values(rows, key):
    vals = []
    for row in rows:
        if isinstance(row, dict):
            v = row.get(key)
            if isinstance(v, (int, float)):
                vals.append(v)
    return vals

def get_baseline_values(all_rows, key, baseline_days=7):
    vals = safe_metric_values(all_rows, key)
    if len(vals) <= 1:
        return []
    vals = vals[:-1]
    if len(vals) > baseline_days:
        vals = vals[-baseline_days:]
    return vals

def compute_baseline(all_rows, key, baseline_days=7):
    vals = get_baseline_values(all_rows, key, baseline_days)
    if not vals:
        return {"median": None}
    return {"median": median(vals)}

def compute_delta(today, baseline, reverse=False):
    if today is None or baseline is None:
        return None
    return (baseline - today) if reverse else (today - baseline)

def build_recovery_report(row, all_rows=None):
    if all_rows is None:
        all_rows = [row]

    sleep = row.get("actual_sleep_minutes", 0)
    deep = row.get("deep_minutes", 0)
    rem = row.get("rem_minutes", 0)
    hr = row.get("sleeping_hr")
    hrv = row.get("sleeping_hrv")
    rr = row.get("respiratory_rate")
    seed = row.get("date", "default")

    hr_base = compute_baseline(all_rows, "sleeping_hr")["median"]
    hrv_base = compute_baseline(all_rows, "sleeping_hrv")["median"]
    rr_base = compute_baseline(all_rows, "respiratory_rate")["median"]

    score = 50
    drivers = []

    if hrv_base is not None and hrv is not None:
        d = compute_delta(hrv, hrv_base)
        score += d * 1.5
        drivers.append(
            pick_sentence("hrv_good", seed + "hrv") if d >= 0
            else pick_sentence("hrv_low", seed + "hrv")
        )

    if hr_base is not None and hr is not None:
        d = compute_delta(hr, hr_base, reverse=True)
        score += d * 1.2
        drivers.append(
            pick_sentence("hr_good", seed + "hr") if d >= 0
            else pick_sentence("hr_high", seed + "hr")
        )

    if sleep >= 420:
        score += 10
        drivers.append(pick_sentence("sleep_good", seed + "sleep"))
    elif sleep >= 300:
        drivers.append(pick_sentence("sleep_ok", seed + "sleep"))
    else:
        score -= 10
        drivers.append(pick_sentence("sleep_low", seed + "sleep"))

    if deep >= 60:
        drivers.append(pick_sentence("deep_good", seed + "deep"))
    else:
        score -= 4
        drivers.append(pick_sentence("deep_low", seed + "deep"))

    if rem >= 60:
        drivers.append(pick_sentence("rem_good", seed + "rem"))
    else:
        score -= 3
        drivers.append(pick_sentence("rem_low", seed + "rem"))

    if rr_base is not None and rr is not None:
        if rr > rr_base:
            drivers.append(pick_sentence("resp_high", seed + "rr"))
        elif rr < rr_base:
            drivers.append(pick_sentence("resp_low", seed + "rr"))
        else:
            drivers.append(pick_sentence("resp_ok", seed + "rr"))

    score = clamp(round(score, 1))
    band = band_for_score(score)
    tone = recovery_message(band, seed)

    return {
        "score": score,
        "band": band,
        "state_label": tone["state_label"],
        "meaning": tone["meaning"],
        "guidance": tone["guidance"],
        "drivers": drivers
    }
