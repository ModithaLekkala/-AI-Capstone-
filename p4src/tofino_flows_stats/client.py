#!/usr/bin/env python3

import argparse
from collections import defaultdict
from scapy.all import rdpcap, sendp, sniff, conf
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP, UDP

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

def pick_packets_with_handshake(fwd_all, rev_all, per_flow_limit):
    if not fwd_all or TCP not in fwd_all[0]:
        return fwd_all[:per_flow_limit], rev_all[:per_flow_limit], False

    have_hs = contains_handshake(fwd_all, rev_all)
    if not have_hs:
        return fwd_all[:per_flow_limit], rev_all[:per_flow_limit], False

    merged = []
    for i, p in enumerate(fwd_all):
        merged.append(('f', i, p.time))
    for i, p in enumerate(rev_all):
        merged.append(('r', i, p.time))
    merged.sort(key=lambda x: x[2])

    f_syn_idx = r_synack_idx = f_ack_idx = None
    for side, idx, _ in merged:
        p = (fwd_all if side == 'f' else rev_all)[idx]
        if TCP not in p:
            continue
        fl = tcp_flags(p)
        if f_syn_idx is None and side == 'f' and fl['syn'] and not fl['ack']:
            f_syn_idx = ('f', idx)
        elif f_syn_idx and r_synack_idx is None and side == 'r' and fl['syn'] and fl['ack']:
            r_synack_idx = ('r', idx)
        elif f_syn_idx and r_synack_idx and f_ack_idx is None and side == 'f' and fl['ack'] and not fl['syn']:
            f_ack_idx = ('f', idx)
            break

    if f_syn_idx and r_synack_idx and f_ack_idx:
        idxs = []
        for target in (f_syn_idx, r_synack_idx, f_ack_idx):
            for j, (side, i, _) in enumerate(merged):
                if side == target[0] and i == target[1]:
                    idxs.append(j)
                    break
        lo = max(0, min(idxs) - (per_flow_limit // 4))
        hi = min(len(merged), max(idxs) + (per_flow_limit // 4) + 1)

        f_selected, r_selected = [], []
        for side, i, _ in merged[lo:hi]:
            if side == 'f' and len(f_selected) < per_flow_limit:
                f_selected.append(fwd_all[i])
            elif side == 'r' and len(r_selected) < per_flow_limit:
                r_selected.append(rev_all[i])

        if len(f_selected) < per_flow_limit:
            for p in fwd_all:
                if p not in f_selected:
                    f_selected.append(p)
                    if len(f_selected) == per_flow_limit: break
        if len(r_selected) < per_flow_limit:
            for p in rev_all:
                if p not in r_selected:
                    r_selected.append(p)
                    if len(r_selected) == per_flow_limit: break

        return f_selected, r_selected, True

    return fwd_all[:per_flow_limit], rev_all[:per_flow_limit], have_hs

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
    parser.add_argument("--iface", default="h1-eth1")
    parser.add_argument("--src-mac", default="00:00:0a:00:00:01")
    parser.add_argument("--dst-mac", default="00:00:0a:00:00:02")
    parser.add_argument("--packets-per-flow", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=1.0)
    args = parser.parse_args()

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
    fwd_sel, rev_sel, hs_included = pick_packets_with_handshake(
        fwd_all, rev_all, args.packets_per_flow
    )

    fwd_last_ttl = last_ttl(fwd_sel)
    rev_last_ttl = last_ttl(rev_sel)

    print(f"Forward: {fwd_key} | {len(fwd_sel)} packets | Last TTL={fwd_last_ttl}")
    print(f"Reverse: {rev_key} | {len(rev_sel)} packets | Last TTL={rev_last_ttl}")
    print(f"Handshake included: {hs_included}")

    merged = []
    for p in fwd_sel:
        merged.append((p.time, 'f', p))
    for p in rev_sel:
        merged.append((p.time, 'r', p))
    merged.sort(key=lambda x: x[0])

    if not merged:
        return

    conf.iface = args.iface
    total_bytes_fwd = 0
    total_bytes_rev = 0
    sent_count_fwd = 0
    sent_count_rev = 0

    for idx, (t, side, pkt) in enumerate(merged, start=1):
        if Ether not in pkt and IP in pkt:
            pkt = Ether(src=args.src_mac, dst=args.dst_mac) / pkt[IP]
        else:
            pkt[Ether].src = args.src_mac
            pkt[Ether].dst = args.dst_mac

        pkt_len_on_wire = len(pkt) + 4  # FCS size

        if side == 'f':
            total_bytes_fwd += pkt_len_on_wire
            sent_count_fwd += 1
        else:
            total_bytes_rev += pkt_len_on_wire
            sent_count_rev += 1

        print(f"[{idx:03d}] ({'FWD' if side=='f' else 'REV'}) "
              f"len={pkt_len_on_wire}  {pkt.summary()}")

        sendp(pkt, iface=args.iface, verbose=False)
        sniff(iface=args.iface, timeout=args.timeout, count=1)

    print("\n--- Stats ---")
    print(f"Forward packets: {sent_count_fwd} | Total bytes: {total_bytes_fwd} | Avg: {total_bytes_fwd/max(sent_count_fwd,1):.2f}")
    print(f"Reverse packets: {sent_count_rev} | Total bytes: {total_bytes_rev} | Avg: {total_bytes_rev/max(sent_count_rev,1):.2f}")
    print(f"Last TTL forward: {fwd_last_ttl} | Last TTL reverse: {rev_last_ttl}")

if __name__ == "__main__":
    main()
