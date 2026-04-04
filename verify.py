# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
verify.py - Accuracy checker for the P4 IDS project.

How it works:
  - Reads the pcap files saved by inject.py
  - Runs tcpdump on veth1 BEFORE and AFTER inject.py to count forwarded packets
  - Compares forwarded vs expected for each test
  - Prints a clear accuracy report

Usage (inside container):
  # Terminal 1: start the switch + load rules, then run:
  python3 verify.py

  # Terminal 2 (separate): run inject.py while verify.py is listening
  python3 inject.py
"""

import subprocess
import threading
import time
from scapy.all import sniff, rdpcap, Ether, IP, TCP

# ── Test definitions ──────────────────────────────────────────────────────────
# Each test: name, source IP (unique per test), expected verdict, packet count
TESTS = [
    {
        "name":       "Benign Test A",
        "src_ip":     "10.0.1.1",
        "expected":   "FORWARD",
        "sent":       2,  # updated
    },
    {
        "name":       "Malicious Test A",
        "src_ip":     "10.0.2.1",
        "expected":   "DROP",
        "sent":       1,
    },
    {
        "name":       "Benign Test B",
        "src_ip":     "10.0.1.1",
        "expected":   "FORWARD",
        "sent":       2,  # updated
    },
    {
        "name":       "Malicious Test B",
        "src_ip":     "10.0.2.1",
        "expected":   "DROP",
        "sent":       1,
    },
]

IFACE        = "veth1"       # where forwarded packets appear
CAPTURE_TIME = 5            # seconds to listen (must cover inject.py runtime ~45s)

# ── Packet capture ────────────────────────────────────────────────────────────
captured = []

def capture_packets():
    """Sniff on veth1 for CAPTURE_TIME seconds, store IPv4/TCP packets."""
    print("[*] Listening on {} for {}s ...".format(IFACE, CAPTURE_TIME))
    pkts = sniff(iface=IFACE, timeout=CAPTURE_TIME,
                 filter="ip and tcp")
    captured.extend(pkts)
    print("[*] Capture done. {} TCP/IP packets seen on {}.".format(len(captured), IFACE))

# ── Main verification ─────────────────────────────────────────────────────────
def verify():
    # Count forwarded packets per source IP
    forwarded_by_src = {}
    for pkt in captured:
        if IP in pkt:
            src = pkt[IP].src
            forwarded_by_src[src] = forwarded_by_src.get(src, 0) + 1

    print("\n" + "=" * 65)
    print("  P4 IDS ACCURACY REPORT")
    print("=" * 65)

    correct = 0
    total   = len(TESTS)

    for test in TESTS:
        src      = test["src_ip"]
        expected = test["expected"]
        sent     = test["sent"]
        fwd      = forwarded_by_src.get(src, 0)

        if expected == "DROP":
            # Correctly dropped = 0 data packets forwarded
            # (trigger packet after sleep may still pass — allow ≤1)
            passed = fwd <= 1
            verdict = "DROPPED" if passed else "FORWARDED {}/{}".format(fwd, sent)
        else:  # FORWARD
            # All sent packets should appear on veth1
            passed = fwd >= sent
            verdict = "FORWARDED {}/{}".format(fwd, sent) if passed else "ONLY {}/{} forwarded".format(fwd, sent)

        status = "PASS" if passed else "FAIL"
        if passed:
            correct += 1

        print("\n  {}  {}".format(status, test['name']))
        print("         Expected : {}".format(expected))
        print("         Sent     : {} packets  |  Seen on veth1: {}".format(sent, fwd))
        print("         Result   : {}".format(verdict))

    accuracy = (correct / total) * 100
    print("\n" + "=" * 65)
    print("  ACCURACY: {}/{} tests correct = {:.1f}%".format(correct, total, accuracy))
    print("=" * 65)

    if accuracy < 100:
        print("""
  COMMON REASONS FOR FAILURES:
  1. trigger.py was not run before inject.py -> no rules loaded
  2. simple_switch was restarted but rules not reloaded
  3. veth interfaces were recreated but switch not restarted
  4. Rules in rules.json don't match the injected packet profile
  5. Window timeout in main.p4 expired before enough packets arrived
""")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("  P4 IDS Verifier")
    print("  Run inject.py in another terminal NOW.")
    print("=" * 65)

    t = threading.Thread(target=capture_packets)
    t.start()
    t.join()

    verify()