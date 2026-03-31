from flask import Flask, request, redirect
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / "state.json"


def now_ts() -> int:
    return int(time.time())


def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def default_state():
    return {
        "wake_ts": None,
        "nap_start_ts": None,
        "nap_wake_ts": None,
        "nap_duration_m": 0,
        "last_updated_ts": None,
        "daily": {
            "actual_sleep_minutes": None,
            "deep_minutes": None,
            "rem_minutes": None,
            "sleep_hr": None,
            "hrv": None,
            "respiratory_rate": None,
            "activity_minutes": None,
            "sleep_eff": None,
        },
        "history": []
    }


def load_state():
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = default_state()
                base.update(data)
                base["daily"] = {**default_state()["daily"], **data.get("daily", {})}
                if not isinstance(base.get("history"), list):
                    base["history"] = []
                return base
        except Exception:
            pass
    return default_state()


def save_state(state: dict):
    state["last_updated_ts"] = now_ts()
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def clamp_100(x):
    return max(0, min(100, x))


def safe_num(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def fmt_time_from_ts(ts):
    if not ts:
        return "Not set"
    return datetime.fromtimestamp(ts).strftime("%H:%M")


def mins_since(ts):
    if not ts:
        return None
    return int((now_ts() - ts) / 60)


def human_mins(mins):
    if mins is None:
        return "Not set"
    h = mins // 60
    m = mins % 60
    return f"{h}h {m}m"


def parse_hhmm_to_ts(hhmm: str):
    hhmm = (hhmm or "").strip()
    if not hhmm:
        return None

    if ":" in hhmm:
        parts = hhmm.split(":")
        if len(parts) != 2:
            return None
        hh, mm = parts
    else:
        if len(hhmm) != 4 or not hhmm.isdigit():
            return None
        hh, mm = hhmm[:2], hhmm[2:]

    try:
        hh = int(hh)
        mm = int(mm)
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            return None
    except ValueError:
        return None

    now = datetime.now()
    dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)

    if dt.timestamp() > time.time():
        dt = dt - timedelta(days=1)

    return int(dt.timestamp())


def compute_nap_duration(state: dict) -> int:
    start_ts = state.get("nap_start_ts")
    wake_ts = state.get("nap_wake_ts")
    if start_ts and wake_ts and wake_ts >= start_ts:
        return int((wake_ts - start_ts) / 60)
    return 0


def robust_scale(values, min_scale: float, fallback: float) -> float:
    vals = [v for v in values if v is not None]
    if len(vals) < 3:
        return max(min_scale, fallback)
    m = median(vals)
    abs_devs = [abs(v - m) for v in vals]
    mad = median(abs_devs)
    return max(min_scale, mad if mad > 0 else fallback)


def nap_credit_minutes(n):
    if not n or n <= 0:
        return 0
    if n <= 20:
        credit = round(n * 0.55)
    elif n <= 45:
        credit = round(11 + (n - 20) * 0.9)
    elif n <= 90:
        credit = round(34 + (n - 45) * 1.1)
    else:
        credit = round(84 + (n - 90) * 0.55)
    return min(credit, 140)


def phase_extension_minutes(n):
    if not n or n <= 0:
        return 0
    if n <= 20:
        extension = round(n * 0.2)
    elif n <= 45:
        extension = round(4 + (n - 20) * 0.35)
    elif n <= 90:
        extension = round(13 + (n - 45) * 0.45)
    else:
        extension = round(33 + (n - 90) * 0.2)
    return min(extension, 45)


def phase_from_effective_awake(effective_awake_min: int, extension_min: int = 0):
    if effective_awake_min is None:
        return ("⏳", "Untracked", "Set your wake time to begin.")

    recovery_end = 4 * 60
    flow_end = 10 * 60 + extension_min
    radiance_end = 14 * 60 + extension_min
    surge_end = 18 * 60 + round(extension_min * 0.6)

    if effective_awake_min < recovery_end:
        return ("🌑", "Recovery", "Take it slow. You are still warming up.")
    elif effective_awake_min < flow_end:
        return ("🌊", "Flow", "Things should feel smooth right now.")
    elif effective_awake_min < radiance_end:
        return ("☀️", "Radiance", "This is your strongest window.")
    elif effective_awake_min < surge_end:
        return ("⚡", "Surge", "Energy is high. Do not waste it.")
    else:
        return ("🌙", "Settle", "Start slowing things down.")


