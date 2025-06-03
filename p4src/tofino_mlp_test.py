from scapy.all import sendp, send, srp1, sniff
from scapy.all import Packet, hexdump, binrepr
from scapy.all import Ether, IP, IntField, ShortField, ByteField
from scapy.all import bind_layers

# class BNN_pkt(Packet):
#     name = "BNN_pkt"
#     fields_desc = [ IntField("x", 0x15a91b27)]

class BNN_pkt(Packet):
    name = "BNN_pkt"
    fields_desc = [ ByteField("x", 0x55)]

bind_layers(Ether, BNN_pkt, type=0x2323)

def main():
    iface = 'h1-eth1'
    src = '00:00:0a:00:00:01'
    dst = '00:00:0a:00:00:02'
    print(f'Sending pkt from {src} to {dst} through {iface}')

    # no nn input since it's inside tofino registers
    pkt = Ether(src=src, dst=dst,type=0x2323)/BNN_pkt()
    resp = srp1(pkt, iface=iface, timeout=2, verbose=True)
    if resp:
        print("← got response:")
        resp.show()
    else:
        print("✗ no reply")

if __name__ == '__main__':
    main()