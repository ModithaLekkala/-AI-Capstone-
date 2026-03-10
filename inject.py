#inject.py
#!/usr/bin/env python3
# -- coding: utf-8 --

from scapy.all import Ether, IP, TCP, Raw, sendp, wrpcap
import time
import random
import os

# === CONFIGURATION ===
IFACE = "veth0"  # Make sure this is your input interface to the P4 switch
DUMP_PCAPS = True  # Set to False if you do not want to save .pcap files

def craft_packet(flow_def, length, psh=False, seq=None):
    BASE_LEN = 54  # Ethernet + IP + TCP headers
    length = max(length, BASE_LEN)
    payload_size = length - BASE_LEN

    flags = 'PA' if psh else 'A'
    if seq is None:
        seq = random.randint(0, 10000)

    return (
        Ether(src="00:11:22:33:44:55", dst="00:AA:BB:CC:DD:EE") /
        IP(src=flow_def["src_ip"], dst=flow_def["dst_ip"]) /
        TCP(sport=flow_def["sport"], dport=flow_def["dport"], flags=flags, seq=seq) /
        Raw(load=b'X' * payload_size)
    )

def send_sequence(packet_sequence, flow_def, delay=1.0, pcap_name=None):
    pkts = []
    for i, p in enumerate(packet_sequence):
        pkt = craft_packet(flow_def, p["len"], p.get("psh", False))
        print(f"  - Sending packet {i+1}/{len(packet_sequence)} | Len: {p['len']} | PSH: {p.get('psh', False)}")
        sendp(pkt, iface=IFACE, verbose=False)
        pkts.append(pkt)
        time.sleep(delay)

    print("  - Sending final trigger packet...")
    trigger_pkt = craft_packet(flow_def, 64)
    sendp(trigger_pkt, iface=IFACE, verbose=False)
    pkts.append(trigger_pkt)

    if DUMP_PCAPS and pcap_name:
        wrpcap(pcap_name, pkts)
        print(f"  [PCAP] Saved as {pcap_name}")

def run_rule_a():
    print("\n[Rule A] 5 packets of 270B, no PSH (Low-rate DoS)")
    flow = {"src_ip": "10.0.1.1", "dst_ip": "192.168.1.1", "sport": 1234, "dport": 80}
    seq = [{"len": 270, "psh": False}] * 5
    send_sequence(seq, flow, pcap_name="rule_a.pcap")

def run_rule_b():
    print("\n[Rule B] 3 packets (100, 150, 200B), 2 with PSH (Mixed Profile)")
    flow = {"src_ip": "10.0.9.1", "dst_ip": "192.168.9.9", "sport": 9999, "dport": 443}
    seq = [{"len": 100, "psh": True}, {"len": 150, "psh": False}, {"len": 200, "psh": True}]
    send_sequence(seq, flow, pcap_name="rule_b.pcap")

def run_tree_rule_1():
    print("\n[Tree Rule 1] 11 packets of 1400B without PSH (Tree-based Case)")
    flow = {"src_ip": "10.0.2.1", "dst_ip": "192.168.2.2", "sport": 5678, "dport": 22}
    seq = [{"len": 1400, "psh": False}] * 11
    send_sequence(seq, flow, pcap_name="tree_rule_1.pcap")

def run_normal_packets():
    print("\n[Normal Packets] 5 packets (130, 200, 300, 150, 250B), all without PSH (Benign)")
    flow = {"src_ip": "10.0.10.1", "dst_ip": "192.168.10.10", "sport": 8888, "dport": 8080}
    seq = [{"len": l, "psh": False} for l in [130, 200, 300, 150, 250]]
    send_sequence(seq, flow, pcap_name="normal_packets.pcap")

if __name__ == "__main__":
    print("=== TEST SCENARIO INJECTOR FOR P4 ===")
    print("1) Rule A (Low-rate DoS)")
    print("2) Rule B (Mixed Profile)")
    print("3) Tree Rule 1 (11 large packets)")
    print("4) Normal packets (Benign test, should not match any rule)")
    choice = input("Select an option (1-4): ").strip()

    if choice == "1":
        run_rule_a()
    elif choice == "2":
        run_rule_b()
    elif choice == "3":
        run_tree_rule_1()
    elif choice == "4":
        run_normal_packets()
    else:
        print("Invalid option.")
