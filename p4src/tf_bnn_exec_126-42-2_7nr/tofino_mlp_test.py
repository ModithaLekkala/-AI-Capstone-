from scapy.all import Ether, IntField, ByteField, ShortField, sniff, sendp, bind_layers, Packet, raw, XBitField
from mlp import MLP
from pycommon import hex_input, hex_w, nn, hex_w2
import time

BNN_TO_CPU_INTF = 'veth7'
CPU_TO_BNN_INTF = 'veth8'

class BNN(Packet):
    name = "BNN_pkt"
    fields_desc = [ 
        ByteField("layer_no", 0),
        XBitField ("l0_out", 0, 42),
        XBitField("padding", 0, 6),
        ByteField("l1_out", 0),
        # ByteField("l2_out", 0x00),

        ShortField("input_offset", 0),

        ByteField("pop_recirc", 0),
        ByteField("nrs_recirc", 0),

        ByteField("pop1", 0),
        ByteField("pop2", 0),
        ByteField("pop3", 0),
        ByteField("pop4", 0),
        ByteField("pop5", 0),
        ByteField("pop6", 0),
        ByteField("pop7", 0),
        
    ]

bind_layers(Ether, BNN, type=0x2323)

def hex_lists_to_ints(*hex_lists):
    return [[int(h, 16) for h in lst] for lst in hex_lists]

def main():
    src = '00:00:0a:00:00:01'
    dst = '00:00:0a:00:00:02'
    print(f'Sending pkt from {src} to {dst} through {CPU_TO_BNN_INTF}')

    pkt = Ether(src=src, dst=dst, type=0x2323)/BNN()

    # shared variable to store start timestamp
    timings = {"start": None}

    def sendp_callback():
        timings["start"] = time.perf_counter_ns()
        sendp(pkt, CPU_TO_BNN_INTF, verbose=False)

    def recv_bnn_res(resp):
        end_time = time.perf_counter_ns()
        elapsed = end_time - timings["start"] if timings["start"] else None

        resp = Ether(raw(resp))
        print("← got response:")
        resp.show()

        mlp = MLP(nn[0], [nn[1]], nn[-1])
        w_mlp = hex_lists_to_ints(hex_w, hex_w2)

        expected = mlp.do_inference(int(hex_input, 16), w_mlp, True)
        print(f'expected: {expected}')

        obtained = resp[BNN].l1_out
        print(f'obtained: l0: {resp[BNN].l0_out} l1: {obtained}')

        match = expected == obtained
        color = '\033[92m' if match else '\033[91m'
        print(f'{color}Result is {"NOT " if not match else ""}matching!\033[0m')

        if elapsed is not None:
            print(f'Elapsed time between trigger and response packet: {elapsed} ns')

    sniff(
        iface=BNN_TO_CPU_INTF,
        promisc=True,
        prn=recv_bnn_res,
        count=1,                  # stop after first response
        started_callback=sendp_callback
    )

if __name__ == '__main__':
    main()
