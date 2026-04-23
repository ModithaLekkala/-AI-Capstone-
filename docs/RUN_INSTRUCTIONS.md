# How to Run the P4 IDS Project (Docker + 2 Terminals)

## Prerequisites
- Docker installed and running
- Container `p4-ids-dev` already created and available
- All Python files: `trigger.py`, `inject.py`, `verify.py`, `batch_profiles.py`
- P4 files: `main.p4`, `main.json`
- Rules file: `rules.json`

---

## Setup (One-Time)

### 1. Verify Container Exists
```bash
docker ps -a | findstr p4-ids-dev
```
If it exists, you're good. If not, create it:
```bash
docker compose up -d
```

### 2. Verify Files in Container
The files are mounted at `/workspace` inside the container. Check:
```bash
docker exec p4-ids-dev ls -la /workspace
```

---

## Running the Project (2 Terminals)

### Terminal 1: Start Switch + Capture Results
```bash
cd c:\Users\modit\Desktop\-AI-Capstone-
docker exec p4-ids-dev bash -c "cd /workspace && simple_switch main.json -i 0@switch0 -i 1@switch1 &"
sleep 2
docker exec p4-ids-dev bash -c "cd /workspace && python3 trigger.py"
sleep 1
docker exec p4-ids-dev bash -c "cd /workspace && python3 verify.py"
```

**What it does:**
- Starts the BMv2 simple_switch in background
- Loads the rules from `rules.json` into the switch
- Starts listening on veth1 and waits for packets (8 seconds)
- Will print accuracy + confusion matrix when done

**Expected Output:**
```
[*] Listening on veth1 for 8s ...
[*] Capture done. 200 TCP/IP packets seen on veth1.

=================================================================
  P4 IDS ACCURACY REPORT
=================================================================
  Samples evaluated: 100 | Input packets sent: 200
  
  [Results for each sample...]
  
=================================================================
  ACCURACY: 55/100 tests correct = 55.0%
=================================================================
  CONFUSION MATRIX
  ...TP/TN/FP/FN...
```

---

### Terminal 2: Send Test Packets
Wait ~3 seconds after Terminal 1 starts verify.py, then:
```bash
cd c:\Users\modit\Desktop\-AI-Capstone-
docker exec p4-ids-dev bash -c "cd /workspace && python3 inject.py"
```

**What it does:**
- Sends 50 benign + 50 malicious samples (100 total)
- Phase 1: Initial packets (0-0 seconds)
- Wait: 2.1 second gap for window expiry
- Phase 2: Trigger packets (after 2.1s)
- Total: 200 packets injected

**Expected Output:**
```
=== P4 IDS Packet Injector ===
Sending on interface: veth0
Samples: 100 | Total injected packets: 200

[Phase 1] Sending initial packets for 100 samples
  - Initial packet 1/100 | Benign Sample 01 | Len: 500 | PSH: False
  - Initial packet 2/100 | Benign Sample 02 | Len: 500 | PSH: True
  ...
  - Initial packet 100/100 | Malicious Sample 50 | Len: 60 | PSH: False

[Phase 2] Sending trigger packets after 2.1s window gap
  - Trigger packet 1/100 | Benign Sample 01
  ...
  - Trigger packet 100/100 | Malicious Sample 50

=== Done. Check tcpdump on veth1 for forwarded trigger packets. ===
```

---

## Key Timing

| Step | Terminal 1 | Terminal 2 | Notes |
|------|-----------|-----------|-------|
| T=0s | Start switch → trigger.py → verify.py (listening) | — | verify listens for 8 seconds |
| T=1-3s | Waiting for packets | — | Allows time for setup |
| T=3s | Still listening | Start inject.py | Begin sending 100 samples |
| T=3-6s | Capturing packets | Sending phase 1 (benign + malicious) | 100 initial packets |
| T=6-8.1s | Capturing packets | 2.1s gap (window expires) | Switch registers reset after 2s |
| T=8.1-11s | Capturing packets | Sending phase 2 (trigger packets) | 100 trigger packets |
| T=11-12s | Processing results | Done sending | verify finishes capture |
| T=12+ | PRINTS ACCURACY + CONFUSION MATRIX | — | Results displayed in Terminal 1 |

---

## Expected Results (Original Rules)

Based on previous runs with the 2-rule system:

```
=================================================================
  ACCURACY: 55/100 tests correct = 55.0%
=================================================================
  CONFUSION MATRIX
                          Pred DROP   Pred FORWARD
         Actual DROP             50              0
      Actual FORWARD              5             45

  TP: 50  TN: 5  FP: 45  FN: 0
  Precision: 0.526
  Recall   : 1.000
  Specificity: 0.1
  F1 Score : 0.690
```

---

## Troubleshooting

### Problem: "Could not connect to thrift client on port 9090"
**Solution:** The switch didn't start. Make sure it's running:
```bash
docker exec p4-ids-dev ps aux | findstr simple_switch
```
If it's not there, restart it manually in Terminal 1.

### Problem: "verify.py: No such file or directory"
**Solution:** Check that files are in the container:
```bash
docker exec p4-ids-dev ls /workspace/*.py
```

### Problem: No packets captured (0 packets on veth1)
**Solution:** 
1. Verify interfaces exist: `docker exec p4-ids-dev ip link show`
2. Check switch is listening on correct ports: `docker exec p4-ids-dev ip link show | grep switch`
3. Make sure inject.py runs AFTER verify.py starts listening

### Problem: Accuracy is 0% or 100%
**Solution:**
1. Check if rules loaded: Look for "2 reglas validas seran insertadas" in trigger.py output
2. Verify rules.json is valid JSON: `docker exec p4-ids-dev python3 -m json.tool rules.json`
3. Check main.p4 has mark_to_drop() for DROP actions

### Problem: Container crashed
**Solution:**
```bash
docker compose down
docker compose up -d
```

---

## One-Liner (Copy & Paste)

If you want to run the entire test in one command:

**Terminal 1:**
```bash
cd c:\Users\modit\Desktop\-AI-Capstone- && docker exec p4-ids-dev bash -c "cd /workspace && simple_switch main.json -i 0@switch0 -i 1@switch1 &" && sleep 2 && docker exec p4-ids-dev bash -c "cd /workspace && python3 trigger.py" && sleep 1 && docker exec p4-ids-dev bash -c "cd /workspace && python3 verify.py"
```

**Terminal 2 (start after Terminal 1 prints "Listening"):**
```bash
cd c:\Users\modit\Desktop\-AI-Capstone- && docker exec p4-ids-dev bash -c "cd /workspace && python3 inject.py"
```

---

## Project Structure

```
.
├── main.p4                  ← P4 data plane code (flow classification)
├── main.json               ← Compiled P4 binary for BMv2
├── rules.json             ← Classifier rules (ternary match table)
├── trigger.py             ← Loads rules into switch
├── inject.py              ← Sends benign + malicious test packets
├── verify.py              ← Listens, captures, scores accuracy
└── batch_profiles.py      ← Sample definitions (50 benign, 50 malicious)
```

---

## That's It!

You now have a clean, reproducible way to test the P4 IDS accuracy with the original rules.
