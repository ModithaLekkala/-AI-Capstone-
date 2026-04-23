# Terminal 1: Setup, compile, start switch, load rules, start verifier
$ErrorActionPreference = 'Stop'

$repo = 'C:\Users\modit\Desktop\-AI-Capstone-'
Set-Location $repo

Write-Host 'Starting container...'
docker start p4-ids-dev | Out-Null

Write-Host 'Resetting interface topology...'
docker exec p4-ids-dev bash -c "ip link delete veth0 2>/dev/null || true; ip link delete switch0 2>/dev/null || true; ip link delete veth1 2>/dev/null || true; ip link delete switch1 2>/dev/null || true; ip link add veth0 type veth peer name switch0; ip link add veth1 type veth peer name switch1; ip link set veth0 up; ip link set veth1 up; ip link set switch0 up; ip link set switch1 up"

Write-Host 'Compiling P4...'
docker exec p4-ids-dev bash -c "cd /workspace && p4c-bm2-ss --arch v1model -o src/p4/main.json src/p4/main.p4"

Write-Host 'Starting switch...'
docker exec p4-ids-dev bash -c "pkill -9 -f simple_switch || true"
docker exec p4-ids-dev bash -c "cd /workspace && simple_switch src/p4/main.json -i 0@switch0 -i 1@switch1 > switch_manual.log 2>&1 &"
Start-Sleep -Seconds 2

Write-Host 'Loading rules into table...'
docker exec p4-ids-dev bash -c "cd /workspace && python3 src/python/core/trigger.py > trigger_manual.log 2>&1"

Write-Host '[RULES LOADED] Starting packet verifier on veth1 (15s capture window)...'
docker exec p4-ids-dev bash -c "cd /workspace && python3 src/python/core/verify.py > verify_manual.log 2>&1 &"

Write-Host '[WAITING] Verifier started in background. Now run Terminal 2: run_injector_custom.ps1'
Write-Host 'Waiting for verification to complete (20s timeout)...'
Start-Sleep -Seconds 20

Write-Host '===== RESULTS ====='
docker exec p4-ids-dev bash -c "cd /workspace && tail -50 verify_manual.log"
