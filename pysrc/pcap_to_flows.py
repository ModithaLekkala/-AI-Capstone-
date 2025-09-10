#!/usr/bin/env python3
"""
pcap_to_flows.py

Read a folder of pcaps named 1.pcap, 2.pcap, ...; extract the first N packets
per flow (bidirectional 5-tuple) and write one merged CSV with features +
(optional) ground-truth labels.

Notes:
- File sequence starts at --start-index (default: 1) and stops at the first gap.
- Ground truth is loaded once and applied to all pcaps.
"""

import argparse
import csv
import logging
import os
from collections import Counter
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Dict, Tuple, Optional, List, Any

from scapy.all import (
    PcapReader,
    IP, IPv6,
    TCP, UDP,
    ICMP,
    ICMPv6EchoRequest, ICMPv6EchoReply,
    Raw,
)
from scapy.packet import Packet

# ---------- Logging ----------
logger = logging.getLogger("pcap_to_flows")

def setup_logging(verbose: bool, log_file: Optional[str] = None):
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=level,
        handlers=handlers,
    )

# ---------- Types / dataclasses ----------
FlowKey = Tuple[str, int, str, int, str]  # (src_ip, sport, dst_ip, dport, proto)

@dataclass
class FlowStats:
    key: FlowKey
    initiator: Tuple[str, int]
    responder: Tuple[str, int]
    proto: str

    first_ts: Optional[float] = None
    last_ts: Optional[float] = None
    timestamps: List[float] = field(default_factory=list)

    sbytes: int = 0
    dbytes: int = 0
    spkts: int = 0
    dpkts: int = 0
    smaxbytes: int = 0
    dmaxbytes: int = 0
    sminbytes: Optional[int] = None
    dminbytes: Optional[int] = None
    sttl: Optional[int] = None
    dttl: Optional[int] = None

    tcp_flags_counter: Counter = field(default_factory=Counter)
    syn_time: Optional[float] = None
    synack_time: Optional[float] = None
    ack_after_synack_time: Optional[float] = None

    seen_pkts: int = 0

    gt: Optional[Dict[str, Any]] = None
    is_attack: bool = False

    def add_timestamp(self, ts: float):
        self.timestamps.append(ts)
        if self.first_ts is None:
            self.first_ts = ts
        self.last_ts = ts

# ---------- Packet helpers ----------
def get_l3(pkt: Packet):
    if IP in pkt: return pkt[IP]
    if IPv6 in pkt: return pkt[IPv6]
    return None

def get_proto(pkt: Packet) -> Optional[str]:
    if TCP in pkt: return "TCP"
    if UDP in pkt: return "UDP"
    if ICMP in pkt or ICMPv6EchoRequest in pkt or ICMPv6EchoReply in pkt: return "ICMP"
    return None

def get_addrs_ports(pkt: Packet) -> Tuple[Optional[str], int, Optional[str], int]:
    l3 = get_l3(pkt)
    if l3 is None:
        return None, 0, None, 0
    src_ip, dst_ip = l3.src, l3.dst
    if   TCP in pkt: sport, dport = int(pkt[TCP].sport), int(pkt[TCP].dport)
    elif UDP in pkt: sport, dport = int(pkt[UDP].sport), int(pkt[UDP].dport)
    else:            sport, dport = 0, 0
    return src_ip, sport, dst_ip, dport

def get_ttl(pkt: Packet) -> Optional[int]:
    if IP in pkt: return int(pkt[IP].ttl)
    if IPv6 in pkt: return int(pkt[IPv6].hlim)
    return None

