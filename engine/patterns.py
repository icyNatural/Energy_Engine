from statistics import median
from engine.pattern_language import PATTERN_LANGUAGE
from engine.pattern_presence import PATTERN_PRESENCE
from engine.memory import summarize_pattern

def _numeric_series(rows, key):
    vals = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)):
            vals.append(float(value))
    return vals

def _baseline_median(rows, key, baseline_days=7):
    if len(rows) <= 1:
        return None
    historical = rows[:-1]
    if baseline_days and len(historical) > baseline_days:
        historical = historical[-baseline_days:]
    vals = _numeric_series(historical, key)
    if not vals:
        return None
    return median(vals)

def _count_consecutive_condition(rows, key, baseline, comparator, max_lookback=7):
    count = 0
    for row in reversed(rows[-max_lookback:]):
        value = row.get(key)
        if not isinstance(value, (int, float)) or baseline is None:
            break
        if comparator(float(value), float(baseline)):
            count += 1
        else:
            break
    return count

def _presence_from_streak(streak):
    if streak >= 6:
        return "established"
    if streak >= 4:
        return "clear"
    if streak >= 2:
        return "present"
    return "emerging"

def _build_language_pattern(pattern_id, detail, streak=1):
    language = PATTERN_LANGUAGE.get(pattern_id, {})
    presence_key = _presence_from_streak(streak)
    presence = PATTERN_PRESENCE.get(presence_key, {})

    return {
        "id": pattern_id,
        "title": language.get("title", pattern_id),
        "meaning": language.get("meaning", ""),
        "note": language.get("note", ""),
        "detail": detail,
        "pattern_presence": presence_key,
        "pattern_presence_label": presence.get("label", presence_key.title()),
        "pattern_presence_description": presence.get("description", "")
    }

def build_pattern_report(row, all_rows=None, baseline_days=7):
    if all_rows is None:
        all_rows = [row]

    patterns = []
    signals = {}

    hrv_base = _baseline_median(all_rows, "sleeping_hrv", baseline_days)
    hr_base = _baseline_median(all_rows, "sleeping_hr", baseline_days)
    rr_base = _baseline_median(all_rows, "respiratory_rate", baseline_days)
    sleep_base = _baseline_median(all_rows, "actual_sleep_minutes", baseline_days)

    signals["sleeping_hrv_baseline_median"] = hrv_base
    signals["sleeping_hr_baseline_median"] = hr_base
    signals["respiratory_rate_baseline_median"] = rr_base
    signals["actual_sleep_minutes_baseline_median"] = sleep_base

    hrv_down = _count_consecutive_condition(all_rows, "sleeping_hrv", hrv_base, lambda x, b: x < b)
    if hrv_down >= 2:
        patterns.append(_build_language_pattern(
            "hrv_down_shift",
            f"HRV has stayed below your recent baseline for {hrv_down} day(s).",
            hrv_down
        ))

    hr_up = _count_consecutive_condition(all_rows, "sleeping_hr", hr_base, lambda x, b: x > b)
    if hr_up >= 2:
        patterns.append(_build_language_pattern(
            "sleep_hr_rise",
            f"Sleeping heart rhythm has stayed above your recent baseline for {hr_up} day(s).",
            hr_up
        ))

    rr_up = _count_consecutive_condition(all_rows, "respiratory_rate", rr_base, lambda x, b: x > b)
    if rr_up >= 2:
        patterns.append(_build_language_pattern(
            "respiratory_rise",
            f"Breathing rhythm has stayed above your recent baseline for {rr_up} day(s).",
            rr_up
        ))

    sleep_low = _count_consecutive_condition(all_rows, "actual_sleep_minutes", sleep_base, lambda x, b: x < b)
    if sleep_low >= 2:
        patterns.append(_build_language_pattern(
            "short_sleep_rhythm",
            f"Sleep time has stayed below your recent baseline for {sleep_low} day(s).",
            sleep_low
        ))

    current = all_rows[-1] if all_rows else row
    current_hrv = current.get("sleeping_hrv")
    current_hr = current.get("sleeping_hr")
    current_rr = current.get("respiratory_rate")

    cluster_flags = 0
    cluster_parts = []

    if isinstance(current_hrv, (int, float)) and hrv_base is not None and current_hrv < hrv_base:
        cluster_flags += 1
        cluster_parts.append("heart variability below baseline")

    if isinstance(current_hr, (int, float)) and hr_base is not None and current_hr > hr_base:
        cluster_flags += 1
        cluster_parts.append("sleeping heart rhythm above baseline")

    if isinstance(current_rr, (int, float)) and rr_base is not None and current_rr > rr_base:
        cluster_flags += 1
        cluster_parts.append("breathing rhythm above baseline")

    if cluster_flags >= 2:
        patterns.append(_build_language_pattern(
            "strain_cluster",
            ", ".join(cluster_parts) + ".",
            cluster_flags + 1
        ))

    memory = [summarize_pattern(p["id"]) for p in patterns]

    if patterns:
        summary = "Pattern watch active: " + "; ".join(p["title"] for p in patterns[:3]) + "."
    else:
        summary = "No strong pattern signals are standing out right now."

    return {
        "summary": summary,
        "patterns": patterns,
        "signals": signals,
        "memory": memory
    }
