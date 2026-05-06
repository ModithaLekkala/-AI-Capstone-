# Terminal 2: Wait for rules to load, then inject traffic
$ErrorActionPreference = 'Stop'

$repo = 'C:\Users\modit\Desktop\-AI-Capstone-'
Set-Location $repo

Write-Host 'Waiting 3 seconds for rules to load in Terminal 1...'
Start-Sleep -Seconds 3

Write-Host 'Injecting test traffic (50 benign + 50 malicious, 2-phase)...'
docker exec p4-ids-dev bash -c "cd /workspace && python3 src/python/core/inject.py"

Write-Host 'Injection complete. Terminal 1 will finish in ~15 seconds.'