def l4_payload_len(pkt: Packet) -> int:
    try:
        if TCP in pkt:
            if IP in pkt:
                ip = pkt[IP]; ip_payload_len = int(ip.len) - (ip.ihl * 4)
            elif IPv6 in pkt:
                ip = pkt[IPv6]; ip_payload_len = int(ip.plen)
            else:
                return 0
            tcp = pkt[TCP]
            tcp_hdr_len = tcp.dataofs * 4 if tcp.dataofs else 20
            return max(0, ip_payload_len - tcp_hdr_len)
        if UDP in pkt:
            udp = pkt[UDP]
            udp_len = int(udp.len) if hasattr(udp, "len") and udp.len else 0
            return max(0, udp_len - 8)
        if ICMP in pkt:
            if Raw in pkt: return len(pkt[Raw].load)
            try: return max(0, len(bytes(pkt[ICMP])) - 8)
            except Exception: return 0
        if ICMPv6EchoRequest in pkt or ICMPv6EchoReply in pkt:
            if Raw in pkt: return len(pkt[Raw].load)
            try:
                if IPv6 in pkt:
                    return max(0, int(pkt[IPv6].plen) - 8)
            except Exception:
                return 0
        return 0
    except Exception:
        return 0

def canonical_key(src_ip: str, sport: int, dst_ip: str, dport: int, proto: str) -> FlowKey:
    return (src_ip, sport, dst_ip, dport, proto)

def _count_tcp_flags(fs: FlowStats, flags: int):
    if flags & 0x01: fs.tcp_flags_counter["FIN"] += 1
    if flags & 0x02: fs.tcp_flags_counter["SYN"] += 1
    if flags & 0x04: fs.tcp_flags_counter["RST"] += 1
    if flags & 0x08: fs.tcp_flags_counter["PSH"] += 1
    if flags & 0x10: fs.tcp_flags_counter["ACK"] += 1
    if flags & 0x40: fs.tcp_flags_counter["ECE"] += 1

# ---------- Ground-truth ----------
def load_ground_truth(csv_path: str) -> Dict[FlowKey, Dict[str, Any]]:
    gt_map: Dict[FlowKey, Dict[str, Any]] = {}
    required_headers = {
        "Attack category", "Protocol", "Source IP", "Source Port", "Destination IP", "Destination Port"
    }
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        missing = [h for h in required_headers if h not in reader.fieldnames]
        if missing:
            raise ValueError(f"Ground-truth CSV missing headers: {missing}")
        for row in reader:
            try:
                key = (
                    row["Source IP"].strip(),
                    int(row["Source Port"]) if row["Source Port"] else 0,
                    row["Destination IP"].strip(),
                    int(row["Destination Port"]) if row["Destination Port"] else 0,
                    row["Protocol"].strip().upper(),
                )
                gt_map[key] = {"attack_cat": row["Attack category"]}
            except Exception:
                continue
    logger.info(f"Loaded {len(gt_map)} GT entries from {csv_path}")
    return gt_map

# ---------- Flow table ----------
class FlowTable:
    def __init__(self, max_pkts_per_flow: int, gt_map: Dict[FlowKey, Dict[str, Any]]):
        self.max_pkts = max_pkts_per_flow
        self._map: Dict[FlowKey, FlowStats] = {}
        self._rev_index: Dict[FlowKey, FlowStats] = {}
        self.gt_map = gt_map

    def get_or_create(self, pkt: Packet, ts: float) -> Optional[FlowStats]:
        proto = get_proto(pkt)
        if not proto: return None
        src_ip, sport, dst_ip, dport = get_addrs_ports(pkt)
        if src_ip is None or dst_ip is None: return None

        proto_up = proto.upper()
        fwd = canonical_key(src_ip, sport, dst_ip, dport, proto_up)
        rev = canonical_key(dst_ip, dport, src_ip, sport, proto_up)

        fs = (self._map.get(fwd)
              or self._rev_index.get(fwd)
              or self._map.get(rev)
              or self._rev_index.get(rev))
        if fs: return fs

        gt = self.gt_map.get(fwd)
        fs = FlowStats(
            key=fwd,
            initiator=(src_ip, sport),
            responder=(dst_ip, dport),
            proto=proto_up,
            gt=gt,
            is_attack=(gt is not None),
        )
        self._map[fwd] = fs
        self._rev_index[rev] = fs
        return fs

    def flows(self) -> List[FlowStats]:
        return list({id(v): v for v in self._map.values()}.values())

