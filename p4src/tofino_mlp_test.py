from scapy.all import srp1
from scapy.all import Packet
from scapy.all import Ether, IntField, ByteField, ShortField
from scapy.all import bind_layers
from mlp import MLP
from pycommon import hex_input, hex_w, nn, hex_w2, hex_w3

class BNN_pkt(Packet):
    name = "BNN_pkt"
    fields_desc = [ 
        ByteField("layer_no", 0x00),
        IntField ("l0_out", 0x000000),
        ByteField("l1_out", 0x00),
        ByteField("l2_out", 0x00),

        ByteField("pop_recirc", 0x00),
        ByteField("nrs_recirc", 0x00),

        ByteField("pop1", 0x00),
        ByteField("pop2", 0x00),
        ByteField("pop3", 0x00),
        ByteField("pop4", 0x00),
    ]


bind_layers(Ether, BNN_pkt, type=0x2323)

def hex_lists_to_ints(*hex_lists):
    return [[int(h, 16) for h in lst] for lst in hex_lists]

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

        # expected = exec_l1_bmlp(hex_input, hex_w)
        mlp = MLP(nn[0], [nn[1], nn[2]], nn[-1])
        w_mlp = hex_lists_to_ints(hex_w, hex_w2, hex_w3)

        expected = mlp.do_inference(int(hex_input, 16), w_mlp, True)
        print(f'expected: {expected}')

        obtained = resp[BNN_pkt].l2_out
        print(f'obtained: l0: {resp[BNN_pkt].l0_out} l1: {resp[BNN_pkt].l1_out} l2: {obtained}')

        match = expected == obtained
        color = '\033[92m' if match else '\033[91m'

        print(f'{color}Result is {"NOT" if not match else ""} matching!\033[0m')
    else:
        print("✗ no reply")

if __name__ == '__main__':
    main()



    