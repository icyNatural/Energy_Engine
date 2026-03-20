$date = Read-Host "Date (YYYY-MM-DD)"
$overall = Read-Host "Overall feeling (smooth/heavy/foggy/drained/light/etc)"
$matched = Read-Host "Did mode match? (y/n)"
$workload = Read-Host "Workload high? (y/n)"
$illness = Read-Host "Illness watch? (y/n)"
$rebound = Read-Host "Rebounded next day? (y/n)"
$caffeine = Read-Host "Caffeine masked fatigue? (y/n)"
$notes = Read-Host "Notes"

$matchedBool = $matched -eq "y"
$workloadBool = $workload -eq "y"
$illnessBool = $illness -eq "y"
$reboundBool = $rebound -eq "y"
$caffeineBool = $caffeine -eq "y"

python -c "import json; from engine.storage import load_list; from engine.recovery import build_recovery_report; from engine.energy import build_energy_report; from engine.phase import phase_from_effective_awake; from engine.patterns import build_pattern_report; from engine.outcomes import record_outcome; rows=load_list('data/daily_metrics.json'); row=next((r for r in rows if r.get('date')=='$date'), None); 
assert row is not None, 'Date not found in daily_metrics.json'; 
recovery=build_recovery_report(row, rows); 
energy=build_energy_report(row); 
phase=phase_from_effective_awake(row.get('effective_awake_minutes',0)).get('phase'); 
patterns=build_pattern_report(row, rows).get('patterns', []);
reflection={'overall_feeling':'$overall','matched_mode':$matchedBool,'workload_high':$workloadBool,'illness_watch':$illnessBool,'rebounded_next_day':$reboundBool,'caffeine_masked':$caffeineBool,'notes':'$notes'};
entry=record_outcome('$date', reflection, patterns, recovery['band'], energy['band'], phase);
print(json.dumps(entry, indent=2))"
