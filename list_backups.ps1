$parent = "E:\PROJECTS"
Get-ChildItem $parent -Directory | Where-Object { $_.Name -like "energy_engine_v1_backup_*" } | Sort-Object Name