def phase_color(name: str):
    return {
        "Recovery": "#64748b",
        "Flow": "#38bdf8",
        "Radiance": "#f59e0b",
        "Surge": "#a855f7",
        "Settle": "#94a3b8",
        "Untracked": "#6b7280",
    }.get(name, "#38bdf8")


def upsert_history_for_today(state):
    d = state.get("daily", {})
    hist = state.get("history", [])
    if not isinstance(hist, list):
        hist = []

    snapshot = {
        "date": today_iso(),
        "actual_sleep_minutes": safe_num(d.get("actual_sleep_minutes")),
        "deep_minutes": safe_num(d.get("deep_minutes")),
        "rem_minutes": safe_num(d.get("rem_minutes")),
        "sleep_hr": safe_num(d.get("sleep_hr")),
        "hrv": safe_num(d.get("hrv")),
        "respiratory_rate": safe_num(d.get("respiratory_rate")),
        "activity_minutes": safe_num(d.get("activity_minutes")),
        "sleep_eff": safe_num(d.get("sleep_eff")),
    }

    updated = False
    for row in hist:
        if row.get("date") == snapshot["date"]:
            row.update(snapshot)
            updated = True
            break

    if not updated:
        hist.append(snapshot)

    hist.sort(key=lambda x: x.get("date", ""))
    state["history"] = hist[-30:]


def unique_recent_days(state, n=7):
    hist = state.get("history", [])
    if not isinstance(hist, list):
        return []

    by_date = {}
    for row in hist:
        dt = row.get("date")
        if dt:
            by_date[dt] = row

    unique_rows = [by_date[k] for k in sorted(by_date.keys())]
    return unique_rows[-n:]


def collect(rows, key):
    vals = []
    for r in rows:
        v = safe_num(r.get(key))
        if v is not None:
            vals.append(v)
    return vals


def baseline_bundle(rows):
    out = {}
    fields = [
        "sleep_hr",
        "hrv",
        "sleep_eff",
        "actual_sleep_minutes",
        "deep_minutes",
        "rem_minutes",
        "respiratory_rate",
        "activity_minutes",
    ]
    for f in fields:
        vals = collect(rows, f)
        out[f] = median(vals) if vals else None
    return out


