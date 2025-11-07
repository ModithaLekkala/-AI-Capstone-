#!/usr/bin/env python3

import argparse
from collections import defaultdict
from scapy.all import rdpcap, sendp, sniff, conf
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP, UDP

FEATURE_EXTRACTOR_PIPE_INTF_INPUT  = 'veth0'
CLIENT_RECEIVING_INTF = 'veth3'


FlowKey = tuple  # (src, dst, sport, dport, proto)

def five_tuple(pkt):
    if IP not in pkt:
        return None
    ip = pkt[IP]
    proto = ip.proto
    if proto == 6 and TCP in pkt:
        return (ip.src, ip.dst, pkt[TCP].sport, pkt[TCP].dport, 6)
    elif proto == 17 and UDP in pkt:
        return (ip.src, ip.dst, pkt[UDP].sport, pkt[UDP].dport, 17)
    return None

def reverse_key(k: FlowKey) -> FlowKey:
    src, dst, sport, dport, proto = k
    return (dst, src, dport, sport, proto)

def group_by_flow(packets):
    flows = defaultdict(list)
    for pkt in packets:
        k = five_tuple(pkt)
        if k:
            flows[k].append(pkt)
    return flows

def tcp_flags(pkt):
    f = pkt[TCP].flags
    return {
        'syn': bool(f & 0x02),
        'ack': bool(f & 0x10),
        'rst': bool(f & 0x04),
        'fin': bool(f & 0x01),
    }

def contains_handshake(forward_pkts, reverse_pkts):
    saw_syn = saw_synack = saw_ack = False
    order = []
    for i, p in enumerate(forward_pkts):
        order.append(('f', i, p.time, p))
    for i, p in enumerate(reverse_pkts):
        order.append(('r', i, p.time, p))
    order.sort(key=lambda x: x[2])

    for side, _, _, p in order:
        if TCP not in p:
            continue
        fl = tcp_flags(p)
        if side == 'f' and fl['syn'] and not fl['ack']:
            saw_syn = True
        elif side == 'r' and fl['syn'] and fl['ack'] and saw_syn:
            saw_synack = True
        elif side == 'f' and fl['ack'] and not fl['syn'] and saw_syn and saw_synack:
            saw_ack = True
            break
    return saw_syn and saw_synack and saw_ack

def last_ttl(pkts):
    ttl = None
    for p in pkts:
        if IP in p:
            ttl = p[IP].ttl
    return ttl if ttl is not None else 0

def main():
    parser = argparse.ArgumentParser(description="Send two specular flows from PCAP and compute metrics")
    parser.add_argument("--pcap", required=True)
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--iface", default=FEATURE_EXTRACTOR_PIPE_INTF_INPUT)
    parser.add_argument("--receiving-iface", default=CLIENT_RECEIVING_INTF)
    parser.add_argument("--src-mac", default="00:00:0a:00:00:01")
    parser.add_argument("--dst-mac", default="00:00:0a:00:00:02")
    parser.add_argument("--tot-flow-packets", type=int, default=16, help="Total number of packets across both directions.")
    parser.add_argument("--balanced", action="store_true", help="If set, split total packets evenly between forward and reverse.")
    parser.add_argument("--timeout", type=float, default=1.0)
    args = parser.parse_args()

    conf.use_pcap = True
    print(f'Use pcap backend: [{conf.use_pcap}]')

    all_pkts = rdpcap(args.pcap, count=args.count)
    flows = group_by_flow(all_pkts)

    fwd_key = rev_key = None
    for k in flows.keys():
        if k[4] != 6:
            continue
        rk = reverse_key(k)
        if rk in flows:
            fwd_key, rev_key = k, rk
            break
    if not fwd_key:
        print("No TCP flow pair found")
        return

    fwd_all = flows[fwd_key]
    rev_all = flows[rev_key]

    if args.balanced:
        half = args.tot_flow_packets // 2
        fwd_sel = fwd_all[:half]
        rev_sel = rev_all[:args.tot_flow_packets - half]
    else:
        # Follow chronological order across both directions until budget reached
        merged_all = []
        for p in fwd_all: merged_all.append((p.time, 'f', p))
        for p in rev_all: merged_all.append((p.time, 'r', p))
        merged_all.sort(key=lambda x: x[0])

        fwd_sel, rev_sel = [], []
        for _, side, pkt in merged_all:
            if len(fwd_sel) + len(rev_sel) >= args.tot_flow_packets:
                break
            if side == 'f':
                fwd_sel.append(pkt)
            else:
                rev_sel.append(pkt)

    hs_included = contains_handshake(fwd_sel, rev_sel)
    fwd_last_ttl = last_ttl(fwd_sel)
    rev_last_ttl = last_ttl(rev_sel)

    print(f"Forward: {fwd_key} | {len(fwd_sel)} packets | Last TTL={fwd_last_ttl}")
    print(f"Reverse: {rev_key} | {len(rev_sel)} packets | Last TTL={rev_last_ttl}")
    print(f"Handshake included: {hs_included}")

    merged = []
    for p in fwd_sel: merged.append((p.time, 'f', p))
    for p in rev_sel: merged.append((p.time, 'r', p))
    merged.sort(key=lambda x: x[0])

    if not merged:
        return

    conf.iface = args.iface
    total_bytes_fwd = total_bytes_rev = 0
    sent_count_fwd = sent_count_rev = 0

    print(f'Sending on {args.iface}.')
    print(f'Receiving on {args.receiving_iface}.')
    for idx, (t, side, pkt) in enumerate(merged, start=1):
        if Ether not in pkt and IP in pkt:
            pkt = Ether(src=args.src_mac, dst=args.dst_mac) / pkt[IP]
        else:
            pkt[Ether].src = args.src_mac
            pkt[Ether].dst = args.dst_mac

        pkt_len_on_wire = len(pkt) + 4  # account for FCS

        if side == 'f':
            total_bytes_fwd += pkt_len_on_wire
            sent_count_fwd += 1
        else:
            total_bytes_rev += pkt_len_on_wire
            sent_count_rev += 1

        print(f"[{idx:03d}] ({'FWD' if side=='f' else 'REV'}) "
              f"len={pkt_len_on_wire}  {pkt.summary()}...", end='')

        def sendp_callback():
            sendp(pkt, iface=args.iface, verbose=False)


        sniff(
            iface=args.receiving_iface,
            promisc=True,
            prn=lambda p: print(f'Replied.'),
            count=1,
            timeout=1,
            started_callback=sendp_callback
        )

    print("\n--- Stats ---")
    print(f"Forward packets: {sent_count_fwd} | Total bytes: {total_bytes_fwd} | Avg: {total_bytes_fwd/max(sent_count_fwd,1):.2f}")
    print(f"Reverse packets: {sent_count_rev} | Total bytes: {total_bytes_rev} | Avg: {total_bytes_rev/max(sent_count_rev,1):.2f}")
    print(f"Last TTL forward: {fwd_last_ttl} | Last TTL reverse: {rev_last_ttl}")

if __name__ == "__main__":
    main()
