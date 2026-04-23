#!/usr/bin/env python3
"""Sweep candidate win_maxlength values for malicious drop rule.
For each candidate, program table entries and run a 1-benign / 1-malicious 2-phase test.
"""
import subprocess
import threading
import time
from scapy.all import Ether, IP, TCP, Raw, sendp, sniff

IFACE_IN = "veth0"
IFACE_OUT = "veth1"


def build_pkt(src, dst, sport, dport, length):
    payload = max(0, length - 54)
    return Ether()/IP(src=src, dst=dst)/TCP(sport=sport, dport=dport, flags="A")/Raw(load="X" * payload)


def run_cli(commands):
    p = subprocess.Popen(["simple_switch_CLI"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = ("\n".join(commands) + "\n").encode("ascii")
    out, err = p.communicate(data)
    return out.decode("utf-8", errors="ignore"), err.decode("utf-8", errors="ignore")


def program_rules(drop_len):
    cmds = [
        "table_clear ingress.decision_table",
        "table_add ingress.decision_table ingress.drop {}&&&0xffffffff 0x0&&&0x0 0x0&&&0x0 0x0&&&0x0 0x1&&&0xffffffff => 200".format(hex(drop_len)),
        "table_add ingress.decision_table ingress.forward 0x0&&&0x0 0x0&&&0x0 0x0&&&0x0 0x0&&&0x0 0x1&&&0xffffffff => 100",
    ]
    run_cli(cmds)


def run_pair(case_id):
    # unique IPs per case so register state from prior cases does not interfere
    ben_src = "10.120.{}.1".format(case_id)
    mal_src = "10.121.{}.1".format(case_id)
    ben_dst = "192.168.120.1"
    mal_dst = "172.16.121.1"

    captured = []

    def cap():
        pkts = sniff(iface=IFACE_OUT, timeout=7, filter="ip and tcp")
        for p in pkts:
            if IP in p:
                captured.append(p[IP].src)

    def inj():
        time.sleep(0.3)
        sendp(build_pkt(ben_src, ben_dst, 21000 + case_id, 80, 500), iface=IFACE_IN, verbose=False)
        sendp(build_pkt(mal_src, mal_dst, 31000 + case_id, 443, 60), iface=IFACE_IN, verbose=False)
        time.sleep(2.2)
        sendp(build_pkt(ben_src, ben_dst, 21000 + case_id, 80, 500), iface=IFACE_IN, verbose=False)
        sendp(build_pkt(mal_src, mal_dst, 31000 + case_id, 443, 60), iface=IFACE_IN, verbose=False)

    t1 = threading.Thread(target=cap, daemon=True)
    t2 = threading.Thread(target=inj)
    t1.start()
    t2.start()
    t2.join()
    t1.join()

    ben_seen = sum(1 for s in captured if s == ben_src)
    mal_seen = sum(1 for s in captured if s == mal_src)
    return ben_seen, mal_seen, len(captured)


def main():
    # common candidates: L2+L3+L4 sizes often around these values for this profile
    candidates = [40, 46, 54, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90]
    print("len_sweep: testing {} candidates".format(len(candidates)))
    print("expected success pattern: benign_seen=2 and malicious_seen=1")
    print("-" * 72)

    good = []
    for idx, cand in enumerate(candidates, start=1):
        program_rules(cand)
        ben_seen, mal_seen, total = run_pair(idx)
        ok = (ben_seen == 2 and mal_seen == 1)
        status = "MATCH" if ok else "no"
        print("len={:>3} -> benign={} malicious={} total={} [{}]".format(cand, ben_seen, mal_seen, total, status))
        if ok:
            good.append(cand)

    print("-" * 72)
    if good:
        print("BEST_CANDIDATES={}".format(good))
    else:
        print("BEST_CANDIDATES=[]")


if __name__ == "__main__":
    main()
