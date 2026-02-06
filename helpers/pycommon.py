from scapy.all import (ByteField, ShortField, Packet, BitField, IntField)

DUMMY_ETHER_SRC = "00:00:0a:00:00:01"
DUMMY_ETHER_DST = "00:00:0a:00:00:02"
FEATURES_TYPE_ETHER = 0x2324
BNN_TYPE_ETHER = 0x2323

CONCURRENT_ACTIVE_FLOWS = 50

feaures_bit_width =  {
    'sbytes': 14, 
    'dbytes': 14,
    'spkts': 7, 
    'dpkts': 7, 
    'smeansz': 14, 
    'dmeansz': 14,
    'smaxbytes': 14, 
    'dmaxbytes': 14, 
    'sminbytes': 14, 
    'dminbytes': 14,
    'fin_cnt': 7, 
    'syn_cnt': 7, 
    'ack_cnt': 7, 
    'psh_cnt': 7, 
    'rst_cnt': 7, 
    'ece_cnt': 7
}

class BNNFeaturesHeader(Packet):
    name = "bnn_input_h"
    fields_desc = [
        ShortField("sbytes", 0),
        ShortField("dbytes", 0),
        ByteField("spkts",  0),
        ByteField("dpkts",  0),
        ShortField("smean",  0),
        ShortField("dmean",  0),
        ShortField("smaxbytes",  0),
        ShortField("dmaxbytes",  0),
        ShortField("sminbytes",  0),
        ShortField("dminbytes",  0),
        BitField("fin_cnt",  0, 4),
        BitField("syn_cnt",  0, 4),
        BitField("ack_cnt",  0, 4),
        BitField("psh_cnt",  0, 4),
        BitField("rst_cnt",  0, 4),
        BitField("ece_cnt",  0, 4)
    ]
    # ---- summary printed by p.summary() or your handler ----
    def summary(self):
        return (f"BNNInput\n"
                f"\tsbytes={self.sbytes} dbytes={self.dbytes} \n"
                f"\tsmean={self.smean} dmean={self.dmean} \n"
                f"\tspkts={self.spkts} dpkts={self.dpkts} \n"
                f"\tsmaxbytes={self.smaxbytes} dmaxbytes={self.dmaxbytes} \n"
                f"\tsminbytes={self.sminbytes} dminbytes={self.dminbytes} \n"
                f"\tfin_cnt={self.fin_cnt} syn_cnt={self.syn_cnt} \n"
                f"\tack_cnt={self.ack_cnt} psh_cnt={self.psh_cnt} \n"
                f"\trst_cnt={self.rst_cnt} ece_cnt={self.ece_cnt} \n")
    
    def bits_concat_128b(self) -> str:
        """Concatenate all fields as a 128-bit binary string (zero-padded)."""
        parts = [
            f"{self.sbytes & 0xFFFF:016b}",
            f"{self.dbytes & 0xFFFF:016b}",
            f"{self.smean & 0xFFFF:016b}",
            f"{self.dmean & 0xFFFF:016b}",
            f"{self.spkts & 0xFFFF:016b}",
            f"{self.dpkts & 0xFFFF:016b}",
            f"{self.smaxbytes & 0xFFFF:016b}",
            f"{self.dmaxbytes & 0xFFFF:016b}",
            f"{self.sminbytes & 0xFFFF:016b}",
            f"{self.dminbytes & 0xFFFF:016b}",
            f"{self.fin_cnt & 0x0F:04b}",
            f"{self.syn_cnt & 0x0F:04b}",
            f"{self.ack_cnt & 0x0F:04b}",
            f"{self.psh_cnt & 0x0F:04b}",
            f"{self.rst_cnt & 0x0F:04b}",
            f"{self.ece_cnt & 0x0F:04b}"
        ]
        return "".join(parts)
    
    def bits_concat_126b(self) -> str:
        """Concatenate all fields as a 126-bit binary string (zero-padded)."""
        parts = [
            f"{self.sbytes & 0x3FFF:014b}",
            f"{self.dbytes & 0x3FFF:014b}",
            f"{self.smean & 0x3FFF:014b}",
            f"{self.dmean & 0x3FFF:014b}",
            f"{self.spkts & 0x7F:07b}",
            f"{self.dpkts & 0x7F:07b}",
            f"{self.smaxbytes & 0x3FFF:014b}",
            f"{self.dmaxbytes & 0x3FFF:014b}",
            f"{self.sminbytes & 0x3FFF:014b}",
            f"{self.dminbytes & 0x3FFF:014b}",
            f"{self.fin_cnt & 0x7F:07b}",
            f"{self.syn_cnt & 0x7F:07b}",
            f"{self.ack_cnt & 0x7F:07b}",
            f"{self.psh_cnt & 0x7F:07b}",
            f"{self.rst_cnt & 0x7F:07b}",
            f"{self.ece_cnt & 0x7F:07b}"
        ]
        return "".join(parts)

    def to_hex(self) -> str:
        """Hex string of the concatenated bits (32 hex chars)."""
        bits = self.bits_concat_126b()
        # print(f"bits: {bits} (len={len(bits)})")
        return f"{int(bits, 2):0{len(bits)//4}x}"
    
