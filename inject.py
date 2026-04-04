from scapy.all import Ether, IP, TCP, Raw, sendp, wrpcap
import time
import random

IFACE = "veth0"

def send_packet_sequence(packet_sequence, src_ip, dst_ip, sport, dport, pcap_name):
    pkts = []
    for i, p in enumerate(packet_sequence):
        length = p["len"]
        psh = p.get("psh", False)
        payload_size = max(0, length - 54)
        flags = "PA" if psh else "A"
        pkt = (Ether() /
               IP(src=src_ip, dst=dst_ip) /
               TCP(sport=sport, dport=dport, flags=flags) /
               Raw(load="X" * payload_size))
        print("  - Sending packet {}/{} | Len: {} | PSH: {}".format(
            i + 1, len(packet_sequence), length, psh))
        sendp(pkt, iface=IFACE, verbose=False)
        pkts.append(pkt)
        time.sleep(0.1)
    wrpcap(pcap_name, pkts)
    print("  - Saved to {}".format(pcap_name))


def test_benign():
    print("\n[Test Benign] Random packets (expect: FORWARD)")
    num_packets = 5  # Fixed for consistency
    packet_sequence = []
    for _ in range(num_packets):
        length = random.randint(100, 2000)  # Higher lengths to avoid matching drop rules
        psh = random.choice([True, False])
        packet_sequence.append({"len": length, "psh": psh})
    send_packet_sequence(packet_sequence, "10.0.1.1", "192.168.1.1",
                         1234, 80, "benign_a.pcap")

def test_malicious():
    print("\n[Test Malicious] Packets designed to match drop rules (expect: DROP)")
    # Exact match for first rule: 1 packet, length 54, no PSH
    num_packets = 1
    packet_sequence = [{"len": 54, "psh": False}]
    send_packet_sequence(packet_sequence, "10.0.1.1", "192.168.1.1",
                         1234, 80, "malicious_a.pcap")


def test_rule_b():
    print("\n[Test Rule B] Mixed Profile - 3 packets, 2 with PSH (expect: DROP)")
    packet_sequence = [
        {"len": 100, "psh": True},
        {"len": 150, "psh": False},
        {"len": 200, "psh": True},
    ]
    send_packet_sequence(packet_sequence, "10.0.9.1", "192.168.9.9",
                         9999, 443, "rule_b.pcap")
    time.sleep(2.1)
    pkt = (Ether() / IP(src="10.0.9.1", dst="192.168.9.9") /
           TCP(sport=9999, dport=443, flags="A"))
    sendp(pkt, iface=IFACE, verbose=False)


def test_tree_rule_1():
    print("\n[Test Tree Rule 1] 11 x 1400-byte packets, no PSH (expect: DROP)")
    packet_sequence = [{"len": 1400, "psh": False}] * 11
    send_packet_sequence(packet_sequence, "10.0.2.1", "192.168.2.2",
                         5678, 22, "tree_rule_1.pcap")
    time.sleep(2.1)
    pkt = (Ether() / IP(src="10.0.2.1", dst="192.168.2.2") /
           TCP(sport=5678, dport=22, flags="A"))
    sendp(pkt, iface=IFACE, verbose=False)


def test_normal():
    print("\n[Test Normal] Benign traffic - mixed sizes (expect: FORWARD)")
    packet_sequence = [
        {"len": 130, "psh": False},
        {"len": 200, "psh": False},
        {"len": 300, "psh": False},
        {"len": 150, "psh": False},
        {"len": 250, "psh": False},
    ]
    send_packet_sequence(packet_sequence, "10.0.10.1", "192.168.10.10",
                         8888, 8080, "normal.pcap")
    time.sleep(2.1)
    pkt = (Ether() / IP(src="10.0.10.1", dst="192.168.10.10") /
           TCP(sport=8888, dport=8080, flags="A"))
    sendp(pkt, iface=IFACE, verbose=False)


if __name__ == "__main__":
    print("=== P4 IDS Packet Injector ===")
    print("Sending on interface: {}".format(IFACE))
    print("")

    test_benign()
    test_malicious()
    test_benign()
    test_malicious()

    print("\n=== Done. Check tcpdump on veth1 for forwarded packets. ===")