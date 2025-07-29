import argparse
from scapy.all import rdpcap, sendp, srp1, conf, sniff
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP

def main():
    parser = argparse.ArgumentParser(description="Send packets from PCAP to Tofino and wait for replies")
    parser.add_argument("pcap", help="Path to the input PCAP file")
    parser.add_argument("count", type=int, help="Number of packets to send from the PCAP")
    parser.add_argument("--iface", default="h1-eth0", help="Interface to send on (default: h1-eth0)")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout to wait for each response (default: 1.0s)")
    parser.add_argument("--src-mac", default="00:00:0a:00:00:01", help="Source MAC address to set")
    parser.add_argument("--dst-mac", default="00:00:0a:00:00:02", help="Destination MAC address to set")
    args = parser.parse_args()

    print(f"Loading packets from {args.pcap}...")
    packets = rdpcap(args.pcap, count=args.count)

    if len(packets) == 0:
        print("No packets found in the PCAP.")
        return

    conf.iface = args.iface
    print(f"Sending {args.count} packets on {args.iface}...")

    for i, pkt in enumerate(packets[:args.count]):
        print(f"\n[Packet {i+1}] Preparing and sending packet...")
        if not pkt.haslayer(Ether):
            pkt = Ether(src=args.src_mac, dst=args.dst_mac) / pkt[IP]

        print(pkt.summary())
        try:
            # sendp(pkt, iface=args.iface, verbose=True)
            print(f"[Packet {i+1}] Sent. Waiting for response...")
            response = sniff(pkt, iface=args.iface, timeout=1)
            if response:
                print(f"[Packet {i+1}] Received:")
                response[0].show()
            else:
                print(f"[Packet {i+1}] No response (timeout)")
        except Exception as e:
            print(f"[Packet {i+1}] Error: {e}")

if __name__ == "__main__":
    main()
