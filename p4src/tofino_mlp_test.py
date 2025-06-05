from scapy.all import srp1
from scapy.all import Packet
from scapy.all import Ether, ShortField
from scapy.all import bind_layers
import numpy as np
from mlp import MLP

def exec_l1_bmlp(hex_input, hex_w):
    W1 = np.empty((16, 128), dtype=np.float32)
    for i, h in enumerate(hex_w):
        b = bin(int(h, 16))[2:].zfill(128)
        W1[i] = np.array([1.0 if c=='1' else -1.0 for c in b])

    # Example input (32 hex digits = 128 bits)
    b = bin(int(hex_input, 16))[2:].zfill(128)
    x = np.array([1.0 if c=='1' else -1.0 for c in b], dtype=np.float32)

    # Compute hidden layer outputs (8 neurons)
    h = np.empty(16, dtype=np.float32)
    for i in range(16):
        s = int(np.dot(x, W1[i]))
        h[i] = 1.0 if s >= 0 else -1.0

    h[h==-1] = 0
    h = h.astype('int').tolist()
    h ="".join(map(str, h))

    print("Expected outputs:", int(h, 2))

    return int(h, 2)


class BNN_pkt(Packet):
    name = "BNN_pkt"
    fields_desc = [ ShortField("x", 0x0000)]

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

        hex_w = [
            "e97be2dd1d113e46777483d626c89129",
            "1a568f08b5d7c9b867c20d1fcd1618e5",
            "db83d17c296c36c85d023cac8c1d26e5",
            "b9b8c1110dec94703ab4cb70b07e9a0a",
            "b158c7809c71049238ce5e6e88c89416",
            "b2742753d81449f9fb8295c1a6ecf097",
            "cc5e7ca7e16b789aa061da83820cdc80",
            "28daae2b4b87a45656a12a06111b4c7d",
            "236539e62c271bb8ca5fb0a8c7100291",
            "446e63b9bf3c1ec1a6d3e43a6efc5299",
            "a402b23ae2b0eb5a747eb77fdd335ce6",
            "02908710c934b52a2f4dcb95db3cbb4d",
            "b39dae3d78e2737e0bf5788e8b030ac1",
            "82d6e357dafcfc7fdd0a0283041757e3",
            "488b3e8229356e21b8393ceb8b44311c",
            "819ac144d0135a443e5164e7eca03bc6"
        ]
        
        hex_input = "e51411243381365b9ea36fbeedd94689"

        expected = exec_l1_bmlp(hex_input, hex_w)
        obtained = resp[BNN_pkt].x

        match = expected == obtained
        color = '\033[92m' if match else '\033[91m'

        print(f'{color}Result is {"NOT" if not match else ""} matching!\033[0m')
    else:
        print("✗ no reply")

if __name__ == '__main__':
    main()



    