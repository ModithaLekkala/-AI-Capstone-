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

import threading
from scapy.all import sniff, IP

from batch_profiles import generate_samples, total_input_packets

TESTS = [
    {
        "name": sample["name"],
        "src_ip": sample["src_ip"],
        "expected": sample["expected"],
        "sent": 2,
    }
    for sample in generate_samples()
]

IFACE        = "veth1"       # where forwarded packets appear
CAPTURE_TIME = 15            # seconds to listen for the full 200-packet batch

# ── Packet capture ────────────────────────────────────────────────────────────
captured = []


def classify_test_result(expected, sent, forwarded):
    if expected == "DROP":
        # In the two-phase injector, a malicious flow should forward at most
        # one packet (phase 1) and be dropped in phase 2.
        predicted = "DROP" if forwarded <= 1 else "FORWARD"
        passed = predicted == expected
        verdict = "DROPPED" if passed else "FORWARDED {}/{}".format(forwarded, sent)
    else:
        # Benign flows should forward both packets (phase 1 and phase 2).
        predicted = "FORWARD" if forwarded >= sent else "DROP"
        passed = predicted == expected
        verdict = (
            "FORWARDED {}/{}".format(forwarded, sent)
            if passed else
            "ONLY {}/{} forwarded".format(forwarded, sent)
        )

    return predicted, passed, verdict


def build_confusion_matrix(results):
    matrix = {
        "TP": 0,
        "TN": 0,
        "FP": 0,
        "FN": 0,
    }

    for result in results:
        expected = result["expected"]
        predicted = result["predicted"]

        if expected == "DROP" and predicted == "DROP":
            matrix["TP"] += 1
        elif expected == "FORWARD" and predicted == "FORWARD":
            matrix["TN"] += 1
        elif expected == "FORWARD" and predicted == "DROP":
            matrix["FP"] += 1
        elif expected == "DROP" and predicted == "FORWARD":
            matrix["FN"] += 1

    return matrix


def print_confusion_matrix(matrix):
    print("\n" + "=" * 65)
    print("  CONFUSION MATRIX")
    print("  Positive class = DROP / malicious")
    print("  Negative class = FORWARD / benign")
    print("=" * 65)
    print("{:>20} {:>14} {:>14}".format("", "Pred DROP", "Pred FORWARD"))
    print("{:>20} {:>14} {:>14}".format(
        "Actual DROP",
        matrix["TP"],
        matrix["FN"]
    ))
    print("{:>20} {:>14} {:>14}".format(
        "Actual FORWARD",
        matrix["FP"],
        matrix["TN"]
    ))

    total = sum(matrix.values())
    precision = (matrix["TP"] / (matrix["TP"] + matrix["FP"])) if (matrix["TP"] + matrix["FP"]) else 0.0
    recall = (matrix["TP"] / (matrix["TP"] + matrix["FN"])) if (matrix["TP"] + matrix["FN"]) else 0.0
    specificity = (matrix["TN"] / (matrix["TN"] + matrix["FP"])) if (matrix["TN"] + matrix["FP"]) else 0.0
    f1_score = ((2 * precision * recall) / (precision + recall)) if (precision + recall) else 0.0

    print("\n  TP: {}  TN: {}  FP: {}  FN: {}".format(
        matrix["TP"], matrix["TN"], matrix["FP"], matrix["FN"]))
    print("  Precision: {:.3f}".format(precision))
    print("  Recall   : {:.3f}".format(recall))
    print("  Specificity: {:.3f}".format(specificity))
    print("  F1 Score : {:.3f}".format(f1_score))
    print("  Total    : {} tests".format(total))

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
    print("  Samples evaluated: {} | Input packets sent: {}".format(
        len(TESTS), total_input_packets()))

    correct = 0
    total   = len(TESTS)
    results = []

    for test in TESTS:
        src      = test["src_ip"]
        expected = test["expected"]
        sent     = test["sent"]
        fwd      = forwarded_by_src.get(src, 0)

        predicted, passed, verdict = classify_test_result(expected, sent, fwd)

        status = "PASS" if passed else "FAIL"
        if passed:
            correct += 1

        results.append({
            "name": test["name"],
            "expected": expected,
            "predicted": predicted,
            "sent": sent,
            "forwarded": fwd,
        })

        print("\n  {}  {}".format(status, test['name']))
        print("         Expected : {}".format(expected))
        print("         Predicted: {}".format(predicted))
        print("         Sent     : {} packets  |  Seen on veth1: {}".format(sent, fwd))
        print("         Result   : {}".format(verdict))

    accuracy = (correct / total) * 100
    print("\n" + "=" * 65)
    print("  ACCURACY: {}/{} tests correct = {:.1f}%".format(correct, total, accuracy))
    print("=" * 65)

    print_confusion_matrix(build_confusion_matrix(results))

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
    print("  Dataset: {} samples / {} injected packets".format(
        len(TESTS), total_input_packets()))
    print("  Run inject.py in another terminal NOW.")
    print("=" * 65)

    t = threading.Thread(target=capture_packets)
    t.start()
    t.join()

    verify()