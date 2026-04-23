$ErrorActionPreference = 'Stop'

$repo = 'C:\Users\modit\Desktop\-AI-Capstone-'
Set-Location $repo

Write-Host 'Starting container if needed...'
docker start p4-ids-dev | Out-Null

Write-Host 'Resetting interfaces to expected topology (veth0<->switch0, veth1<->switch1)...'
docker exec p4-ids-dev bash -c "ip link delete veth0 2>/dev/null || true; ip link delete switch0 2>/dev/null || true; ip link delete veth1 2>/dev/null || true; ip link delete switch1 2>/dev/null || true; ip link add veth0 type veth peer name switch0; ip link add veth1 type veth peer name switch1; ip link set veth0 up; ip link set veth1 up; ip link set switch0 up; ip link set switch1 up"

Write-Host 'Recompiling current P4 program...'
docker exec p4-ids-dev bash -c "cd /workspace && p4c-bm2-ss --arch v1model -o src/p4/main.json src/p4/main.p4"

Write-Host 'Stopping any old switch instance...'
docker exec p4-ids-dev bash -c "pkill -f simple_switch || true"

Write-Host 'Starting switch on switch0/switch1...'
docker exec p4-ids-dev bash -c "cd /workspace && simple_switch src/p4/main.json -i 0@switch0 -i 1@switch1 > switch_manual.log 2>&1 &"

Start-Sleep -Seconds 2

Write-Host 'Loading rules.json...'
docker exec p4-ids-dev bash -c "cd /workspace && python3 src/python/core/trigger.py"

Write-Host 'Starting verifier. Run run_injector.ps1 in Terminal 2 now.'
docker exec p4-ids-dev bash -c "cd /workspace && python3 src/python/core/verify.py"