# ---------- Core processing ----------
def process_pcap(infile: str, n_first: int, max_pkts: Optional[int], flows: FlowTable):
    packet_count = 0
    logger.info(f"Reading pcap: {infile}")
    with PcapReader(infile) as pr:
        for pkt in pr:
            packet_count += 1
            if max_pkts is not None and packet_count > max_pkts:
                logger.info(f"Reached max packet limit ({max_pkts}) in {infile}, stopping early")
                break
            try:
                proto = get_proto(pkt)
                if not proto: continue
                l3 = get_l3(pkt)
                if l3 is None: continue
                ts = float(pkt.time)

                fs = flows.get_or_create(pkt, ts)
                if fs is None: continue

                src_ip, sport, dst_ip, dport = get_addrs_ports(pkt)
                if (src_ip, sport) == fs.initiator:
                    direction = "src"
                elif (src_ip, sport) == fs.responder:
                    direction = "dst"
                else:
                    continue

                if fs.seen_pkts >= flows.max_pkts:
                    logger.debug(f'Flow {fs.key} completed.')
                    continue

                fs.add_timestamp(ts)
                fs.seen_pkts += 1

                ttl = get_ttl(pkt)
                if ttl is not None:
                    if direction == "src": fs.sttl = ttl
                    else: fs.dttl = ttl

                size = l4_payload_len(pkt)
                if direction == "src":
                    fs.sbytes += size; fs.spkts += 1
                    fs.smaxbytes = max(fs.smaxbytes, size)
                    fs.sminbytes = size if fs.sminbytes is None else min(fs.sminbytes, size)
                else:
                    fs.dbytes += size; fs.dpkts += 1
                    fs.dmaxbytes = max(fs.dmaxbytes, size)
                    fs.dminbytes = size if fs.dminbytes is None else min(fs.dminbytes, size)

                if fs.proto == "TCP" and TCP in pkt:
                    flags = pkt[TCP].flags
                    _count_tcp_flags(fs, flags)
                    if direction == "src" and (flags & 0x02) and fs.syn_time is None:
                        fs.syn_time = ts
                    if direction == "dst" and ((flags & 0x12) == 0x12) and fs.synack_time is None:
                        fs.synack_time = ts
                    if direction == "src" and (flags & 0x10) and not (flags & 0x02):
                        if fs.synack_time is not None and fs.ack_after_synack_time is None and ts >= fs.synack_time:
                            fs.ack_after_synack_time = ts
            except Exception as e:
                logger.debug(f"Packet error in {infile}: {e}")
                continue

def flows_to_rows(flows: FlowTable) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for fs in flows.flows():
        iats = []
        if len(fs.timestamps) >= 2:
            ts_sorted = sorted(fs.timestamps)
            iats = [ts_sorted[i] - ts_sorted[i-1] for i in range(1, len(ts_sorted))]
        iat_mean = mean(iats) if iats else 0.0
        # iat_std = pstdev(iats) if len(iats) >= 2 else 0.0
        iat_min = min(iats) if iats else 0.0
        iat_max = max(iats) if iats else 0.0

        synack = (fs.synack_time - fs.syn_time) if (fs.syn_time is not None and fs.synack_time is not None) else 0.0
        ackdat = (fs.ack_after_synack_time - fs.synack_time) if (fs.synack_time is not None and fs.ack_after_synack_time is not None) else 0.0

        minbytes_candidates = [x for x in [fs.sminbytes, fs.dminbytes] if x is not None]
        minbytes = min(minbytes_candidates) if minbytes_candidates else 0
        maxbytes = max(fs.smaxbytes, fs.dmaxbytes)

        smeansz = (fs.sbytes / fs.spkts) if fs.spkts > 0 else 0.0
        dmeansz = (fs.dbytes / fs.dpkts) if fs.dpkts > 0 else 0.0

        gt = fs.gt or {}
        rows.append({
            "proto": fs.proto,
            "sbytes": fs.sbytes, "dbytes": fs.dbytes,
            "sttl": fs.sttl or 0, "dttl": fs.dttl or 0,
            "spkts": fs.spkts, "dpkts": fs.dpkts,
            "smeansz": round(smeansz, 6), "dmeansz": round(dmeansz, 6),
            "synack": round(synack, 9), "ackdat": round(ackdat, 9),
            "smaxbytes": fs.smaxbytes, "dmaxbytes": fs.dmaxbytes,
            "sminbytes": fs.sminbytes or 0, "dminbytes": fs.dminbytes or 0,
            "minbytes": minbytes, "maxbytes": maxbytes,
            "fin_cnt": fs.tcp_flags_counter.get("FIN", 0),
            "syn_cnt": fs.tcp_flags_counter.get("SYN", 0),
            "ack_cnt": fs.tcp_flags_counter.get("ACK", 0),
            "psh_cnt": fs.tcp_flags_counter.get("PSH", 0),
            "rst_cnt": fs.tcp_flags_counter.get("RST", 0),
            "ece_cnt": fs.tcp_flags_counter.get("ECE", 0),
            "iat_mean": round(iat_mean, 9),
            # "iat_std": round(iat_std, 9),
            "iat_min": round(iat_min, 9),
            "iat_max": round(iat_max, 9),
            # "stime": fs.first_ts or 0.0, "ltime": fs.last_ts or 0.0,
            "attack_cat": gt.get("attack_cat", ""),
            "label": 1 if fs.is_attack else 0
        })
    return rows

