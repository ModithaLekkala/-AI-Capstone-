// echo.p4
/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
#include "common/headers.p4"
#include "common/util.p4"
#define WRITE_POP_PROC(y)\
    action pop_act##y(popcount_t popvalue) { hdr.recirc.pop##y## = hdr.recirc.pop##y## + popvalue;} \
    table pop##y{ \
        actions = { pop_act##y; } \ 
        key = { meta.nr##y##: exact; } \
        size = 65535; \
        const default_action = pop_act##y(0xF); \
    }

parser IngressParser(
    packet_in pkt,
    out headers_t hdr,
    out metadata_t ig_md,
    out ingress_intrinsic_metadata_t ig_intr_md)
{

    TofinoIngressParser() tofino_parser;

    state start {
        tofino_parser.apply(pkt, ig_intr_md);
        transition parse_eth;
    }

    state parse_eth {
        pkt.extract(hdr.ethernet);
        transition select(hdr.ethernet.ether_type) {
            BNN_PKT_ETYPE:  parse_bnn;
        }
    }

    state parse_bnn {
        pkt.extract(hdr.bnn_pkt);
        transition select(ig_intr_md.ingress_port) {
            LAYER_RECIRC_PORT:  parse_l1;
            POP_RECIRC_PORT: parse_recirc;
            default: accept;
        }
    }

    state parse_recirc {
        pkt.extract(hdr.recirc);
        transition accept;
    }

    state parse_l1 {
        pkt.extract(hdr.bnn_l1);
        transition accept;
    }

}

control Ingress(
    inout headers_t                                   hdr,
    inout metadata_t                              meta,
    in    ingress_intrinsic_metadata_t                 ig_intr_md,
    in    ingress_intrinsic_metadata_from_parser_t     ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t   ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t         ig_tm_md 
){
    bit<9> egress_port;

    Register<bit<16>, bit<16>>(8, 0x5555) bnn_input_reg;
    RegisterAction<bit<16>,bit<8>, bit<16>>(bnn_input_reg) get_bnn_input_reg = {
        void apply(inout bit<16> bnn_input, out bit<16> out_var) {
            out_var = bnn_input;
        }
    };


	action get_nn_input(){
        meta.nr1 = get_bnn_input_reg.execute(hdr.recirc.pop_recirc);
	}

    action get_l1_weights(bit<16> nr1_w, bit<16> nr2_w, bit<16> nr3_w, bit<16> nr4_w,
                          bit<16> nr5_w, bit<16> nr6_w, bit<16> nr7_w, bit<16> nr8_w) {
        meta.nr1_w = nr1_w;
        meta.nr2_w = nr2_w;
        meta.nr3_w = nr3_w;
        meta.nr4_w = nr4_w;
        meta.nr5_w = nr5_w;
        meta.nr6_w = nr6_w;
        meta.nr7_w = nr7_w;
        meta.nr8_w = nr8_w;
    }
    
    table l1_weights{
        actions = { get_l1_weights; }
        key = { 
            hdr.recirc.pop_recirc: exact;
            hdr.recirc.nrs_recirc: exact;
        }
        size = 16;
    }

    WRITE_POP_PROC(1)
    WRITE_POP_PROC(2)
    WRITE_POP_PROC(3)
    WRITE_POP_PROC(4)
    WRITE_POP_PROC(5)
    WRITE_POP_PROC(6)
    WRITE_POP_PROC(7)
    WRITE_POP_PROC(8)

    apply { 
        if(ig_intr_md.ingress_port != POP_RECIRC_PORT && 
            ig_intr_md.ingress_port != LAYER_RECIRC_PORT) {
            hdr.recirc.original_port = (bit<16>)ig_intr_md.ingress_port;
        }

        if(ig_intr_md.ingress_port != LAYER_RECIRC_PORT) {
            get_nn_input();
            l1_weights.apply();
            meta.nr1 = meta.nr1 ^ meta.nr1_w;
            meta.nr2 = meta.nr1 ^ meta.nr2_w;
            meta.nr3 = meta.nr1 ^ meta.nr3_w;
            meta.nr4 = meta.nr1 ^ meta.nr4_w;
            meta.nr5 = meta.nr1 ^ meta.nr5_w;
            meta.nr6 = meta.nr1 ^ meta.nr6_w;
            meta.nr7 = meta.nr1 ^ meta.nr7_w;
            meta.nr8 = meta.nr1 ^ meta.nr8_w;
        }

        pop1.apply();
        pop2.apply();
        pop3.apply();
        pop4.apply();
        pop5.apply();
        pop6.apply();
        pop7.apply();
        pop8.apply();
        
        if(hdr.recirc.pop_recirc < 7) {
            hdr.recirc.setValid();
            hdr.recirc.pop_recirc = hdr.recirc.pop_recirc + 1;
            ig_tm_md.ucast_egress_port = POP_RECIRC_PORT;

        } else if(hdr.recirc.pop_recirc == 7) {
            
            if(hdr.recirc.pop1 >= 8) hdr.bnn_pkt.x[0:0] = 0; else hdr.bnn_pkt.x[0:0] = 1;
            if(hdr.recirc.pop2 >= 8) hdr.bnn_pkt.x[1:1] = 0; else hdr.bnn_pkt.x[1:1] = 1;
            if(hdr.recirc.pop3 >= 8) hdr.bnn_pkt.x[2:2] = 0; else hdr.bnn_pkt.x[2:2] = 1;
            if(hdr.recirc.pop4 >= 8) hdr.bnn_pkt.x[3:3] = 0; else hdr.bnn_pkt.x[3:3] = 1;
            if(hdr.recirc.pop5 >= 8) hdr.bnn_pkt.x[4:4] = 0; else hdr.bnn_pkt.x[4:4] = 1;
            if(hdr.recirc.pop6 >= 8) hdr.bnn_pkt.x[5:5] = 0; else hdr.bnn_pkt.x[5:5] = 1;
            if(hdr.recirc.pop7 >= 8) hdr.bnn_pkt.x[6:6] = 0; else hdr.bnn_pkt.x[6:6] = 1;
            if(hdr.recirc.pop8 >= 8) hdr.bnn_pkt.x[7:7] = 0; else hdr.bnn_pkt.x[7:7] = 1;
            
            hdr.recirc.setInvalid();

            bit<48> tmp = hdr.ethernet.dst_addr;
            hdr.ethernet.dst_addr = hdr.ethernet.src_addr;
            hdr.ethernet.src_addr = tmp;
            ig_tm_md.ucast_egress_port = (bit<9>)hdr.recirc.original_port;
        }
        ig_tm_md.bypass_egress = 1w1;
    }
}

control IngressDeparser(
    packet_out      pkt,
    inout headers_t hdr,
    in   metadata_t meta,
    in   ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md)
{
    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.bnn_pkt);     
        pkt.emit(hdr.recirc);
               
  
        // pkt.emit(hdr.bnn_l1);    
    }
}



Pipeline(
    IngressParser(),
    Ingress(),
    IngressDeparser(),
    EmptyEgressParser(),
    EmptyEgress(),
    EmptyEgressDeparser()
) pipe;
Switch(pipe) main;
