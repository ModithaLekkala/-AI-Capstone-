$ErrorActionPreference = 'Stop'

$repo = 'C:\Users\modit\Desktop\-AI-Capstone-'
Set-Location $repo

Write-Host 'Sending test traffic...'
docker exec p4-ids-dev bash -c "cd /workspace && python3 src/python/core/inject.py"