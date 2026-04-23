"""phase2_test.py: Single probe that tests Phase 2 forwarding after a clean-slate setup.
Uses UNIQUE source IPs not used in any prior tests to avoid stale register pollution."""
import threading
import time
from scapy.all import IP, TCP, Ether, Raw, sendp, sniff

IFACE_IN  = 'veth0'
IFACE_OUT = 'veth1'
captured = []

def do_capture():
    pkts = sniff(iface=IFACE_OUT, timeout=10, filter='ip and tcp')
    for p in pkts:
        if IP in p:
            captured.append((p.time, p[IP].src, len(p)))
    print('[cap] done, {} pkts'.format(len(captured)))

# Use FRESH IPs 10.99.x.x to avoid stale register state
FRESH_SRC = ['10.99.1.1', '10.99.1.2']

def do_inject(t0):
    time.sleep(0.5)
    print('[inj] t={:.2f} Phase 1 (2 fresh benign flows)'.format(time.time()-t0))
    for src in FRESH_SRC:
        pkt = Ether()/IP(src=src, dst='192.168.99.1')/TCP(dport=80)/Raw(load='X'*446)
        sendp(pkt, iface=IFACE_IN, verbose=False)
        print('[inj] t={:.2f} sent {}'.format(time.time()-t0, src))
        time.sleep(0.1)

    print('[inj] t={:.2f} waiting 2.5s for window expiry...'.format(time.time()-t0))
    time.sleep(2.5)

    print('[inj] t={:.2f} Phase 2 (trigger packets)'.format(time.time()-t0))
    for src in FRESH_SRC:
        pkt = Ether()/IP(src=src, dst='192.168.99.1')/TCP(dport=80)/Raw(load='X'*446)
        sendp(pkt, iface=IFACE_IN, verbose=False)
        print('[inj] t={:.2f} sent {}'.format(time.time()-t0, src))
        time.sleep(0.1)

    print('[inj] t={:.2f} done'.format(time.time()-t0))

t0 = time.time()
print('=== Phase2 Forwarding Test (fresh IPs only) ===')

cap_thread = threading.Thread(target=do_capture, daemon=True)
cap_thread.start()
inj_thread = threading.Thread(target=do_inject, args=(t0,))
inj_thread.start()
inj_thread.join()
cap_thread.join()

print('')
print('--- Captured ---')
for ts, src, pktlen in sorted(captured):
    print('  t={:.2f}  src={:15s}  len={}'.format(ts - t0, src, pktlen))

phase1_end = 0.5 + 2 * 0.1  # approx
phase2_start = 0.5 + 0.2 + 2.5  # approx

p1_count = sum(1 for ts,src,l in captured if (ts-t0) < phase2_start)
p2_count = sum(1 for ts,src,l in captured if (ts-t0) >= phase2_start)
print('')
print('Packets in Phase-1 window (<{:.1f}s): {}'.format(phase2_start, p1_count))
print('Packets in Phase-2 window (>={:.1f}s): {}'.format(phase2_start, p2_count))

if p2_count > 0:
    print('RESULT: Phase-2 benign are FORWARDED (switch working correctly)')
else:
    print('RESULT: Phase-2 benign are DROPPED (P4 classification issue!)')
