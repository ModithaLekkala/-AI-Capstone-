#!/usr/bin/env python3
"""
selftest.py — self-contained test that sends 10 benign and 10 malicious
packets inside the same process, captures on veth1, and prints a mini
confusion matrix.  Run: python3 selftest.py  (no second terminal needed)
"""
import threading
import time
from scapy.all import Ether, IP, TCP, Raw, sendp, sniff

IFACE_IN  = "veth0"
IFACE_OUT = "veth1"
CAPTURE_SEC = 12    # generous window

captured = []

# --- flow definitions --------------------------------------------------
BENIGN_FLOWS = [
    {"src": "10.1.1.{}".format(i), "dst": "192.168.1.{}".format(i),
     "sport": 20000 + i, "dport": 80, "len": 500, "psh": False}
    for i in range(1, 11)
]
MALICIOUS_FLOWS = [
    {"src": "10.2.1.{}".format(i), "dst": "172.16.1.{}".format(i),
     "sport": 30000 + i, "dport": 443, "len": 60, "psh": False}
    for i in range(1, 11)
]

def build_pkt(f, psh=False, length=None):
    if length is None:
        length = f["len"]
    payload = max(0, length - 54)
    flags = "PA" if psh else "A"
    return (Ether() /
            IP(src=f["src"], dst=f["dst"]) /
            TCP(sport=f["sport"], dport=f["dport"], flags=flags) /
            Raw(load="X" * payload))

def do_capture():
    pkts = sniff(iface=IFACE_OUT, timeout=CAPTURE_SEC, filter="ip and tcp")
    captured.extend(pkts)
    print("[capture] Done. {} packets observed on {}.".format(len(pkts), IFACE_OUT))

def do_inject():
    all_flows = BENIGN_FLOWS + MALICIOUS_FLOWS
    print("[inject] Phase 1 - sending {} initial packets".format(len(all_flows)))
    for f in all_flows:
        sendp(build_pkt(f), iface=IFACE_IN, verbose=False)
        time.sleep(0.05)

    print("[inject] Waiting 2.2s for window to expire...")
    time.sleep(2.2)

    print("[inject] Phase 2 - sending {} trigger packets".format(len(all_flows)))
    for f in all_flows:
        sendp(build_pkt(f), iface=IFACE_IN, verbose=False)
        time.sleep(0.05)

    print("[inject] Done.")

# --- main --------------------------------------------------------------
print("=" * 60)
print("  P4 IDS Self-Test (20 flows, 40 packets) - single process")
print("  Listening on {} | Injecting on {}".format(IFACE_OUT, IFACE_IN))
print("=" * 60)

cap_thread = threading.Thread(target=do_capture, daemon=True)
cap_thread.start()
time.sleep(0.3)   # let sniff() bind before first packet

inj_thread = threading.Thread(target=do_inject)
inj_thread.start()
inj_thread.join()

cap_thread.join()

# --- evaluate ----------------------------------------------------------
fwd_by_src = {}
for pkt in captured:
    if IP in pkt:
        src = pkt[IP].src
        fwd_by_src[src] = fwd_by_src.get(src, 0) + 1

print("\n  Forwarded packet counts by source IP:")
for src, cnt in sorted(fwd_by_src.items()):
    print("    {} -> {} pkt(s)".format(src, cnt))

TP = TN = FP = FN = 0
for f in BENIGN_FLOWS:
    seen = fwd_by_src.get(f["src"], 0)
    # Benign flows should be forwarded in both phases: expected count = 2.
    if seen >= 2:
        TN += 1
    else:
        FP += 1

for f in MALICIOUS_FLOWS:
    seen = fwd_by_src.get(f["src"], 0)
    # Malicious flows should be forwarded only once (phase 1) and dropped in phase 2.
    if seen <= 1:
        TP += 1
    else:
        FN += 1

correct = TP + TN
total   = len(BENIGN_FLOWS) + len(MALICIOUS_FLOWS)
accuracy = (correct / total) * 100

print("\n" + "=" * 60)
print("  ACCURACY: {}/{} = {:.1f}%".format(correct, total, accuracy))
print("=" * 60)
print("{:>20} {:>14} {:>14}".format("", "Pred DROP", "Pred FWD"))
print("{:>20} {:>14} {:>14}".format("Actual DROP",  TP, FN))
print("{:>20} {:>14} {:>14}".format("Actual FWD",   FP, TN))
precision    = TP / (TP + FP) if (TP + FP) else 0.0
recall       = TP / (TP + FN) if (TP + FN) else 0.0
specificity  = TN / (TN + FP) if (TN + FP) else 0.0
f1           = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
print("\n  TP={} TN={} FP={} FN={}".format(TP, TN, FP, FN))
print("  Precision={:.3f}  Recall={:.3f}  Specificity={:.3f}  F1={:.3f}".format(
    precision, recall, specificity, f1))
print("=" * 60)
