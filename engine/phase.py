def phase_from_effective_awake(effective_awake_minutes):
    if effective_awake_minutes is None:
        return {
            "phase": "Untracked",
            "icon": "⏳",
            "condition": "Wake time has not been set",
            "sense": "Phase cannot be calculated yet",
            "quote": "Set wake time to begin phase tracking."
        }

    hours = effective_awake_minutes / 60

    if hours < 4:
        return {
            "phase": "Recovery",
            "icon": "🌑",
            "condition": "System rebuilds quietly",
            "sense": "Low outward demand, high inward repair",
            "quote": "System rebuilds quietly."
        }

    if hours < 10:
        return {
            "phase": "Flow",
            "icon": "🌊",
            "condition": "Movement continues without resistance",
            "sense": "Steady continuity and workable output",
            "quote": "Movement continues without resistance."
        }

    if hours < 14:
        return {
            "phase": "Radiance",
            "icon": "☀️",
            "condition": "Expression and clarity come forward",
            "sense": "Clear output, strong presence, lighter effort",
            "quote": "The sun shines unhindered."
        }

    if hours < 18:
        return {
            "phase": "Surge",
            "icon": "⚡",
            "condition": "Energy expands beyond ordinary demand",
            "sense": "Drive rises, output can stretch higher",
            "quote": "Energy expands beyond demand."
        }

    return {
        "phase": "Settle",
        "icon": "🌙",
        "condition": "System begins to quiet",
        "sense": "Output softens and recovery preparation begins",
        "quote": "System begins to quiet."
    }
