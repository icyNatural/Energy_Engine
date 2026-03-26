from flask import Flask, request, redirect
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / "state.json"


# ----------------------------
# STATE
# ----------------------------
def now_ts() -> int:
    return int(time.time())


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


# ----------------------------
# HELPERS
# ----------------------------
def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


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


# ----------------------------
# NAP EFFECT
# ----------------------------
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


# ----------------------------
# PHASE
# ----------------------------
def phase_from_effective_awake(effective_awake_min: int, extension_min: int = 0):
    if effective_awake_min is None:
        return ("⏳", "Untracked", "Set wake to begin.")

    recovery_end = 4 * 60
    flow_end = 10 * 60 + extension_min
    radiance_end = 14 * 60 + extension_min
    surge_end = 18 * 60 + round(extension_min * 0.6)

    if effective_awake_min < recovery_end:
        return ("🌑", "Recovery", "System rebuilds quietly.")
    elif effective_awake_min < flow_end:
        return ("🌊", "Flow", "Movement continues without resistance.")
    elif effective_awake_min < radiance_end:
        return ("☀️", "Radiance", "The sun shines unhindered.")
    elif effective_awake_min < surge_end:
        return ("⚡", "Surge", "Energy expands beyond demand.")
    else:
        return ("🌙", "Settle", "System begins to quiet.")


def phase_color(name: str):
    return {
        "Recovery": "#64748b",
        "Flow": "#38bdf8",
        "Radiance": "#f59e0b",
        "Surge": "#a855f7",
        "Settle": "#94a3b8",
        "Untracked": "#6b7280",
    }.get(name, "#38bdf8")


# ----------------------------
# BASELINE + SCORING CORE V1
# ----------------------------
def recent_history(state, n=7):
    hist = state.get("history", [])
    if not isinstance(hist, list):
        return []
    return hist[-n:]


def collect(rows, key):
    return [safe_num(r.get(key)) for r in rows if safe_num(r.get(key)) is not None]


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
    rows = recent_history(state, 7)
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

    # adaptive scales from your own variability
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

    # lower HR better
    if hr is not None and base["sleep_hr"] is not None:
        d_hr = hr - base["sleep_hr"]
        scores["sleep_hr"] = clamp((-d_hr) / hr_scale)
        notes.append(f"Sleep HR vs baseline: {d_hr:+.1f}")
    else:
        scores["sleep_hr"] = None

    # higher HRV better
    if hrv is not None and base["hrv"] is not None:
        d_hrv = hrv - base["hrv"]
        scores["hrv"] = clamp((d_hrv) / hrv_scale)
        notes.append(f"HRV vs baseline: {d_hrv:+.1f}")
    else:
        scores["hrv"] = None

    # higher efficiency better
    if eff is not None and base["sleep_eff"] is not None:
        d_eff = eff - base["sleep_eff"]
        scores["sleep_eff"] = clamp(d_eff / eff_scale)
        notes.append(f"Sleep efficiency vs baseline: {d_eff:+.1f}")
    else:
        scores["sleep_eff"] = None

    # higher actual sleep better, but personal not generic
    if sleep_min is not None and base["actual_sleep_minutes"] is not None:
        d_sleep = sleep_min - base["actual_sleep_minutes"]
        scores["actual_sleep_minutes"] = clamp(d_sleep / sleep_scale)
        notes.append(f"Actual sleep vs baseline: {d_sleep:+.1f}")
    else:
        scores["actual_sleep_minutes"] = None

    # higher deep better
    if deep is not None and base["deep_minutes"] is not None:
        d_deep = deep - base["deep_minutes"]
        scores["deep_minutes"] = clamp(d_deep / deep_scale)
        notes.append(f"Deep vs baseline: {d_deep:+.1f}")
    else:
        scores["deep_minutes"] = None

    # higher REM better
    if rem is not None and base["rem_minutes"] is not None:
        d_rem = rem - base["rem_minutes"]
        scores["rem_minutes"] = clamp(d_rem / rem_scale)
        notes.append(f"REM vs baseline: {d_rem:+.1f}")
    else:
        scores["rem_minutes"] = None

    # lower respiratory usually better if above baseline
    if rr is not None and base["respiratory_rate"] is not None:
        d_rr = rr - base["respiratory_rate"]
        scores["respiratory_rate"] = clamp((-d_rr) / rr_scale)
        notes.append(f"Respiratory vs baseline: {d_rr:+.2f}")
    else:
        scores["respiratory_rate"] = None

    # activity mismatch is mild, not moralized
    if act is not None and base["activity_minutes"] is not None and base["activity_minutes"] > 0:
        ratio = act / base["activity_minutes"]
        dist = abs(ratio - 1.0)
        scores["activity_minutes"] = -clamp(dist / max(act_scale / max(base["activity_minutes"], 1), 0.25))
        notes.append(f"Activity ratio vs baseline: x{ratio:.2f}")
    else:
        scores["activity_minutes"] = None

    def pick(name, fallback=0.0):
        return scores[name] if scores[name] is not None else fallback

    # core readiness blend based on your second script logic, expanded
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
        return ("Open", "Energy looks widely available.", "This is a strong window for action and expression.")
    if score_100 >= 55:
        return ("Usable", "Energy is available but not unlimited.", "Move forward with steady pacing.")
    return ("Narrow", "Energy range looks smaller right now.", "Choose essential actions and conserve effort.")


