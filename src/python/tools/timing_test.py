"""timing_test.py - 3-flow test with per-packet timestamps to see which phase is captured"""
import threading
import time
from scapy.all import IP, TCP, Ether, Raw, sendp, sniff

captured = []
IFACE_IN = 'veth0'
IFACE_OUT = 'veth1'
t0 = [0]

def do_capture():
    pkts = sniff(iface=IFACE_OUT, timeout=8, filter='ip and tcp')
    for p in pkts:
        if IP in p:
            captured.append((float(p.time) - t0[0], p[IP].src))
    print('[cap] done, {} pkts'.format(len(captured)))

def do_inject():
    time.sleep(0.5)  # let sniff settle
    t0[0] = time.time()
    print('[inj] phase1 start at t=0.0')
    for i in range(3):
        pkt = Ether()/IP(src='10.1.1.{}'.format(i+1), dst='192.168.1.1')/TCP()/Raw(load='X'*446)
        sendp(pkt, iface=IFACE_IN, verbose=False)
        print('[inj] phase1 pkt {} at t={:.2f}'.format(i+1, time.time() - t0[0]))
        time.sleep(0.1)
    print('[inj] waiting 2.3s for window...')
    time.sleep(2.3)
    print('[inj] phase2 start at t={:.2f}'.format(time.time() - t0[0]))
    for i in range(3):
        pkt = Ether()/IP(src='10.1.1.{}'.format(i+1), dst='192.168.1.1')/TCP()/Raw(load='X'*446)
        sendp(pkt, iface=IFACE_IN, verbose=False)
        print('[inj] phase2 pkt {} at t={:.2f}'.format(i+1, time.time() - t0[0]))
        time.sleep(0.1)

cap = threading.Thread(target=do_capture, daemon=True)
cap.start()
inj = threading.Thread(target=do_inject)
inj.start()
inj.join()
cap.join()

print('--- Captured packets (relative time) ---')
for rel_ts, src in sorted(captured):
    print('  t={:.2f}s  src={}'.format(rel_ts, src))
print('--- Window boundary at ~2.8s (0.5s + 2.3s) ---')
