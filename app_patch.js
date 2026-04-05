/* ================================
   BASELINE + CONFIDENCE DISPLAY
================================ */

function getBaselineInfo(history){
  const days = history?.length || 0;

  let confidence = "learning";
  if(days >= 7) confidence = "stable";
  else if(days >= 4) confidence = "building";

  return { days, confidence };
}

/* ================================
   HERO LANGUAGE MODES
================================ */

function getHeroGuidance(energyIndex){
  if(energyIndex < 40){
    return {
      mode: "low",
      title: "Keep things light",
      text: "Reduce pressure. Stay simple and steady."
    };
  }

  if(energyIndex < 70){
    return {
      mode: "steady",
      title: "You have usable range",
      text: "Good time for clean progress. Don’t overcomplicate."
    };
  }

  return {
    mode: "strong",
    title: "Capacity is open",
    text: "Move directly. Good time for focus, decisions, or expression."
  };
}

/* ================================
   INTERPRETER (MULTI-STATE)
================================ */

let primaryState = null;
let secondaryStates = [];

// allow max 2 secondary
function toggleSecondary(state){
  if(secondaryStates.includes(state)){
    secondaryStates = secondaryStates.filter(s => s !== state);
  } else {
    if(secondaryStates.length < 2){
      secondaryStates.push(state);
    }
  }
}

/* ================================
   STATE DEFINITIONS (EXPANDED)
================================ */

const STATE_MAP = {
  sad: {
    refined: "let down",
    meaning: "Something didn’t meet expectation or felt missing.",
    questions: [
      "What did I expect to happen?",
      "What feels missing right now?"
    ]
  },

  mad: {
    refined: "disrespected",
    meaning: "Something crossed a line or felt off in tone or behavior.",
    questions: [
      "What boundary felt crossed?",
      "Was it intent or how it landed?"
    ]
  },

  frustrated: {
    refined: "blocked",
    meaning: "Something is not moving how you want.",
    questions: [
      "What is stuck?",
      "What is the smallest move forward?"
    ]
  },

  tired: {
    refined: "drained",
    meaning: "Your system is low on usable energy.",
    questions: [
      "What actually needs energy right now?",
      "What can wait?"
    ]
  },

  anxious: {
    refined: "uncertain",
    meaning: "Future outcomes feel unclear or unstable.",
    questions: [
      "What am I trying to control?",
      "What is actually known?"
    ]
  },

  stressed: {
    refined: "overloaded",
    meaning: "Too many demands or pressure at once.",
    questions: [
      "What can be removed?",
      "What actually matters first?"
    ]
  },

  confused: {
    refined: "unclear",
    meaning: "You don’t yet have a clean interpretation.",
    questions: [
      "What do I actually know?",
      "What am I assuming?"
    ]
  },

  // ?? POSITIVE STATES
  good: {
    refined: "clear",
    meaning: "Things are working and making sense.",
    questions: [
      "What is working right now?",
      "How can I keep this going?"
    ]
  },

  focused: {
    refined: "locked in",
    meaning: "Your attention is stable and directed.",
    questions: [
      "What should I finish while this lasts?",
      "What deserves full focus?"
    ]
  },

  calm: {
    refined: "steady",
    meaning: "Low noise, low pressure state.",
    questions: [
      "What can I do cleanly right now?",
      "What would maintain this state?"
    ]
  }
};

/* ================================
   MULTI-STATE MERGE
================================ */

function buildStateOutput(primary, secondary){

  const base = STATE_MAP[primary];
  if(!base) return null;

  let mergedQuestions = [...base.questions];

  secondary.forEach(s => {
    const extra = STATE_MAP[s];
    if(extra){
      mergedQuestions = mergedQuestions.concat(extra.questions);
    }
  });

  return {
    refined: base.refined,
    meaning: base.meaning,
    questions: mergedQuestions.slice(0, 4) // cap
  };
}

/* ================================
   AUTO-FILL MEANING FIX
================================ */

function sendToMeaning(output){
  if(!output) return;

  document.querySelector("#meaning_state").value =
    output.refined + (secondaryStates.length ? " +" : "");

  document.querySelector("#meaning_text").value =
    output.meaning;

  document.querySelector("#meaning_questions").value =
    output.questions.join("\n");

  // ?? force tab switch
  switchTab("meaning");
}

/* ================================
   BASELINE UI INJECTION
================================ */

function renderBaselineInfo(){
  const history = JSON.parse(localStorage.getItem("energy_history") || "[]");
  const info = getBaselineInfo(history);

  const el = document.getElementById("baseline_info");
  if(el){
    el.innerText = `Baseline: ${info.days} days • ${info.confidence}`;
  }
}