def score_v1(state):
    d = state.get("daily", {})
    rows = unique_recent_days(state, 7)
    base = baseline_bundle(rows)

    hr_vals = collect(rows, "sleep_hr")
    hrv_vals = collect(rows, "hrv")
    eff_vals = collect(rows, "sleep_eff")
    sleep_vals = collect(rows, "actual_sleep_minutes")
    deep_vals = collect(rows, "deep_minutes")
    rem_vals = collect(rows, "rem_minutes")
    rr_vals = collect(rows, "respiratory_rate")
    act_vals = collect(rows, "activity_minutes")

    hr = safe_num(d.get("sleep_hr"))
    hrv = safe_num(d.get("hrv"))
    eff = safe_num(d.get("sleep_eff"))
    sleep_min = safe_num(d.get("actual_sleep_minutes"))
    deep = safe_num(d.get("deep_minutes"))
    rem = safe_num(d.get("rem_minutes"))
    rr = safe_num(d.get("respiratory_rate"))
    act = safe_num(d.get("activity_minutes"))

    hr_scale = robust_scale(hr_vals, 1.0, 2.0)
    hrv_scale = robust_scale(hrv_vals, 5.0, 10.0)
    eff_scale = robust_scale(eff_vals, 2.0, 5.0)
    sleep_scale = robust_scale(sleep_vals, 30.0, 60.0)
    deep_scale = robust_scale(deep_vals, 10.0, 20.0)
    rem_scale = robust_scale(rem_vals, 10.0, 20.0)
    rr_scale = robust_scale(rr_vals, 0.3, 0.6)
    act_scale = robust_scale(act_vals, 20.0, 40.0)

    scores = {}
    notes = []

    if hr is not None and base["sleep_hr"] is not None:
        d_hr = hr - base["sleep_hr"]
        scores["sleep_hr"] = clamp((-d_hr) / hr_scale)
        notes.append(f"Sleep heart rate is {d_hr:+.1f} from your baseline")
    else:
        scores["sleep_hr"] = None

    if hrv is not None and base["hrv"] is not None:
        d_hrv = hrv - base["hrv"]
        scores["hrv"] = clamp((d_hrv) / hrv_scale)
        notes.append(f"HRV is {d_hrv:+.1f} from your baseline")
    else:
        scores["hrv"] = None

    if eff is not None and base["sleep_eff"] is not None:
        d_eff = eff - base["sleep_eff"]
        scores["sleep_eff"] = clamp(d_eff / eff_scale)
        notes.append(f"Sleep efficiency is {d_eff:+.1f} from your baseline")
    else:
        scores["sleep_eff"] = None

    if sleep_min is not None and base["actual_sleep_minutes"] is not None:
        d_sleep = sleep_min - base["actual_sleep_minutes"]
        scores["actual_sleep_minutes"] = clamp(d_sleep / sleep_scale)
        notes.append(f"Sleep time is {d_sleep:+.1f} minutes from your baseline")
    else:
        scores["actual_sleep_minutes"] = None

    if deep is not None and base["deep_minutes"] is not None:
        d_deep = deep - base["deep_minutes"]
        scores["deep_minutes"] = clamp(d_deep / deep_scale)
        notes.append(f"Deep sleep is {d_deep:+.1f} minutes from your baseline")
    else:
        scores["deep_minutes"] = None

    if rem is not None and base["rem_minutes"] is not None:
        d_rem = rem - base["rem_minutes"]
        scores["rem_minutes"] = clamp(d_rem / rem_scale)
        notes.append(f"REM sleep is {d_rem:+.1f} minutes from your baseline")
    else:
        scores["rem_minutes"] = None

    if rr is not None and base["respiratory_rate"] is not None:
        d_rr = rr - base["respiratory_rate"]
        scores["respiratory_rate"] = clamp((-d_rr) / rr_scale)
        notes.append(f"Respiratory rate is {d_rr:+.2f} from your baseline")
    else:
        scores["respiratory_rate"] = None

    if act is not None and base["activity_minutes"] is not None and base["activity_minutes"] > 0:
        ratio = act / base["activity_minutes"]
        dist = abs(ratio - 1.0)
        scores["activity_minutes"] = -clamp(dist / max(act_scale / max(base["activity_minutes"], 1), 0.25))
        notes.append(f"Activity landed at {ratio:.2f} times your usual level")
    else:
        scores["activity_minutes"] = None

    def pick(name, fallback=0.0):
        return scores[name] if scores[name] is not None else fallback

    readiness = (
        0.24 * pick("sleep_hr") +
        0.24 * pick("hrv") +
        0.12 * pick("sleep_eff") +
        0.14 * pick("actual_sleep_minutes") +
        0.10 * pick("deep_minutes") +
        0.06 * pick("rem_minutes") +
        0.06 * pick("respiratory_rate") +
        0.04 * pick("activity_minutes")
    )

    readiness = clamp(readiness)

    return {
        "baseline_days": len(rows),
        "baseline": base,
        "scores": scores,
        "readiness": readiness,
        "notes": notes,
    }


def band_from_energy(score_100):
    if score_100 >= 78:
        return (
            "Open",
            "You feel sharp and ready",
            "Use this window for something important"
        )
    if score_100 >= 55:
        return (
            "Steady",
            "You have energy but not endless",
            "Move forward but stay controlled"
        )
    return (
        "Low",
        "Energy is limited right now",
        "Keep things light and avoid pressure"
    )


def band_from_recovery(score_100):
    if score_100 >= 75:
        return (
            "Recovered",
            "Your body is in a good place",
            "You can move without forcing anything"
        )
    if score_100 >= 58:
        return (
            "Steady",
            "You are holding steady",
            "Stay smooth and avoid pushing too hard"
        )
    return (
        "Rebuilding",
        "Your body needs more recovery",
        "Slow down and give yourself space"
    )


def estimate_window_text(phase_name, eff_awake, phase_extension):
    if eff_awake is None:
        return "Set your wake time to begin."

    if phase_name == "Recovery":
        mins_left = max(0, (4 * 60) - eff_awake)
        return f"You will feel better in about {human_mins(mins_left)}"

    if phase_name == "Flow":
        mins_left = max(0, (10 * 60 + phase_extension) - eff_awake)
        return f"Strong window for the next {human_mins(mins_left)}"

    if phase_name == "Radiance":
        mins_left = max(0, (14 * 60 + phase_extension) - eff_awake)
        return f"Peak window for the next {human_mins(mins_left)}"

    if phase_name == "Surge":
        mins_left = max(0, (18 * 60 + round(phase_extension * 0.6)) - eff_awake)
        return f"High energy for about {human_mins(mins_left)} more"

    return "You will likely need rest soon."


