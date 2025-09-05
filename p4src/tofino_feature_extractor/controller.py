from scapy.all import Ether, sniff, Packet, BitField, raw, ShortField, ByteField

CPU_INTF = 'sw-cpu'

class BNNInput(Packet):
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

def recv_msg_cpu(pkt):
    packet = Ether(raw(pkt))
    if packet.type == 0x2323:
        cpu_header = BNNInput(bytes(packet.load))
        print(cpu_header.summary())

def run_cpu_port_loop():
    cpu_port_intf = CPU_INTF
    sniff(iface=cpu_port_intf, prn=recv_msg_cpu, promisc=True, count=1)

print('\nE2E MIRROR CONFIGURATION')
bfrt.mirror.cfg.entry_with_normal(sid=1, direction='EGRESS', session_enable=True, ucast_egress_port=64, ucast_egress_port_valid=1).push()
print('→ mirror session set.\n')

print('\nSET OUTPUT PORT')

print('→ output ports set.\n')



print('\nWAITING FOR CPU PACKET')
# run_cpu_port_loop()