# ---------- CSV ----------
def write_csv(rows: List[Dict[str, Any]], outfile: str):
    logger.info(f"Writing {len(rows)} flow records to {outfile}")
    header = [
        "proto",
        "sbytes", "dbytes", "sttl", "dttl", "spkts", "dpkts", "smeansz", "dmeansz",
        "synack", "ackdat",
        "smaxbytes", "dmaxbytes", "sminbytes", "dminbytes", "minbytes", "maxbytes",
        "fin_cnt", "syn_cnt", "ack_cnt", "psh_cnt", "rst_cnt", "ece_cnt",
        "iat_mean", "iat_min", "iat_max", 
        # "iat_std", 
        # "stime", "ltime",
        "attack_cat", "label",
    ]
    with open(outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(
        description="Create a flow-level dataset from a folder of pcaps named 1.pcap, 2.pcap, ...")
    parser.add_argument("-I", "--input-dir", required=True,
                        help="Folder containing sequential pcaps: 1.pcap, 2.pcap, ...")
    parser.add_argument("-o", "--output", required=True, help="Output CSV file")
    parser.add_argument("-n", "--nfirst", type=int, default=16,
                        help="Number of first packets per flow to consider (default: 16)")
    parser.add_argument("-m", "--max-pkts", type=int, default=None,
                        help="Maximum packets to analyze PER PCAP (default: no limit)")
    parser.add_argument("--start-index", type=int, default=1,
                        help="First index to look for (default: 1 → 1.pcap)")
    parser.add_argument("--flows-ground-truth", required=True,
                        help="Ground-truth CSV to join by directional 5-tuple")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--log-file", default=None, help="Optional log file path")
    args = parser.parse_args()

    setup_logging(args.verbose, args.log_file)
    logger.info("Starting processing")
    logger.info(f"Params: nfirst={args.nfirst}, max_pkts/pcap={args.max_pkts}, "
                f"gt='{args.flows_ground_truth}', input_dir='{args.input_dir}'")

    # Load GT once
    gt_map = load_ground_truth(args.flows_ground_truth)

    # Shared flow table across all pcaps (merges flows)
    flows = FlowTable(args.nfirst, gt_map)

    # Walk 1.pcap, 2.pcap, ... stopping at first gap
    idx = args.start_index
    processed_files = 0
    while True:
        pcap_path = os.path.join(args.input_dir, f"{idx}.pcap")
        if not os.path.isfile(pcap_path):
            if processed_files == 0:
                logger.error(f"No pcap found at {pcap_path}")
                raise SystemExit(1)
            logger.info(f"No file {pcap_path}; stopping at index {idx-1}")
            break

        process_pcap(pcap_path, args.nfirst, args.max_pkts, flows)
        processed_files += 1
        idx += 1

    rows = flows_to_rows(flows)
    write_csv(rows, args.output)
    logger.info("All done!")

if __name__ == "__main__":
    main()
