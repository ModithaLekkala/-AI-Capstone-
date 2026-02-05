from scapy.all import Ether, sniff, Packet, BitField, raw, ShortField, ByteField

CPU_INTF = 'sw-cpu'

class BNNInput(Packet):
    name = "bnn_input_h"
    fields_desc = [
        ShortField("sbytes", 0),
        ShortField("dbytes", 0),
        ByteField("spkts", 0),
        ByteField("dpkts", 0),
        ShortField("smeansz", 0),
        ShortField("dmeansz", 0),
        ShortField("smaxbytes", 0),
        ShortField("dmaxbytes", 0),
        ShortField("sminbytes", 0),
        ShortField("dminbytes", 0),
        ByteField("fin_cnt", 0),
        ByteField("syn_cnt", 0),
        ByteField("ack_cnt", 0),
        ByteField("psh_cnt", 0),
        ByteField("rst_cnt", 0),
        ByteField("ece_cnt", 0),
    ]

    def summary(self):
        return (f"BNNInput "
                f"sbytes={self.sbytes} dbytes={self.dbytes} "
                f"spkts={self.spkts} dpkts={self.dpkts} "
                f"smeansz={self.smeansz} dmeansz={self.dmeansz} "
                f"smaxbytes={self.smaxbytes} dmaxbytes={self.dmaxbytes} "
                f"sminbytes={self.sminbytes} dminbytes={self.dminbytes} "
                f"fin={self.fin_cnt} syn={self.syn_cnt} ack={self.ack_cnt} "
                f"psh={self.psh_cnt} rst={self.rst_cnt} ece={self.ece_cnt}")

def recv_msg_cpu(pkt):
    packet = Ether(raw(pkt))
    if packet.type == 0x2324:
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
