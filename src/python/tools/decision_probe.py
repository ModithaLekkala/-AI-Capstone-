#!/usr/bin/env python3
import subprocess
import threading
import time
from scapy.all import Ether, IP, TCP, Raw, sendp, sniff

IFACE_IN = "veth0"
IFACE_OUT = "veth1"


def run_cli(commands):
    p = subprocess.Popen(["simple_switch_CLI"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = ("\n".join(commands) + "\n").encode("ascii")
    out, err = p.communicate(data)
    return out.decode("utf-8", errors="ignore"), err.decode("utf-8", errors="ignore")


def build_pkt(src, dst, sport, dport, length):
    payload = max(0, length - 54)
    return Ether()/IP(src=src, dst=dst)/TCP(sport=sport, dport=dport, flags="A")/Raw(load="X" * payload)

# Force a universal drop if decision_table is reached.
run_cli([
    "table_clear ingress.decision_table",
    "table_add ingress.decision_table ingress.drop 0x0&&&0x0 0x0&&&0x0 0x0&&&0x0 0x0&&&0x0 0x0&&&0x0 => 250"
])

ben_src = "10.130.1.1"
mal_src = "10.131.1.1"
cap = []


def do_cap():
    pkts = sniff(iface=IFACE_OUT, timeout=7, filter="ip and tcp")
    for p in pkts:
        if IP in p:
            cap.append(p[IP].src)


def do_inj():
    time.sleep(0.3)
    sendp(build_pkt(ben_src, "192.168.130.1", 22001, 80, 500), iface=IFACE_IN, verbose=False)
    sendp(build_pkt(mal_src, "172.16.131.1", 32001, 443, 60), iface=IFACE_IN, verbose=False)
    time.sleep(2.2)
    sendp(build_pkt(ben_src, "192.168.130.1", 22001, 80, 500), iface=IFACE_IN, verbose=False)
    sendp(build_pkt(mal_src, "172.16.131.1", 32001, 443, 60), iface=IFACE_IN, verbose=False)


t1 = threading.Thread(target=do_cap, daemon=True)
t2 = threading.Thread(target=do_inj)
t1.start()
t2.start()
t2.join()
t1.join()

ben_seen = sum(1 for s in cap if s == ben_src)
mal_seen = sum(1 for s in cap if s == mal_src)
print("decision_probe: benign_seen={} malicious_seen={} total={}".format(ben_seen, mal_seen, len(cap)))
print("Interpretation: if decision table runs in phase-2, expected around benign=1 malicious=1")