def ensure_demo_state():
    if STATE_PATH.exists():
        return
    s = default_state()
    save_state(s)


@app.route("/")
def home():
    ensure_demo_state()
    state = load_state()

    wake_ts = state.get("wake_ts")
    mins_awake = mins_since(wake_ts)

    nap_dur = compute_nap_duration(state)
    if state.get("nap_duration_m") != nap_dur:
        state["nap_duration_m"] = nap_dur
        save_state(state)

    nap_credit = nap_credit_minutes(nap_dur)
    phase_extension = phase_extension_minutes(nap_dur)

    if mins_awake is None:
        eff_awake = None
        phase_icon, phase_name, phase_quote = ("⏳", "Untracked", "Set your wake time to begin.")
    else:
        eff_awake = max(0, mins_awake - nap_credit)
        phase_icon, phase_name, phase_quote = phase_from_effective_awake(eff_awake, phase_extension)

    color = phase_color(phase_name)

    core = score_v1(state)
    readiness = core["readiness"]
    recovery_score = round(((readiness + 1) / 2) * 100, 1)

    if eff_awake is None:
        energy_score = 0.0
    else:
        wake_drag = min((eff_awake / 60.0) * 3.0, 45)
        nap_bonus = min(nap_credit * 0.35 + phase_extension * 0.5, 22)
        energy_score = clamp_100(round(readiness * 50 + 50 + nap_bonus - wake_drag - 5, 1))

    energy_state, energy_meaning, energy_action = band_from_energy(energy_score)
    recovery_state, recovery_meaning, recovery_guidance = band_from_recovery(recovery_score)

    pattern_items = []
    d = state.get("daily", {})
    base = core["baseline"]

    if d.get("actual_sleep_minutes") is not None and base.get("actual_sleep_minutes") is not None:
        if safe_num(d.get("actual_sleep_minutes")) < base["actual_sleep_minutes"]:
            pattern_items.append({
                "title": "Short sleep",
                "label": "Watch",
                "meaning": "You may be running a little low on rest."
            })

    if nap_dur > 0:
        pattern_items.append({
            "title": "Nap boost",
            "label": "Active",
            "meaning": f"That nap gave you {nap_credit} minutes back and opened a little more time."
        })

    why_items = core["notes"][:4]
    window_text = estimate_window_text(phase_name, eff_awake, phase_extension)
    baseline_days = core["baseline_days"]
    confidence_text = (
        "Still learning your baseline."
        if baseline_days < 3 else
        "Getting a better read on your rhythm."
        if baseline_days < 7 else
        "Baseline confidence is getting solid."
    )

    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Energy Engine v1</title>
      <style>
        * {{ box-sizing: border-box; }}

        body {{
          margin: 0;
          padding: 18px;
          background: radial-gradient(circle at top, #12213f 0%, #081225 48%, #06101f 100%);
          color: #f8fafc;
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        }}

        .wrap {{
          max-width: 720px;
          margin: 0 auto;
        }}

        .card {{
          background: rgba(12, 24, 48, 0.88);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 28px;
          padding: 20px;
          margin-bottom: 16px;
          box-shadow: 0 14px 34px rgba(0,0,0,0.26);
          backdrop-filter: blur(8px);
        }}

        .hero {{
          padding: 24px 20px 20px;
          overflow: hidden;
          position: relative;
        }}

        .hero::before {{
          content: "";
          position: absolute;
          inset: 0;
          background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.01));
          pointer-events: none;
        }}

        .hero-inner {{
          position: relative;
          z-index: 1;
        }}

        .eyebrow {{
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: rgba(255,255,255,0.65);
          margin-bottom: 12px;
        }}

        .phase-row {{
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 10px;
        }}

        .emoji {{
          font-size: 34px;
          line-height: 1;
        }}

        .phase {{
          font-size: 48px;
          line-height: 1;
          font-weight: 900;
          margin: 0;
        }}

        .phase-quote {{
          font-size: 16px;
          line-height: 1.5;
          color: #dbe4ef;
          margin-top: 6px;
        }}

        .energy-state {{
          margin-top: 22px;
          font-size: 34px;
          line-height: 1;
          font-weight: 900;
        }}

        .energy-meaning {{
          margin-top: 10px;
          font-size: 18px;
          line-height: 1.45;
          color: #e8eef7;
        }}

        .energy-action {{
          margin-top: 10px;
          font-size: 20px;
          line-height: 1.35;
          font-weight: 800;
        }}

        .window {{
          margin-top: 12px;
          font-size: 14px;
          color: #aebed3;
        }}

        .bar {{
          width: 100%;
          height: 12px;
          border-radius: 999px;
          background: rgba(255,255,255,0.08);
          overflow: hidden;
          margin-top: 18px;
        }}

        .fill {{
          height: 12px;
          width: {energy_score}%;
          background: {color};
          border-radius: 999px;
        }}

        .hero-actions {{
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 10px;
          margin-top: 18px;
        }}

        .section-title {{
          font-size: 15px;
          font-weight: 800;
          color: rgba(255,255,255,0.76);
          margin-bottom: 14px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }}

        .metrics {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }}

        .metric {{
          background: rgba(255,255,255,0.035);
          border-radius: 18px;
          padding: 14px;
        }}

        .metric-label {{
          font-size: 12px;
          color: #94a3b8;
          margin-bottom: 6px;
        }}

        .metric-value {{
          font-size: 20px;
          font-weight: 800;
          line-height: 1.1;
        }}

        .metric-sub {{
          margin-top: 4px;
          font-size: 12px;
          color: #93a7c2;
        }}

        .split {{
          display: grid;
          grid-template-columns: 1.15fr 0.85fr;
          gap: 14px;
        }}

        .recovery-big {{
          font-size: 34px;
          line-height: 1;
          font-weight: 900;
          margin-bottom: 10px;
        }}

        .text {{
          font-size: 16px;
          line-height: 1.5;
          color: #dbe4ef;
        }}

        .muted {{
          margin-top: 8px;
          font-size: 14px;
          line-height: 1.45;
          color: #94a3b8;
        }}

        .row {{
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 14px;
        }}

        .btn {{
          appearance: none;
          border: 0;
          border-radius: 18px;
          padding: 14px 16px;
          font-size: 15px;
          font-weight: 800;
          cursor: pointer;
          width: 100%;
        }}

        .btn-primary {{
          background: white;
          color: #081225;
        }}

        .btn-ghost {{
          background: rgba(255,255,255,0.08);
          color: white;
        }}

        .btn-soft {{
          background: rgba(255,255,255,0.04);
          color: white;
        }}

        input {{
          width: 100%;
          padding: 14px 14px;
          font-size: 16px;
          border-radius: 18px;
          border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.04);
          color: white;
          outline: none;
        }}

        input::placeholder {{
          color: #94a3b8;
        }}

        .inline-form {{
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 10px;
          align-items: center;
          margin-top: 12px;
        }}

        .double-form {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-top: 12px;
        }}

        .triple-form {{
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 10px;
          margin-top: 12px;
        }}

        .mini-box {{
          background: rgba(255,255,255,0.035);
          border-radius: 18px;
          padding: 14px;
          margin-top: 10px;
        }}

        .mini-title-row {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          margin-bottom: 6px;
        }}

        .mini-title {{
          font-size: 15px;
          font-weight: 800;
        }}

        .mini-text {{
          font-size: 14px;
          color: #dbe4ef;
          line-height: 1.45;
        }}

        .tag {{
          padding: 5px 10px;
          border-radius: 999px;
          background: rgba(255,255,255,0.08);
          font-size: 12px;
          font-weight: 800;
          color: white;
          white-space: nowrap;
        }}

        details {{
          margin-top: 10px;
          background: rgba(255,255,255,0.02);
          border-radius: 18px;
          padding: 14px;
        }}

        summary {{
          cursor: pointer;
          font-weight: 800;
          color: white;
        }}

        ul {{
          margin: 10px 0 0 18px;
          padding: 0;
        }}

        li {{
          color: #dbe4ef;
          margin-bottom: 6px;
          line-height: 1.45;
        }}

        @media (max-width: 640px) {{
          .hero-actions,
          .split,
          .metrics,
          .inline-form,
          .double-form,
          .triple-form {{
            grid-template-columns: 1fr;
          }}

          .phase {{
            font-size: 42px;
          }}

          .energy-state {{
            font-size: 30px;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="wrap">

        <div class="card hero">
          <div class="hero-inner">
            <div class="eyebrow">Your state right now</div>

            <div class="phase-row">
              <div class="emoji">{phase_icon}</div>
              <div class="phase">{phase_name}</div>
            </div>

            <div class="phase-quote">{phase_quote}</div>

            <div class="energy-state">{energy_state}</div>
            <div class="energy-meaning">{energy_meaning}</div>
            <div class="energy-action">{energy_action}</div>
            <div class="window">{window_text}</div>

            <div class="bar"><div class="fill"></div></div>

            <div class="hero-actions">
              <form method="post" action="/wake_now">
                <button class="btn btn-primary" type="submit">Set Wake Now</button>
              </form>
              <form method="post" action="/nap_start">
                <button class="btn btn-ghost" type="submit">Start Nap</button>
              </form>
              <form method="get" action="/">
                <button class="btn btn-soft" type="submit">Refresh</button>
              </form>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="section-title">Today</div>
          <div class="metrics">
            <div class="metric">
              <div class="metric-label">Wake time</div>
              <div class="metric-value">{fmt_time_from_ts(wake_ts)}</div>
            </div>

            <div class="metric">
              <div class="metric-label">Time awake</div>
              <div class="metric-value">{human_mins(eff_awake)}</div>
            </div>

            <div class="metric">
              <div class="metric-label">Nap credit</div>
              <div class="metric-value">{nap_credit}m</div>
              <div class="metric-sub">Energy back from nap recovery</div>
            </div>

            <div class="metric">
              <div class="metric-label">Phase extension</div>
              <div class="metric-value">+{phase_extension}m</div>
              <div class="metric-sub">Added to your stronger window</div>
            </div>
          </div>
        </div>

        <div class="split">
          <div class="card">
            <div class="section-title">Recovery</div>
            <div class="recovery-big">{recovery_state}</div>
            <div class="text">{recovery_meaning}</div>
            <div class="muted">{recovery_guidance}</div>
            <div class="muted">Recovery score {recovery_score}/100</div>
            <div class="muted">{confidence_text}</div>
          </div>

          <div class="card">
            <div class="section-title">Nap</div>
            <div class="text">
              Start {fmt_time_from_ts(state.get("nap_start_ts"))}<br>
              End {fmt_time_from_ts(state.get("nap_wake_ts"))}<br>
              Length {nap_dur if nap_dur else "—"} minutes
            </div>

            <div class="row">
              <form method="post" action="/nap_wake" style="width:100%;">
                <button class="btn btn-primary" type="submit">End Nap</button>
              </form>
              <form method="post" action="/nap_clear" style="width:100%;">
                <button class="btn btn-ghost" type="submit">Clear Nap</button>
              </form>
            </div>

            <details>
              <summary>Set nap time</summary>
              <form method="post" action="/nap_manual">
                <div class="double-form">
                  <input name="start" placeholder="Start 1130 or 11:30">
                  <input name="wake" placeholder="Wake 1225 or 12:25">
                </div>
                <div class="row">
                  <button class="btn btn-ghost" type="submit">Save Nap Time</button>
                </div>
              </form>
            </details>
          </div>
        </div>

        <div class="card">
          <div class="section-title">Today’s numbers</div>

          <form method="post" action="/save_daily_fast">
            <div class="triple-form">
              <input name="actual_sleep_minutes" placeholder="Sleep minutes" value="{'' if d.get('actual_sleep_minutes') is None else d.get('actual_sleep_minutes')}">
              <input name="sleep_hr" placeholder="Sleep heart rate" value="{'' if d.get('sleep_hr') is None else d.get('sleep_hr')}">
              <input name="hrv" placeholder="HRV" value="{'' if d.get('hrv') is None else d.get('hrv')}">
            </div>
            <div class="row">
              <button class="btn btn-ghost" type="submit">Save Today’s Numbers</button>
            </div>
          </form>

          <details>
            <summary>Add more detail</summary>
            <form method="post" action="/save_daily_advanced">
              <div class="triple-form">
                <input name="deep_minutes" placeholder="Deep sleep minutes" value="{'' if d.get('deep_minutes') is None else d.get('deep_minutes')}">
                <input name="rem_minutes" placeholder="REM minutes" value="{'' if d.get('rem_minutes') is None else d.get('rem_minutes')}">
                <input name="respiratory_rate" placeholder="Respiratory rate" value="{'' if d.get('respiratory_rate') is None else d.get('respiratory_rate')}">
              </div>
              <div class="double-form">
                <input name="activity_minutes" placeholder="Activity minutes" value="{'' if d.get('activity_minutes') is None else d.get('activity_minutes')}">
                <input name="sleep_eff" placeholder="Sleep efficiency percent" value="{'' if d.get('sleep_eff') is None else d.get('sleep_eff')}">
              </div>
              <div class="row">
                <button class="btn btn-ghost" type="submit">Save More Detail</button>
              </div>
            </form>
          </details>
        </div>

        <div class="card">
          <div class="section-title">Set wake time</div>
          <div class="muted">Use HHMM or HH:MM. If you enter a future time, it will be treated as yesterday.</div>
          <form method="post" action="/wake_set" class="inline-form">
            <input name="hhmm" placeholder="0930 or 09:30">
            <button class="btn btn-ghost" type="submit">Save Wake Time</button>
          </form>
        </div>

        <div class="card">
          <div class="section-title">Things to watch</div>
          <div class="text">{'Nothing to watch right now.' if not pattern_items else 'A few things are worth watching.'}</div>
          {''.join([f'''
            <div class="mini-box">
              <div class="mini-title-row">
                <div class="mini-title">{p["title"]}</div>
                <div class="tag">{p["label"]}</div>
              </div>
              <div class="mini-text">{p["meaning"]}</div>
            </div>
          ''' for p in pattern_items]) if pattern_items else ''}
        </div>

        <div class="card">
          <details>
            <summary>Why this is showing up</summary>
            <ul>
              {''.join([f"<li>{item}</li>" for item in why_items]) if why_items else "<li>Add a few days of data so this gets more accurate.</li>"}
            </ul>
          </details>
        </div>

      </div>
    </body>
    </html>
    """


@app.route("/wake_now", methods=["POST"])
def wake_now():
    s = load_state()
    s["wake_ts"] = now_ts()
    save_state(s)
    return redirect("/")


@app.route("/wake_set", methods=["POST"])
def wake_set():
    hhmm = request.form.get("hhmm", "")
    ts = parse_hhmm_to_ts(hhmm)
    if ts:
        s = load_state()
        s["wake_ts"] = ts
        save_state(s)
    return redirect("/")


@app.route("/save_daily_fast", methods=["POST"])
def save_daily_fast():
    s = load_state()
    d = s.get("daily", {})
    for key in ["actual_sleep_minutes", "sleep_hr", "hrv"]:
        val = safe_num(request.form.get(key, ""))
        if val is not None:
            d[key] = val
    s["daily"] = d
    upsert_history_for_today(s)
    save_state(s)
    return redirect("/")


@app.route("/save_daily_advanced", methods=["POST"])
def save_daily_advanced():
    s = load_state()
    d = s.get("daily", {})
    for key in ["deep_minutes", "rem_minutes", "respiratory_rate", "activity_minutes", "sleep_eff"]:
        val = safe_num(request.form.get(key, ""))
        if val is not None:
            d[key] = val
    s["daily"] = d
    upsert_history_for_today(s)
    save_state(s)
    return redirect("/")


@app.route("/nap_start", methods=["POST"])
def nap_start():
    s = load_state()
    s["nap_start_ts"] = now_ts()
    s["nap_wake_ts"] = None
    s["nap_duration_m"] = 0
    save_state(s)
    return redirect("/")


@app.route("/nap_wake", methods=["POST"])
def nap_wake():
    s = load_state()
    s["nap_wake_ts"] = now_ts()
    s["nap_duration_m"] = compute_nap_duration(s)
    save_state(s)
    return redirect("/")


@app.route("/nap_clear", methods=["POST"])
def nap_clear():
    s = load_state()
    s["nap_start_ts"] = None
    s["nap_wake_ts"] = None
    s["nap_duration_m"] = 0
    save_state(s)
    return redirect("/")


@app.route("/nap_manual", methods=["POST"])
def nap_manual():
    start_s = request.form.get("start", "")
    wake_s = request.form.get("wake", "")

    start_ts = parse_hhmm_to_ts(start_s) if start_s else None
    wake_ts = parse_hhmm_to_ts(wake_s) if wake_s else None

    if start_ts and wake_ts:
        if wake_ts < start_ts:
            wake_ts += 24 * 60 * 60

        s = load_state()
        s["nap_start_ts"] = start_ts
        s["nap_wake_ts"] = wake_ts
        s["nap_duration_m"] = compute_nap_duration(s)
        save_state(s)

    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8787)
