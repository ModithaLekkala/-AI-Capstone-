BENIGN_SAMPLES = 50
MALICIOUS_SAMPLES = 50
WINDOW_GAP_SEC = 2.8
PACKET_DELAY_SEC = 0.01


def _host_ip(prefix, index):
    third_octet = index // 250
    fourth_octet = (index % 250) + 1
    return "{}.{}.{}".format(prefix, third_octet, fourth_octet)


def generate_samples():
    samples = []

    for index in range(BENIGN_SAMPLES):
        samples.append({
            "name": "Benign Sample {:02d}".format(index + 1),
            "src_ip": _host_ip("10.1", index),
            "dst_ip": _host_ip("192.168", index),
            "sport": 20000 + index,
            "dport": 80,
            "expected": "FORWARD",
            "initial_len": 500,
            "initial_psh": bool(index % 2),
            "pcap_name": "benign_batch.pcap",
        })

    for index in range(MALICIOUS_SAMPLES):
        samples.append({
            "name": "Malicious Sample {:02d}".format(index + 1),
            "src_ip": _host_ip("10.2", index),
            "dst_ip": _host_ip("172.16", index),
            "sport": 30000 + index,
            "dport": 443,
            "expected": "DROP",
            "initial_len": 60,
            "initial_psh": False,
            "pcap_name": "malicious_batch.pcap",
        })

    return samples


def total_input_packets():
    return len(generate_samples()) * 2