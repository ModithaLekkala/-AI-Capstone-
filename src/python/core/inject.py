from scapy.all import Ether, IP, TCP, Raw, sendp, wrpcap
import time

from batch_profiles import (
    PACKET_DELAY_SEC,
    WINDOW_GAP_SEC,
    generate_samples,
    total_input_packets,
)

IFACE = "veth0"

def build_packet(src_ip, dst_ip, sport, dport, length, psh):
    payload_size = max(0, length - 54)
    flags = "PA" if psh else "A"
    return (Ether() /
            IP(src=src_ip, dst=dst_ip) /
            TCP(sport=sport, dport=dport, flags=flags) /
            Raw(load="X" * payload_size))


def send_initial_packets(samples):
    benign_packets = []
    malicious_packets = []

    print("\n[Phase 1] Sending initial packets for {} samples".format(len(samples)))
    for index, sample in enumerate(samples, start=1):
        packet = build_packet(
            sample["src_ip"],
            sample["dst_ip"],
            sample["sport"],
            sample["dport"],
            sample["initial_len"],
            sample["initial_psh"],
        )
        print("  - Initial packet {}/{} | {} | Len: {} | PSH: {}".format(
            index,
            len(samples),
            sample["name"],
            sample["initial_len"],
            sample["initial_psh"],
        ))
        sendp(packet, iface=IFACE, verbose=False)
        if sample["expected"] == "FORWARD":
            benign_packets.append(packet)
        else:
            malicious_packets.append(packet)
        time.sleep(PACKET_DELAY_SEC)

    wrpcap("benign_batch.pcap", benign_packets)
    wrpcap("malicious_batch.pcap", malicious_packets)
    print("  - Saved to benign_batch.pcap and malicious_batch.pcap")


def send_trigger_packets(samples):
    print("\n[Phase 2] Sending trigger packets after {:.1f}s window gap".format(WINDOW_GAP_SEC))
    time.sleep(WINDOW_GAP_SEC)

    for index, sample in enumerate(samples, start=1):
        trigger_packet = (Ether() /
                          IP(src=sample["src_ip"], dst=sample["dst_ip"]) /
                          TCP(sport=sample["sport"], dport=sample["dport"], flags="A"))
        print("  - Trigger packet {}/{} | {}".format(index, len(samples), sample["name"]))
        sendp(trigger_packet, iface=IFACE, verbose=False)
        time.sleep(PACKET_DELAY_SEC)


if __name__ == "__main__":
    samples = generate_samples()

    print("=== P4 IDS Packet Injector ===")
    print("Sending on interface: {}".format(IFACE))
    print("Samples: {} | Total injected packets: {}".format(
        len(samples), total_input_packets()))

    send_initial_packets(samples)
    send_trigger_packets(samples)

    print("\n=== Done. Check tcpdump on veth1 for forwarded trigger packets. ===")