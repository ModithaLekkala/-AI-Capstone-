from scapy.all import Ether, IP, TCP, sendp

pkt = (Ether() /
       IP(src="10.1.0.1", dst="192.168.0.1") /
       TCP(sport=20000, dport=80, flags="A"))

sendp(pkt, iface="veth0", verbose=False)
print("[probe] Sent 1 benign packet on veth0")
