(function dreamObservatory() {
  "use strict";
  const energy = document.getElementById("page-energy");
  if (!energy || document.getElementById("dream-observatory")) return;
  const css = document.createElement("style");
  css.id = "dream-observatory-style";
  css.textContent = `
    #dream-observatory { border: 1px solid rgba(151,171,241,.36); }
    #dream-observatory .dream-head { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
    #dream-observatory .dream-kicker { color:#abc6ed; font-size:12px; letter-spacing:.14em; text-transform:uppercase; font-weight:800; }
    #dream-observatory .dream-sub { color:#b9c8dc; line-height:1.5; font-size:14px; margin:8px 0 16px; }
    #dream-observatory form { display:grid; gap:12px; }
    #dream-observatory label { display:grid; gap:5px; font-weight:700; font-size:13px; color:inherit; }
    #dream-observatory input, #dream-observatory select, #dream-observatory textarea {
      display:block; width:100%; padding:12px; border-radius:12px; border:1px solid rgba(166,189,224,.45);
      background:#111f35; color:#fff; font:inherit; min-width:0; 
    }
    #dream-observatory textarea { min-height:100px; resize:vertical; }
    #dream-observatory .dream-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
    #dream-observatory .dream-actions { display:flex; flex-wrap:wrap; gap:9px; align-items:center; }
    #dream-observatory button, #dream-home-shortcut button {
      appearance:none; border:1px solid rgba(175,202,242,.55); border-radius:12px; 
      padding:11px 14px; background:#18314e; color:white; cursor:pointer; font-weight:750;
    }
    #dream-observatory .dream-primary, #dream-home-shortcut button {background:#b5e3ff; color:#091b30;}
    #dream-observatory button:focus-visible, #dream-home-shortcut button:focus-visible {outline:3px solid #86ceff; outline-offset:2px;}
    #dream-observatory .dream-status { font-size:13px; min-height:20px; color:#a6dbce; }
    #dream-observatory .dream-archive { border-top:1px solid rgba(255,255,255,.18); margin-top:20px; padding-top:15px; }
    #dream-observatory .dream-entry, #dream-observatory .dream-day {
      padding:12px; margin-top:10px; border-radius:12px; background:rgba(120,156,204,.12); 
      border:1px solid rgba(160,190,235,.20); overflow-wrap:anywhere;
    }
    #dream-observatory .dream-entry h4 {margin:0 0 5px; font-size:15px;}
    #dream-observatory .dream-entry p {margin:8px 0; line-height:1.55; white-space:pre-wrap;}
    #dream-observatory .dream-meta, #dream-observatory .dream-muted { color:#aec2dc; font-size:12px; line-height:1.5; }
    #dream-observatory .dream-pill { display:inline-block; padding:3px 8px; margin:0 4px 4px 0; border-radius:30px; background:rgba(132,165,230,.18); font-size:12px; }
    #dream-observatory .dream-day {display:flex; justify-content:space-between; gap:12px; align-items:center;}
    #dream-observatory .dream-range {display:flex; align-items:center; gap:12px;}
    #dream-observatory input[type=range] {padding:0;}
    #dream-home-shortcut { border:1px solid rgba(150,185,239,.3); }
    #dream-home-shortcut .dream-shortcut-row {display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;}
    @media(max-width:560px) {
      #dream-observatory .dream-grid {grid-template-columns:1fr;}
      #dream-observatory .dream-actions button {flex:1 1 auto;}
    }`;
  document.head.appendChild(css);
  const card = document.createElement("div");
  card.id = "dream-observatory";
  card.className = "card";
  card.innerHTML = `
    <div class="dream-head">
      <div><div class="dream-kicker">Sleep · Consciousness</div><h2 style="font-size:24px;margin:6px 0 0">Dream Observatory</h2></div>
      <span class="dream-pill">Private on this device</span>
    </div>
    <p class="dream-sub">Capture your experience as soon as you wake. Reports are linked to a dated Energy Engine sleep record when one exists—not to an invented dream time or sleep stage.</p>
    <form id="dream-form">
      <div class="dream-grid">
        <label>Report date <input id="dream-date" name="date" type="date" required></label>
        <label>When did it seem to happen?
          <select id="dream-context" name="context">
            <option value="sleep-onset">Drifting off / sleep onset</option>
            <option value="awakening">Waking up</option>
            <option value="nap">Nap</option>
            <option value="during-sleep">During sleep / uncertain</option>
            <option value="unknown">Not sure</option>
          </select>
        </label>
      </div>
      <label>What happened? <textarea id="dream-report" name="report" maxlength="12000" placeholder="I was in my actual room, except..." required></textarea></label>
      <div class="dream-actions">
        <button id="dream-dictate" type="button">🎙 Dictate report</button>
        <span class="dream-muted">Dictation writes text; audio isn't stored or uploaded by Energy Engine.</span>
      </div>
      <details>
        <summary>Experience details (optional)</summary>
        <div class="dream-grid" style="margin-top:12px;">
          <label>Environment <input name="environment" maxlength="250" placeholder="Bedroom, unfamiliar place..."></label>
          <label>Senses
            <select name="senses">
              <option value="uncertain">Not sure</option>
              <option value="visual">Visual</option>
              <option value="audio">Sound</option>
              <option value="multiple">Multiple senses</option>
              <option value="other">Other</option>
            </select>
          </label>
          <label>Agency / control
            <select name="agency">
              <option value="unsure">Not sure</option>
              <option value="participant">I could act</option>
              <option value="observer">I was observing</option>
              <option value="lucid">I knew I was dreaming</option>
            </select>
          </label>
          <label>Realism <span class="dream-range"><input id="dream-realism" name="realism" type="range" min="1" max="5" value="5"><output id="dream-realism-read">5 / 5</output></span></label>
        </div>
        <label style="margin-top:12px;">Your interpretation (kept separate from observation)
          <textarea name="interpretation" maxlength="4000" placeholder="Optional: associations, questions, hypotheses..."></textarea>
        </label>
      </details>
      <div class="dream-actions">
        <button type="submit" class="dream-primary" id="dream-save">Save dream report</button>
        <button type="reset" id="dream-reset">Clear form</button>
        <span class="dream-status" id="dream-status" role="status" aria-live="polite"></span>
      </div>
    </form>
    <div class="dream-archive">
      <div class="dream-head"><h3 style="margin:0">Sleep record × Dream markers</h3><span class="dream-muted">Date-linked, not EEG-positioned</span></div>
      <div id="dream-timeline"></div>
    </div>
    <div class="dream-archive">
      <div class="dream-head">
        <h3 style="margin:0">Your reports</h3>
        <button id="dream-export" type="button">Export dream archive (JSON)</button>
      </div>
      <div id="dream-list"></div>
    </div>
    <p class="dream-muted" style="margin-top:14px">Sleep stages shown elsewhere in Energy Engine are recorded inputs or estimates. A watch cannot determine when a specific dream occurred. Reports are included in the existing Energy Engine backup.</p>`;
  const baseline = document.getElementById("baselineReadWrap")?.closest(".card");
  if (baseline) energy.insertBefore(card, baseline);
  else energy.appendChild(card);
  const home = document.getElementById("page-home");
  if (home) {
    const quick = document.createElement("div");
    quick.id = "dream-home-shortcut";
    quick.className = "card";
    quick.innerHTML = `<div class="dream-shortcut-row"><div><strong>Dream / Sleep experience</strong><p class="muted" style="margin:5px 0 0">Catch what you experienced before it fades.</p></div><button id="dream-quick-capture" type="button">Capture experience</button></div>`;
    const hero = home.querySelector(".hero");
    if (hero) hero.insertAdjacentElement("afterend", quick);
    else home.prepend(quick);
    quick.querySelector("button").addEventListener("click", () => {
      if (typeof switchPage === "function") switchPage("energy");
      document.querySelectorAll(".desktop-side-nav button").forEach(el => el.classList.toggle("active", el.dataset.page === "energy"));
      card.scrollIntoView({behavior:"smooth",block:"start"});
      document.getElementById("dream-report").focus({preventScroll:true});
    });
  }
  const form = document.getElementById("dream-form");
  const list = document.getElementById("dream-list");
  const timeline = document.getElementById("dream-timeline");
  const status = document.getElementById("dream-status");
  const dateField = document.getElementById("dream-date");
  function localDate(d = new Date()) {
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  }
  dateField.value = localDate();
  function loadCore() { try { return loadState(); } catch { return null; } }
  function reports(state) { return Array.isArray(state?.dream_reports) ? state.dream_reports : []; }
  const validDate = s => /^\d{4}-\d{2}-\d{2}$/.test(s);
  const briefMinutes = value => {
    const n = Number(value);
    if (!Number.isFinite(n) || n < 0) return "Sleep not logged";
    return `Sleep logged: ${Math.floor(n/60)}h ${Math.round(n%60)}m`;
  };
  const labelFor = { "sleep-onset":"Sleep onset", "awakening":"Awakening", "nap":"Nap", "during-sleep":"During sleep (uncertain)", "unknown":"Uncertain" };
  function makeText(tag,text,className) {
    const el=document.createElement(tag);
    if(className) el.className=className;
    el.textContent=text;
    return el;
  }
  function renderArchive() {
    const state=loadCore();
    const entries=reports(state).slice().sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt)));
    list.replaceChildren();
    if(!entries.length) list.appendChild(makeText("p","No reports saved yet. Your first observation starts here.","dream-muted"));
    for (const entry of entries.slice(0,20)) {
      const item=document.createElement("article");
      item.className="dream-entry";
      const title=makeText("h4",`${entry.date} · ${labelFor[entry.context]||"Uncertain"}`);
      const when=makeText("div",`Reported ${new Date(entry.createdAt).toLocaleString()} · Realism ${entry.realism}/5 · ${entry.agency||"unsure"} agency`,"dream-meta");
      const body=makeText("p",entry.report||"");
      item.append(title,when,body);
      if(entry.environment) item.appendChild(makeText("div",`Environment: ${entry.environment}`,"dream-muted"));
      if(entry.interpretation) item.appendChild(makeText("p",`Interpretation: ${entry.interpretation}`,"dream-muted"));
      const actions=document.createElement("div");actions.className="dream-actions";
      const edit=document.createElement("button"); edit.type="button";edit.textContent="Edit"; edit.addEventListener("click",()=>editEntry(entry));
      const del=document.createElement("button"); del.type="button"; del.textContent="Delete";del.addEventListener("click",()=>deleteEntry(entry.id));
      actions.append(edit,del);item.appendChild(actions);list.appendChild(item);
    }
    if(entries.length>20) list.appendChild(makeText("p",`Showing latest 20 of ${entries.length}. Export to see the complete archive.`,"dream-muted"));
    timeline.replaceChildren();
    const byDate=new Map();
    for(const entry of entries) if(validDate(entry.date)) byDate.set(entry.date,(byDate.get(entry.date)||0)+1);
    const recentHistory=Array.isArray(state?.history)?state.history.filter(x=>validDate(x.date)).slice(-7):[];
    const dates=new Set([localDate(),...recentHistory.map(x=>x.date),...entries.slice(0,7).map(x=>x.date)]);
    for(const date of [...dates].filter(validDate).sort().reverse().slice(0,7)) {
      const snapshot=recentHistory.find(x=>x.date===date)||(
        date===localDate()?state?.daily:null
      );
      const row=document.createElement("div"); row.className="dream-day";
      const left=document.createElement("div");
      left.appendChild(makeText("strong",date));
      left.appendChild(makeText("div",briefMinutes(snapshot?.actual_sleep_minutes),"dream-muted"));
      row.append(left,makeText("span",`${byDate.get(date)||0} dream report${byDate.get(date)===1?"":"s"}`,"dream-pill"));
      timeline.appendChild(row);
    }
  }
  function editEntry(entry) {
    dateField.value=entry.date;
    form.elements.context.value=entry.context;
    form.elements.report.value=entry.report;
    form.elements.environment.value=entry.environment||"";
    form.elements.senses.value=entry.senses||"uncertain";
    form.elements.agency.value=entry.agency||"unsure";
    form.elements.realism.value=entry.realism||5;
    form.elements.interpretation.value=entry.interpretation||"";
    form.dataset.editId=entry.id;
    document.getElementById("dream-save").textContent="Save changes";
    document.getElementById("dream-realism-read").textContent=`${form.elements.realism.value} / 5`;
    form.scrollIntoView({behavior:"smooth",block:"start"});
    form.elements.report.focus({preventScroll:true});
  }
  function deleteEntry(id) {
    if(!window.confirm("Delete this dream report from this browser?"))return;
    const state=loadCore();if(!state)return;
    state.dream_reports=reports(state).filter(x=>x.id!==id);
    try{saveState(state);renderArchive();status.textContent="Report deleted.";}catch{status.textContent="Could not save deletion.";}
  }
  form.addEventListener("submit",event=>{
    event.preventDefault();
    const state=loadCore();
    if(!state){status.textContent="Storage unavailable. Report not saved.";return;}
    const data=new FormData(form);
    const report=String(data.get("report")||"").trim();
    const date=String(data.get("date")||"");
    if(!report||!validDate(date)){status.textContent="Add a report and valid date.";return;}
    const current=reports(state).slice();
    const id=form.dataset.editId||(
      window.crypto?.randomUUID?.()||`${Date.now()}-${Math.random().toString(36).slice(2)}`
    );
    const prior=current.find(e=>e.id===id);
    const entry={
      id,date,createdAt:prior?.createdAt||new Date().toISOString(),updatedAt:new Date().toISOString(),
      context:String(data.get("context")||"unknown"),
      report,environment:String(data.get("environment")||"").trim(),
      senses:String(data.get("senses")||"uncertain"),
      agency:String(data.get("agency")||"unsure"),
      realism:Number(data.get("realism")||5),
      interpretation:String(data.get("interpretation")||"").trim(),
      connection:"Same local calendar date as logged sleep data, if present; no precise sleep-stage timestamp"
    };
    const next=current.filter(e=>e.id!==id); next.push(entry);
    state.dream_reports=next.slice(-300);
    try {
      saveState(state);
      form.reset();dateField.value=localDate();delete form.dataset.editId;
      document.getElementById("dream-save").textContent="Save dream report";
      document.getElementById("dream-realism-read").textContent="5 / 5";
      status.textContent="Report saved locally and included in Energy Engine backups.";
      renderArchive();
    }catch(e){status.textContent="Save failed. Browser storage may be full or disabled.";}
  });
  form.addEventListener("reset",()=>{
    delete form.dataset.editId;
    document.getElementById("dream-save").textContent="Save dream report";
    requestAnimationFrame(()=>{dateField.value=localDate();document.getElementById("dream-realism-read").textContent="5 / 5";});
  });
  document.getElementById("dream-realism").addEventListener("input",e=>{
    document.getElementById("dream-realism-read").textContent=`${e.target.value} / 5`;
  });
  const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  const dictation=document.getElementById("dream-dictate");
  if(!SpeechRecognition) {
    dictation.textContent="Voice dictation unavailable";
    dictation.disabled=true;
    dictation.title="Use your keyboard microphone or type the report.";
  } else {
    let active=null;
    dictation.addEventListener("click",()=>{
      if(active){active.stop();return;}
      const rec=new SpeechRecognition();active=rec;rec.lang="en-US";rec.interimResults=false;rec.continuous=false;
      rec.onresult=e=>{
        const words=Array.from(e.results).map(x=>x[0].transcript).join(" ").trim();
        const area=document.getElementById("dream-report");
        area.value=[area.value.trim(),words].filter(Boolean).join(" ");
        status.textContent="Dictation added. Review the words before saving.";
      };
      rec.onerror=e=>{status.textContent=`Dictation unavailable: ${e.error||"microphone error"}. You can type instead.`;};
      rec.onend=()=>{active=null;dictation.textContent="🎙 Dictate report";};
      try{rec.start();dictation.textContent="Stop dictation";status.textContent="Listening...";}catch{active=null;status.textContent="Could not start dictation.";}
    });
  }
  document.getElementById("dream-export").addEventListener("click",()=>{
    const state=loadCore(),all=reports(state);
    const blob=new Blob([JSON.stringify({format:"icy-energy-dream-observatory",version:1,exportedAt:new Date().toISOString(),reports:all},null,2)],{type:"application/json"});
    const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=`icy-dream-reports-${localDate()}.json`;
    document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    status.textContent=`Exported ${all.length} report${all.length===1?"":"s"}.`;
  });
  // No private dream content is part of source files or sent to GitHub.
  renderArchive();
})();