def band_from_recovery(score_100):
    if score_100 >= 75:
        return ("Restored", "Recovery signals are coming through clearly.", "Movement is available without forcing.")
    if score_100 >= 58:
        return ("Steady", "Recovery signals look workable and balanced.", "Favor smoother pacing today.")
    return ("Regenerating", "Recovery signals are asking for more room.", "Lower friction tasks may feel better.")


# ----------------------------
# UI
# ----------------------------
@app.route("/")
def home():
    state = load_state()

    wake_ts = state.get("wake_ts")
    mins_awake = mins_since(wake_ts)

    nap_dur = compute_nap_duration(state)
    state["nap_duration_m"] = nap_dur
    save_state(state)

    nap_credit = nap_credit_minutes(nap_dur)
    phase_extension = phase_extension_minutes(nap_dur)

    if mins_awake is None:
        eff_awake = None
        phase_icon, phase_name, phase_quote = ("⏳", "Untracked", "Set wake to begin.")
    else:
        eff_awake = max(0, mins_awake - nap_credit)
        phase_icon, phase_name, phase_quote = phase_from_effective_awake(eff_awake, phase_extension)

    color = phase_color(phase_name)

    core = score_v1(state)
    readiness = core["readiness"]  # -1..+1
    recovery_score = round(((readiness + 1) / 2) * 100, 1)

    # energy = recovery base + wake load + nap reintegration
    if eff_awake is None:
        energy_score = 0.0
    else:
        wake_drag = min((eff_awake / 60.0) * 3.0, 45)
        nap_bonus = min(nap_credit * 0.35 + phase_extension * 0.5, 22)
        energy_score = clamp((readiness * 50 + 50 + nap_bonus - wake_drag - 5), 0, 100)

    energy_score = round(energy_score, 1)

    energy_state, energy_meaning, energy_guidance = band_from_energy(energy_score)
    recovery_state, recovery_meaning, recovery_guidance = band_from_recovery(recovery_score)

    pattern_items = []
    d = state.get("daily", {})
    base = core["baseline"]

    if d.get("actual_sleep_minutes") is not None and base.get("actual_sleep_minutes") is not None:
        if safe_num(d.get("actual_sleep_minutes")) < base["actual_sleep_minutes"]:
            pattern_items.append({
                "title": "Short sleep rhythm",
                "label": "Present",
                "meaning": "Rest demand is gradually rising."
            })

    if nap_dur > 0:
        pattern_items.append({
            "title": "Nap integration",
            "label": "Present",
            "meaning": f"Mini cycle returned {nap_credit}m of credit and +{phase_extension}m of extension."
        })

    pattern_summary = "No active patterns." if not pattern_items else "Pattern watch active."

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
          padding: 16px;
          background: #081225;
          color: #f8fafc;
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        }}
        .wrap {{ max-width: 680px; margin: 0 auto; }}
        .card {{
          background: #0c1830;
          border: 1px solid rgba(255,255,255,0.04);
          border-radius: 24px;
          padding: 18px;
          margin-bottom: 14px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.22);
        }}
        .hero {{ padding-top: 20px; }}
        .phase-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }}
        .emoji {{ font-size: 34px; line-height: 1; }}
        .phase {{ font-size: 46px; line-height: 1; font-weight: 800; margin: 0; color: white; }}
        .sub {{ font-size: 16px; color: #dbe4ef; line-height: 1.45; margin-top: 4px; }}
        .stats {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-top: 16px;
        }}
        .stat {{ background: rgba(255,255,255,0.03); border-radius: 16px; padding: 12px; }}
        .stat-label {{ font-size: 12px; color: #94a3b8; margin-bottom: 4px; }}
        .stat-value {{ font-size: 16px; font-weight: 700; }}
        .row {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
        .btn {{
          appearance: none;
          border: 0;
          border-radius: 16px;
          padding: 13px 16px;
          font-size: 16px;
          font-weight: 700;
          cursor: pointer;
        }}
        .btn-primary {{ background: white; color: #081225; }}
        .btn-ghost {{ background: rgba(255,255,255,0.08); color: white; }}
        .title {{ font-size: 17px; font-weight: 800; margin-bottom: 10px; }}
        .big {{ font-size: 34px; font-weight: 800; line-height: 1.05; margin-bottom: 8px; }}
        .text {{ font-size: 16px; line-height: 1.45; color: #dbe4ef; }}
        .muted {{ font-size: 14px; line-height: 1.45; color: #94a3b8; margin-top: 6px; }}
        .bar {{
          width: 100%;
          height: 12px;
          border-radius: 999px;
          background: rgba(255,255,255,0.08);
          overflow: hidden;
          margin-top: 12px;
        }}
        .fill {{
          height: 12px;
          width: {energy_score}%;
          background: {color};
        }}
        input {{
          width: 100%;
          padding: 13px 14px;
          font-size: 16px;
          border-radius: 16px;
          border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.04);
          color: white;
          outline: none;
        }}
        input::placeholder {{ color: #94a3b8; }}
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
          background: rgba(255,255,255,0.03);
          border-radius: 16px;
          padding: 12px;
          margin-top: 10px;
        }}
        .mini-title-row {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          margin-bottom: 6px;
        }}
        .mini-title {{ font-size: 15px; font-weight: 800; }}
        .mini-text {{ font-size: 14px; color: #dbe4ef; line-height: 1.4; }}
        .tag {{
          padding: 4px 10px;
          border-radius: 999px;
          background: rgba(255,255,255,0.08);
          font-size: 12px;
          font-weight: 700;
          color: white;
          white-space: nowrap;
        }}
        @media (max-width: 640px) {{
          .inline-form, .double-form, .triple-form {{
            grid-template-columns: 1fr;
          }}
          .phase {{ font-size: 42px; }}
          .big {{ font-size: 30px; }}
        }}
      </style>
    </head>
    <body>
      <div class="wrap">

        <div class="card hero">
          <div class="phase-row">
            <div class="emoji">{phase_icon}</div>
            <div class="phase">{phase_name}</div>
          </div>
          <div class="sub">{phase_quote}</div>

          <div class="stats">
            <div class="stat">
              <div class="stat-label">Wake</div>
              <div class="stat-value">{fmt_time_from_ts(wake_ts)}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Effective awake</div>
              <div class="stat-value">{human_mins(eff_awake)}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Nap credit</div>
              <div class="stat-value">{nap_credit}m</div>
            </div>
            <div class="stat">
              <div class="stat-label">Phase extension</div>
              <div class="stat-value">+{phase_extension}m</div>
            </div>
          </div>

          <div class="row">
            <form method="post" action="/wake_now">
              <button class="btn btn-primary" type="submit">Set Wake Now</button>
            </form>
            <form method="get" action="/">
              <button class="btn btn-ghost" type="submit">Refresh</button>
            </form>
          </div>
        </div>

        <div class="card">
          <div class="title">Set wake manual</div>
          <div class="muted">Use HHMM or HH:MM. Future times are treated as yesterday.</div>
          <form method="post" action="/wake_set" class="inline-form">
            <input name="hhmm" placeholder="0930 or 09:30">
            <button class="btn btn-ghost" type="submit">Set Wake</button>
          </form>
        </div>

        <div class="card">
          <div class="title">Daily inputs</div>
          <form method="post" action="/save_daily">
            <div class="triple-form">
              <input name="actual_sleep_minutes" placeholder="Actual sleep min" value="{'' if d.get('actual_sleep_minutes') is None else d.get('actual_sleep_minutes')}">
              <input name="deep_minutes" placeholder="Deep min" value="{'' if d.get('deep_minutes') is None else d.get('deep_minutes')}">
              <input name="rem_minutes" placeholder="REM min" value="{'' if d.get('rem_minutes') is None else d.get('rem_minutes')}">
            </div>
            <div class="triple-form">
              <input name="sleep_hr" placeholder="Sleep HR" value="{'' if d.get('sleep_hr') is None else d.get('sleep_hr')}">
              <input name="hrv" placeholder="HRV" value="{'' if d.get('hrv') is None else d.get('hrv')}">
              <input name="respiratory_rate" placeholder="Respiratory" value="{'' if d.get('respiratory_rate') is None else d.get('respiratory_rate')}">
            </div>
            <div class="double-form">
              <input name="activity_minutes" placeholder="Activity min" value="{'' if d.get('activity_minutes') is None else d.get('activity_minutes')}">
              <input name="sleep_eff" placeholder="Sleep efficiency %" value="{'' if d.get('sleep_eff') is None else d.get('sleep_eff')}">
            </div>
            <div class="row">
              <button class="btn btn-ghost" type="submit">Save Daily Inputs</button>
            </div>
          </form>
        </div>

        <div class="card">
          <div class="title">Energy</div>
          <div class="big">{energy_state}</div>
          <div class="text">{energy_meaning}</div>
          <div class="muted">{energy_guidance}</div>
          <div class="bar"><div class="fill"></div></div>
          <div class="muted">Energy index: {energy_score}/100</div>
        </div>

        <div class="card">
          <div class="title">Recovery</div>
          <div class="big">{recovery_state}</div>
          <div class="text">{recovery_meaning}</div>
          <div class="muted">{recovery_guidance}</div>
          <div class="muted">Recovery score: {recovery_score}/100</div>
        </div>

        <div class="card">
          <div class="title">Mini cycle</div>
          <div class="text">
            Nap start: {fmt_time_from_ts(state.get("nap_start_ts"))}<br>
            Nap wake: {fmt_time_from_ts(state.get("nap_wake_ts"))}<br>
            Nap duration: {nap_dur if nap_dur else "—"}m
          </div>

          <div class="row">
            <form method="post" action="/nap_start">
              <button class="btn btn-primary" type="submit">Start Nap</button>
            </form>
            <form method="post" action="/nap_wake">
              <button class="btn btn-primary" type="submit">Nap Wake</button>
            </form>
            <form method="post" action="/nap_clear">
              <button class="btn btn-ghost" type="submit">Clear Nap</button>
            </form>
          </div>

          <form method="post" action="/nap_manual">
            <div class="muted" style="margin-top:14px;">Set nap manually with start and wake times</div>
            <div class="double-form">
              <input name="start" placeholder="Start 1130 or 11:30">
              <input name="wake" placeholder="Wake 1225 or 12:25">
            </div>
            <div class="row">
              <button class="btn btn-ghost" type="submit">Set Nap Manual</button>
            </div>
          </form>
        </div>

        <div class="card">
          <div class="title">Pattern Watch</div>
          <div class="text">{pattern_summary}</div>
          {''.join([f'''
            <div class="mini-box">
              <div class="mini-title-row">
                <div class="mini-title">{p["title"]}</div>
                <div class="tag">{p["label"]}</div>
              </div>
              <div class="mini-text">{p["meaning"]}</div>
            </div>
          ''' for p in pattern_items]) if pattern_items else '<div class="muted">No active patterns.</div>'}
        </div>

        <div class="card">
          <div class="title">Baseline core</div>
          <div class="muted">Baseline days used: {core["baseline_days"]}</div>
          <div class="muted">Readiness core: {round(readiness, 3)}</div>
          <div class="muted">{' | '.join(core["notes"][:5]) if core["notes"] else 'Add a few days of data to strengthen baseline learning.'}</div>
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


@app.route("/save_daily", methods=["POST"])
def save_daily():
    s = load_state()
    d = s.get("daily", {})
    for key in [
        "actual_sleep_minutes",
        "deep_minutes",
        "rem_minutes",
        "sleep_hr",
        "hrv",
        "respiratory_rate",
        "activity_minutes",
        "sleep_eff",
    ]:
        d[key] = safe_num(request.form.get(key, ""))

    s["daily"] = d

    snapshot = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        **d
    }
    hist = s.get("history", [])
    if not isinstance(hist, list):
        hist = []
    hist.append(snapshot)
    s["history"] = hist[-30:]
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
