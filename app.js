async function load(){

const phase = await fetch('outputs/phase_report.json').then(r=>r.json());
const energy = await fetch('outputs/energy_report.json').then(r=>r.json());
const pattern = await fetch('outputs/pattern_report.json').then(r=>r.json());

document.getElementById('phaseCard').innerHTML = 
<div class="title">Current Phase</div>
<div class="value">\</div>
;

document.getElementById('energyCard').innerHTML = 
<div class="title">Energy Score</div>
<div class="value">\</div>
;

document.getElementById('patternCard').innerHTML = 
<div class="title">Dominant Pattern</div>
<div class="value">\</div>
;

}

load();
