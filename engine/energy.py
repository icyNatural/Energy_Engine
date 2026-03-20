from engine.language_tools import pick_sentence

def safe_number(value, default=0):
    return value if isinstance(value, (int, float)) else default

def energy_message(band, seed="default"):
    if band == "open":
        return {
            "state_label": "Open",
            "meaning": pick_sentence("energy_open_meaning", seed + "meaning"),
            "guidance": pick_sentence("energy_open_guidance", seed + "guidance")
        }
    if band == "usable":
        return {
            "state_label": "Usable",
            "meaning": pick_sentence("energy_usable_meaning", seed + "meaning"),
            "guidance": pick_sentence("energy_usable_guidance", seed + "guidance")
        }
    return {
        "state_label": "Narrow",
        "meaning": pick_sentence("energy_narrow_meaning", seed + "meaning"),
        "guidance": pick_sentence("energy_narrow_guidance", seed + "guidance")
    }

def build_energy_report(row):
    effective_awake_minutes = safe_number(row.get("effective_awake_minutes"), 0)
    nap_credit_minutes = safe_number(row.get("nap_credit_minutes"), 0)
    activity_minutes = safe_number(row.get("activity_minutes"), 0)
    seed = str(row.get("date", "default"))

    awake = effective_awake_minutes / 60

    score = 100
    score -= awake * 2
    score += nap_credit_minutes / 10

    if activity_minutes > 180:
        score -= 5

    score = max(0, min(100, round(score, 1)))

    if score > 75:
        band = "open"
    elif score > 55:
        band = "usable"
    else:
        band = "narrow"

    tone = energy_message(band, seed)

    return {
        "score": score,
        "band": band,
        "state_label": tone["state_label"],
        "meaning": tone["meaning"],
        "guidance": tone["guidance"]
    }
