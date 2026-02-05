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
        'fin': bool(f & 0x01),
        'syn': bool(f & 0x02),
        'rst': bool(f & 0x04),
        'psh': bool(f & 0x08),
        'ack': bool(f & 0x10),
        'ece': bool(f & 0x40),
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
    parser.add_argument("--src-mac", default="da:ba:0e:cd:03:19")
    parser.add_argument("--dst-mac", default="7c:76:35:28:71:2f")
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

    # Feature tracking for BNN_FEAT packet
    sbytes = 0          # Total bytes forward (src -> dst)
    dbytes = 0          # Total bytes reverse (dst -> src)
    spkts = 0           # Packet count forward
    dpkts = 0           # Packet count reverse
    smaxbytes = 0       # Max packet size forward
    dmaxbytes = 0       # Max packet size reverse
    sminbytes = None    # Min packet size forward
    dminbytes = None    # Min packet size reverse

    # TCP flag counters (across both directions)
    fin_cnt = 0
    syn_cnt = 0
    ack_cnt = 0
    psh_cnt = 0
    rst_cnt = 0
    ece_cnt = 0

    print(f'Sending on {args.iface}.')
    print(f'Receiving on {args.receiving_iface}.')
    for idx, (t, side, pkt) in enumerate(merged, start=1):
        if Ether not in pkt and IP in pkt:
            pkt = Ether(src=args.src_mac, dst=args.dst_mac) / pkt[IP]
        else:
            pkt[Ether].src = args.src_mac
            pkt[Ether].dst = args.dst_mac

        # Frame length = IP total_len + 14 (Ethernet header) + 4 (FCS)
        pkt_len_on_wire = len(pkt) + 4  # account for FCS

        # Count TCP flags
        if TCP in pkt:
            fl = tcp_flags(pkt)
            if fl['fin']: fin_cnt += 1
            if fl['syn']: syn_cnt += 1
            if fl['ack']: ack_cnt += 1
            if fl['psh']: psh_cnt += 1
            if fl['rst']: rst_cnt += 1
            if fl['ece']: ece_cnt += 1

        if side == 'f':
            sbytes += pkt_len_on_wire
            spkts += 1
            smaxbytes = max(smaxbytes, pkt_len_on_wire)
            sminbytes = pkt_len_on_wire if sminbytes is None else min(sminbytes, pkt_len_on_wire)
        else:
            dbytes += pkt_len_on_wire
            dpkts += 1
            dmaxbytes = max(dmaxbytes, pkt_len_on_wire)
            dminbytes = pkt_len_on_wire if dminbytes is None else min(dminbytes, pkt_len_on_wire)

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

    # Handle case where no packets in one direction
    sminbytes = sminbytes if sminbytes is not None else 0
    dminbytes = dminbytes if dminbytes is not None else 0

    # Compute mean sizes
    smeansz = sbytes // spkts if spkts > 0 else 0
    dmeansz = dbytes // dpkts if dpkts > 0 else 0

    print("\n" + "="*60)
    print("EXPECTED BNN_FEAT PACKET VALUES (ethertype 0x2324)")
    print("="*60)
    print(f"{'Feature':<15} {'Value':>10}   {'Description'}")
    print("-"*60)
    print(f"{'sbytes':<15} {sbytes:>10}   Total bytes (src -> dst)")
    print(f"{'dbytes':<15} {dbytes:>10}   Total bytes (dst -> src)")
    print(f"{'spkts':<15} {spkts:>10}   Packet count (src -> dst)")
    print(f"{'dpkts':<15} {dpkts:>10}   Packet count (dst -> src)")
    print(f"{'smeansz':<15} {smeansz:>10}   Mean size (src -> dst)")
    print(f"{'dmeansz':<15} {dmeansz:>10}   Mean size (dst -> src)")
    print(f"{'smaxbytes':<15} {smaxbytes:>10}   Max packet size (src -> dst)")
    print(f"{'dmaxbytes':<15} {dmaxbytes:>10}   Max packet size (dst -> src)")
    print(f"{'sminbytes':<15} {sminbytes:>10}   Min packet size (src -> dst)")
    print(f"{'dminbytes':<15} {dminbytes:>10}   Min packet size (dst -> src)")
    print(f"{'fin_cnt':<15} {fin_cnt:>10}   FIN flag count")
    print(f"{'syn_cnt':<15} {syn_cnt:>10}   SYN flag count")
    print(f"{'ack_cnt':<15} {ack_cnt:>10}   ACK flag count")
    print(f"{'psh_cnt':<15} {psh_cnt:>10}   PSH flag count")
    print(f"{'rst_cnt':<15} {rst_cnt:>10}   RST flag count")
    print(f"{'ece_cnt':<15} {ece_cnt:>10}   ECE flag count")
    print("="*60)
    print(f"Note: smeansz/dmeansz are computed by CP (not in dataplane)")
    print(f"Note: Values may differ slightly due to P4 register timing")

if __name__ == "__main__":
    main()
