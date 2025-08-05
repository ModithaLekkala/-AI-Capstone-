#!/usr/bin/env python3

import argparse
from scapy.all import rdpcap, sendp, sniff, conf
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP, UDP
from collections import defaultdict

def extract_5tuple(pkt):
    if IP not in pkt:
        return None

    ip_layer = pkt[IP]
    proto = ip_layer.proto
    sport = dport = 0

    if proto == 6 and pkt.haslayer(TCP):  # TCP
        sport = pkt[TCP].sport
        dport = pkt[TCP].dport
    elif proto == 17 and pkt.haslayer(UDP):  # UDP
        sport = pkt[UDP].sport
        dport = pkt[UDP].dport

    return (ip_layer.src, ip_layer.dst, sport, dport, proto)

def group_packets_by_flow(packets):
    flow_data = defaultdict(lambda: {"packets": []})

    for pkt in packets:
        key = extract_5tuple(pkt)
        if key:
            flow_data[key]["packets"].append(pkt)

    return flow_data

def main():
    parser = argparse.ArgumentParser(description="Send packets from PCAP to Tofino and wait for replies")
    parser.add_argument("--pcap", help="Path to the input PCAP file")
    parser.add_argument("--count", default=10, type=int, help="Number of packets to load from the PCAP")
    parser.add_argument("--iface", default="h1-eth1", help="Interface to send on")
    parser.add_argument("--src-mac", default="00:00:0a:00:00:01", help="Source MAC address to set")
    parser.add_argument("--dst-mac", default="00:00:0a:00:00:02", help="Destination MAC address to set")
    parser.add_argument("--num-flows", type=int, default=1, help="Number of flows to extract")
    parser.add_argument("--packets-per-flow", type=int, default=8, help="Packets per flow to keep")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout waiting for response")
    
    args = parser.parse_args()
    print("\n" + "*-" * 45)
    print(f"Loading packets from {args.pcap}...")
    all_packets = rdpcap(args.pcap, count=args.count)

    print("Grouping packets by 5-tuple flows...\n")
    flows = group_packets_by_flow(all_packets)
    print(f"Total flows found: {len(flows)}")

    selected_flows = list(flows.items())[:args.num_flows]
    selected_packets = []

    for flow_key, flow_info in selected_flows:
        trimmed_pkts = flow_info["packets"][:args.packets_per_flow]
        selected_packets.extend(trimmed_pkts)
        print(f"\nFlow {flow_key}: Using {len(trimmed_pkts)} packets")

    print("*-" * 45 + "\n")

    if not selected_packets:
        print("No packets to send.")
        return

    conf.iface = args.iface
    print(f"Sending packets on {args.iface}...\n")

    total_sent_bytes = 0

    for i, pkt in enumerate(selected_packets):
        print(f"[Packet {i+1}] Preparing...")

        if not pkt.haslayer(Ether):
            pkt = Ether(src=args.src_mac, dst=args.dst_mac) / pkt[IP]
        else:
            pkt[Ether].src = args.src_mac
            pkt[Ether].dst = args.dst_mac

        pkt_len = len(pkt)
        # Minimum Ethernet frame size + 4 bytes for Ether CRC 
        if pkt_len <= 60:  
            pkt_len = 64
        else:
            pkt_len+= 4
        
        total_sent_bytes += pkt_len

        print(f"[Packet {i+1}] Sending ({pkt_len} bytes): {pkt.summary()}")

        try:
            sendp(pkt, iface=args.iface, verbose=False)
            sniff(iface=args.iface, timeout=args.timeout, count=1)
        except Exception as e:
            print(f"[Packet {i+1}] Error: {e}")

    avg_pkt_size = total_sent_bytes // len(selected_packets)

    print("\n" + "*-" * 45)
    print(f"Total Packets Sent: {len(selected_packets)}")
    print(f"Total Bytes Sent: {total_sent_bytes}")
    print(f"Integer Packet Size Mean: {avg_pkt_size:.2f} bytes")
    print("*-" * 45 + "\n")

if __name__ == "__main__":
    main()