class BNNWide(Packet):
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

class BNNDense(Packet):
    name = "BNN_pkt"
    fields_desc = [
        # first bit of this field is for padding
        ByteField("layer_no", 0),
        ByteField("l0_out_1", 0),
        ByteField("l0_out_2", 0),
        ByteField("l0_out_3", 0),
        ByteField("l0_out_4", 0),
        ByteField("l0_out_5", 0),
        ByteField("l0_out_6", 0),

        ByteField("l1_out", 0),

        ByteField("l0_popcount", 0),
        ByteField("is_pred_confident", 0),

        ShortField("input_offset", 0),
        ShortField("input_offset_cp", 0),

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

class BNNTiny(Packet):
    name = "BNN_pkt"
    fields_desc = [ 
        # first bit of this fields is for padding
        ByteField("layer_no", 0),
        ByteField("l0_out_1", 0), 
        ByteField("l0_out_2", 0), 
        ByteField("l0_out_3", 0), 
        ByteField("l0_out_4", 0),
        
        ByteField("l1_out", 0),

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

l1_w = [
    '1f143be20e90222ffb4839ffeb2968ada',
    '1cc368a838c354317def65f5b822cac7a',
    '1cc368a838c354317def65f5b822cac7a',
    '1916adccb1c624e1c547dacf143e0daba',
    '1decce04296b70e305cdc126b638446ea',
    '1f9978b3e3f60bf9cde423c87d62188aa',
    '1e426dfb4ab9c96d8ead66a73f120a93a',
    '17b9573dbdba0cde69a7c1a036aca167a',
    '1d947b72599d6c1e625b059a4898dcc6a',
    '1408af752b22791fb09bd4942f8b062da',
    '11c6ef8e2f20b80d4bbfcb827fa59586a',
    '1bddfd9ac265ccec30efaad7528eb500a',
    '15ae8bd1796d3922962ee4e295615b25a',
    '16d5544ac645d1de9a1b93f19f31435ca',
    '1fc233d0f6707afe5122ae67f482d694a',
    '18e3a38652cd424613f7f608054d7ab9a',
    '11b628fd17eb0175a5140adfcb231c5ca',
    '1cee4c4f87d38681bcdfd343ffc17f5ba',
    '10bef3208b4fc0e723219d7df2f2ef57a',
    '126c29635e0e492def16b6e6996d716da',
    '175cf5494a17508d54414927f42f77caa',
    '16be8a7ac86bf32cd445a40c6ad45587a',
    '1b6c5596550805836f5bf713a1bd480da',
    '16c2cb6891a6993debb2788688f95155a',
    '1c6c0e913e75902fea63ad42e393e608a',
    '1d49a835f2191522f4b0abf56ad0e177a',
    '12af825d005ecc2c6eccf922183ec661a',
    '133ea74db0055445b805752b07e16473a',
    '16a97ed3d11a5a5317fa20ee42996084a',
    '16bf1c7b083a84db52af1bb889748292a',
    '1eece4370e64e0a06ee1940bb2361df4a',
    '1988f4c2cc501c291d5a0785613e9c84a',
    '199b03a01486aa3010ae69fb10e4bab9a',
    '10bef3208b4fc0e723219d7df2f2ef57a',
    '175cf5494a17508d54414927f42f77caa',
    '16be8a7ac86bf32cd445a40c6ad45587a',
    '1b6c5596550805836f5bf713a1bd480da',
    '16c2cb6891a6993debb2788688f95155a',
    '1c6c0e913e75902fea63ad42e393e608a',
    '1d49a835f2191522f4b0abf56ad0e177a',
    '12af825d005ecc2c6eccf922183ec661a',
    '133ea74db0055445b805752b07e16473a'
]

l2_w = [
    '1f1431220e9',
    '1cc3b2a838c'
]

nn = [132, 42, 2]
