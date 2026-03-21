async function loadData() {

    const phase = await fetch('outputs/phase_report.json').then(r=>r.json());
    const energy = await fetch('outputs/energy_report.json').then(r=>r.json());
    const pattern = await fetch('outputs/pattern_report.json').then(r=>r.json());

    document.getElementById('content').innerHTML = 
        <div class='card'>
            <h2>Phase</h2>
            <pre>\</pre>
        </div>

        <div class='card'>
            <h2>Energy</h2>
            <pre>\</pre>
        </div>

        <div class='card'>
            <h2>Patterns</h2>
            <pre>\</pre>
        </div>
    ;
}

loadData();
