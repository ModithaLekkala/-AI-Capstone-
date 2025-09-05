from scapy.all import Ether, sniff, Packet, BitField, raw, ShortField, ByteField, bind_layers, IntField, sendp

FEATURE_EXTRACTOR_CPU_INTF = 'veth5'
BNN_TO_CPU_INTF = 'veth7'
CPU_TO_BNN_INTF = 'veth8'

class BNNFeaturesHeader(Packet):
    name = "bnn_input_h"
    fields_desc = [
        ByteField("sttl",   0),
        ByteField("dttl",   0),
        ShortField("sbytes", 0),
        ShortField("dbytes", 0),
        ShortField("smean",  0),
        ShortField("dmean",  0),
        ShortField("spkts",  0),
        ShortField("dpkts",  0),
        ByteField("synack",  0),
        ByteField("ackdat",  0),
    ]
    # ---- summary printed by p.summary() or your handler ----
    def summary(self):
        return (f"BNNInput sttl={self.sttl} dttl={self.dttl}"
                f"sbytes={self.sbytes} dbytes={self.dbytes} "
                f"smean={self.smean} dmean={self.dmean} "
                f"spkts={self.spkts} dpkts={self.dpkts} "
                f"synack={self.synack} ackdat={self.ackdat}")
    
    def bits_concat(self) -> str:
        """Concatenate all fields as a 128-bit binary string (zero-padded)."""
        parts = [
            f"{self.sttl & 0xFF:08b}",
            f"{self.dttl & 0xFF:08b}",
            f"{self.sbytes & 0xFFFF:016b}",
            f"{self.dbytes & 0xFFFF:016b}",
            f"{self.smean & 0xFFFF:016b}",
            f"{self.dmean & 0xFFFF:016b}",
            f"{self.spkts & 0xFFFF:016b}",
            f"{self.dpkts & 0xFFFF:016b}",
            f"{self.synack & 0xFF:08b}",
            f"{self.ackdat & 0xFF:08b}",
        ]
        return "".join(parts)

    def to_hex(self) -> str:
        """Hex string of the concatenated bits (32 hex chars)."""
        bits = self.bits_concat()
        return f"{int(bits, 2):0{len(bits)//4}x}"
    
class BNN(Packet):
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

bind_layers(Ether, BNN, type=0x2323)
bind_layers(Ether, BNNFeaturesHeader, type=0x2324)


def recv_msg_cpu(pkt):
    packet = Ether(raw(pkt))
    if packet.type == 0x2324:
        print('Feature extractor packet received.')
        cpu_header = BNNFeaturesHeader(bytes(packet.load))
        print(cpu_header.summary())
        print('Extracting features.')
        bnn_input = cpu_header.to_hex()

        assert len(bnn_input) == 32, "hex_input must be exactly 32 hex digits"

        # Make sixteen 4-digit substrings:
        input_chunks = [ bnn_input[i : i + 4] for i in range(0, 32, 4) ]

        for idx, piece in enumerate(input_chunks):
            print(f"bnn_input_reg.add({idx}, 0x{piece})")
            bnn_input_reg.add(idx, f"0x{piece}")

        print("→ Done loading the 128-bit feature into register slots 0..7.")

        pkt = Ether(src='00:00:0a:00:00:01',dst='00:00:0a:00:00:01',type=0x2323)/BNN()
        print('Send trigger packet to BNN pipeline.')

        def send_bnn():
            sendp(pkt, CPU_TO_BNN_INTF, verbose=False)

        def recv_bnn_res(resp):
            if resp:
                print("← got BNN response:")
                resp.show()
                print(resp[BNN])

                obtained = resp[BNN].l2_out
                print(f'obtained: l0: {resp[BNN].l0_out} l1: {resp[BNN].l1_out} l2: {obtained}')
            else:
                print("✗ no reply")

        sniff(
            iface=BNN_TO_CPU_INTF, 
            promisc=True, 
            count=1, 
            started_callback=send_bnn, 
            prn=recv_bnn_res
        )


def run_cpu_port_loop():
    cpu_port_intf = FEATURE_EXTRACTOR_CPU_INTF
    sniff(iface=cpu_port_intf, prn=recv_msg_cpu, promisc=True, count=1)

p4_bnn_executor = bfrt.multipipe_inetml.bnn_executor
bnn_input_reg = p4_bnn_executor.BnnIngress.bnn_input_reg

print('\nE2E MIRROR CONFIGURATION')
bfrt.mirror.cfg.entry_with_normal(sid=1, direction='EGRESS', session_enable=True, ucast_egress_port=64, ucast_egress_port_valid=1).push()
print('→ mirror session set.\n')

print('\nWAITING FOR CPU PACKET')
run_cpu_port_loop()

