from flask import Flask, request, redirect
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / "state.json"
DASHBOARD_PATH = BASE_DIR / "outputs" / "dashboard.json"


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
    }


def load_state():
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = default_state()
                base.update(data)
                return base
        except Exception:
            pass
    return default_state()


def save_state(state: dict):
    state["last_updated_ts"] = now_ts()
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ----------------------------
# DASHBOARD DATA
# ----------------------------
def run_report():
    subprocess.run(["python", "app.py", "report"], cwd=BASE_DIR, check=False)


def load_dashboard():
    run_report()
    if not DASHBOARD_PATH.exists():
        return {}
    try:
        return json.loads(DASHBOARD_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


# ----------------------------
# TIME HELPERS
# ----------------------------
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

    # If entered time is in the future, treat it as yesterday.
    if dt.timestamp() > time.time():
        dt = dt - timedelta(days=1)

    return int(dt.timestamp())


def compute_nap_duration(state: dict) -> int:
    start_ts = state.get("nap_start_ts")
    wake_ts = state.get("nap_wake_ts")
    if start_ts and wake_ts and wake_ts >= start_ts:
        return int((wake_ts - start_ts) / 60)
    return 0


# ----------------------------
# NAP EFFECT FORMULAS
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
# PHASE LOGIC
# ----------------------------
def phase_from_effective_awake(effective_awake_min: int, extension_min: int = 0):
    if effective_awake_min is None:
        return ("⏳", "Untracked", "Set wake to begin.")

    recovery_end = 4 * 60
    flow_end = 10 * 60 + extension_min
    radiance_end = 14 * 60 + extension_min
    surge_end = 18 * 60 + round(extension_min * 0.6)

    if effective_awake_min < recovery_end:
        return (
            "🌑",
            "Recovery",
            "System rebuilds quietly.",
        )
    elif effective_awake_min < flow_end:
        return (
            "🌊",
            "Flow",
            "Movement continues without resistance.",
        )
    elif effective_awake_min < radiance_end:
        return (
            "☀️",
            "Radiance",
            "The sun shines unhindered.",
        )
    elif effective_awake_min < surge_end:
        return (
            "⚡",
            "Surge",
            "Energy expands beyond demand.",
        )
    else:
        return (
            "🌙",
            "Settle",
            "System begins to quiet.",
        )


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
# UI
# ----------------------------
@app.route("/")
def home():
    state = load_state()
    dash = load_dashboard()

    energy = dash.get("energy", {})
    recovery = dash.get("recovery", {})
    patterns = dash.get("patterns", {})

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
    e_score = energy.get("score", 0)
    try:
        e_pct = max(0, min(100, float(e_score)))
    except Exception:
        e_pct = 0

    pattern_items = patterns.get("patterns", [])
    pattern_count = len(pattern_items)

    if pattern_items:
        pattern_html = ""
        for p in pattern_items[:2]:
            pattern_html += f"""
            <div class="mini-box">
                <div class="mini-title-row">
                    <div class="mini-title">{p.get("title", "Pattern")}</div>
                    <div class="tag">{p.get("pattern_presence_label", "")}</div>
                </div>
                <div class="mini-text">{p.get("meaning", "")}</div>
            </div>
            """
    else:
        pattern_html = '<div class="muted">No active patterns.</div>'

    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Energy Engine</title>
      <style>
        * {{
          box-sizing: border-box;
        }}
        body {{
          margin: 0;
          padding: 16px;
          background: #081225;
          color: #f8fafc;
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        }}
        .wrap {{
          max-width: 560px;
          margin: 0 auto;
        }}
        .card {{
          background: #0c1830;
          border: 1px solid rgba(255,255,255,0.04);
          border-radius: 24px;
          padding: 18px;
          margin-bottom: 14px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.22);
        }}
        .hero {{
          padding-top: 20px;
        }}
        .phase-row {{
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;
        }}
        .emoji {{
          font-size: 34px;
          line-height: 1;
        }}
        .phase {{
          font-size: 46px;
          line-height: 1;
          font-weight: 800;
          margin: 0;
          color: white;
        }}
        .sub {{
          font-size: 16px;
          color: #dbe4ef;
          line-height: 1.45;
          margin-top: 4px;
        }}
        .stats {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-top: 16px;
        }}
        .stat {{
          background: rgba(255,255,255,0.03);
          border-radius: 16px;
          padding: 12px;
        }}
        .stat-label {{
          font-size: 12px;
          color: #94a3b8;
          margin-bottom: 4px;
        }}
        .stat-value {{
          font-size: 16px;
          font-weight: 700;
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
          border-radius: 16px;
          padding: 13px 16px;
          font-size: 16px;
          font-weight: 700;
          cursor: pointer;
        }}
        .btn-primary {{
          background: white;
          color: #081225;
        }}
        .btn-ghost {{
          background: rgba(255,255,255,0.08);
          color: white;
        }}
        .title {{
          font-size: 17px;
          font-weight: 800;
          margin-bottom: 10px;
        }}
        .big {{
          font-size: 34px;
          font-weight: 800;
          line-height: 1.05;
          margin-bottom: 8px;
        }}
        .text {{
          font-size: 16px;
          line-height: 1.45;
          color: #dbe4ef;
        }}
        .muted {{
          font-size: 14px;
          line-height: 1.45;
          color: #94a3b8;
          margin-top: 6px;
        }}
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
          width: {e_pct}%;
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
        .mini-title {{
          font-size: 15px;
          font-weight: 800;
        }}
        .mini-text {{
          font-size: 14px;
          color: #dbe4ef;
          line-height: 1.4;
        }}
        .tag {{
          padding: 4px 10px;
          border-radius: 999px;
          background: rgba(255,255,255,0.08);
          font-size: 12px;
          font-weight: 700;
          color: white;
          white-space: nowrap;
        }}
        .section-gap {{
          margin-top: 16px;
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
          <div class="muted">Use HHMM or HH:MM</div>
          <form method="post" action="/wake_set" class="inline-form">
            <input name="hhmm" placeholder="0930 or 09:30">
            <button class="btn btn-ghost" type="submit">Set Wake</button>
          </form>
        </div>

        <div class="card">
          <div class="title">Energy</div>
          <div class="big">{energy.get("state_label", "—")}</div>
          <div class="text">{energy.get("meaning", "")}</div>
          <div class="muted">{energy.get("guidance", "")}</div>
          <div class="bar"><div class="fill"></div></div>
          <div class="muted">Energy index: {energy.get("score", "—")}/100</div>
        </div>

        <div class="card">
          <div class="title">Recovery</div>
          <div class="big">{recovery.get("state_label", "—")}</div>
          <div class="text">{recovery.get("meaning", "")}</div>
          <div class="muted">{recovery.get("guidance", "")}</div>
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

          <form method="post" action="/nap_manual" class="section-gap">
            <div class="muted">Set nap manually with start and wake times</div>
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
          <div class="text">{patterns.get("summary", "—")}</div>
          {pattern_html}
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
