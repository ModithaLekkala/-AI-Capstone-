/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
// #include "../common/headers.p4"
#include "common/headers.p4"
#include "common/util.p4"

#define WIDTH_IX_L0 7 /* (l0 weights width. / 16) -1  */
#define WIDTH_IX_L1 1
#define WIDTH_IX_L2 0
#define HEIGTH_IX_L0 7 /* (l0 neurons no. / 16) -1  */
#define HEIGTH_IX_L1 1
#define HEIGTH_IX_L2 0
#define INPUT_LEN 128
#define L0_WEIGHT_TB_SIZE 64
#define L1_WEIGHT_TB_SIZE 16
#define L2_WEIGHT_TB_SIZE 1
#define LAST_LAYER_NO 2 /* number of layers -1 */

#define POP_ACCUMULATE(y)\
    action pop_act##y(popcount_t popvalue) { hdr.bnn_pkt.pop##y## = hdr.bnn_pkt.pop##y## + popvalue;}\
    table pop##y{\
        actions = { pop_act##y; }\
        key = { nr##y##: exact; }\
        size = 65535;\
        const default_action = pop_act##y(0xF);\
    }

#define WRITE_SIGN(frst, snd, thrd, frth,  layer, th)\
    if(hdr.bnn_pkt.pop4 >= th) hdr.bnn_pkt.##layer##[##frst##:##frst##] = 0; else hdr.bnn_pkt.##layer##[##frst##:##frst##] = 1;\
    if(hdr.bnn_pkt.pop3 >= th) hdr.bnn_pkt.##layer##[##snd##:##snd##] = 0; else hdr.bnn_pkt.##layer##[##snd##:##snd##] = 1;\
    if(hdr.bnn_pkt.pop2 >= th) hdr.bnn_pkt.##layer##[##thrd##:##thrd##] = 0; else hdr.bnn_pkt.##layer##[##thrd##:##thrd##] = 1;\
    if(hdr.bnn_pkt.pop1 >= th) hdr.bnn_pkt.##layer##[##frth##:##frth##] = 0; else hdr.bnn_pkt.##layer##[##frth##:##frth##] = 1;

#define WRITE_SIGN_BIN(frst, snd, layer, th)\
    if(hdr.bnn_pkt.pop2 >= th) hdr.bnn_pkt.##layer##[##frst##:##frst##] = 0; else hdr.bnn_pkt.##layer##[##frst##:##frst##] = 1;\
    if(hdr.bnn_pkt.pop1 >= th) hdr.bnn_pkt.##layer##[##snd##:##snd##] = 0; else hdr.bnn_pkt.##layer##[##snd##:##snd##] = 1;

#define APPLY_POP()\
    pop1.apply();\
    pop2.apply();\
    pop3.apply();\
    pop4.apply();

#define FREE_POP()\
    hdr.bnn_pkt.pop1 = 0;\
    hdr.bnn_pkt.pop2 = 0;\
    hdr.bnn_pkt.pop3 = 0;\
    hdr.bnn_pkt.pop4 = 0;

#define COPY()\
    nr2 = nr1;\
    nr3 = nr1;\
    nr4 = nr1;

parser BnnIngressParser(
    packet_in pkt,
    out bnn_headers_t hdr,
    out empty_metadata_t ig_md,
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
        transition accept;
    }
}

control BnnIngress(
    inout bnn_headers_t                                   hdr,
    inout empty_metadata_t                              meta,
    in    ingress_intrinsic_metadata_t                 ig_intr_md,
    in    ingress_intrinsic_metadata_from_parser_t     ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t   ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t         ig_tm_md 
){
    bit<16> nr1=0;
    bit<16> nr2=0;
    bit<16> nr3=0;
    bit<16> nr4=0;
    
    Register<bit<16>, bit<16>>(8, 0x5555) bnn_input_reg;
    RegisterAction<bit<16>,bit<8>, bit<16>>(bnn_input_reg) get_bnn_input_reg = {
        void apply(inout bit<16> bnn_input, out bit<16> out_var) {
            out_var = bnn_input;
        }
    };


    action get_weights(bit<16> nr1_w, bit<16> nr2_w, bit<16> nr3_w, bit<16> nr4_w) {
        nr1 = nr1_w ^ nr1;
        nr2 = nr2_w ^ nr2;
        nr3 = nr3_w ^ nr3;
        nr4 = nr4_w ^ nr4;
    }
    
    table l0_weights{
        actions = { get_weights; }
        key = { 
            hdr.bnn_pkt.pop_recirc: exact;
            hdr.bnn_pkt.nrs_recirc: exact;
        }
        size = L0_WEIGHT_TB_SIZE;
    }

    table l1_weights{
        actions = { get_weights; }
        key = { 
            hdr.bnn_pkt.pop_recirc: exact;
            hdr.bnn_pkt.nrs_recirc: exact;
        }
        size = L1_WEIGHT_TB_SIZE;
    }

    table l2_weights{
        actions = { get_weights; }
        key = { 
            hdr.bnn_pkt.pop_recirc: exact;
            hdr.bnn_pkt.nrs_recirc: exact;
        }
        size = L2_WEIGHT_TB_SIZE;
    }

    action pop_recirc() {
        ig_tm_md.ucast_egress_port = POP_RECIRC_PORT;
        hdr.bnn_pkt.pop_recirc = hdr.bnn_pkt.pop_recirc + 1;
    }

    action nrs_recirc() {
        FREE_POP()
                
        hdr.bnn_pkt.pop_recirc = 0;
        hdr.bnn_pkt.nrs_recirc = hdr.bnn_pkt.nrs_recirc + 1;
        ig_tm_md.ucast_egress_port = POP_RECIRC_PORT;
    }

    action to_next_layer() {
        FREE_POP()
        /* current layer completed executed 
            send result for next layer processing */
        hdr.bnn_pkt.layer_no = hdr.bnn_pkt.layer_no + 1;
        hdr.bnn_pkt.pop_recirc = 0;
        hdr.bnn_pkt.nrs_recirc = 0;
        ig_tm_md.ucast_egress_port = LAYER_RECIRC_PORT;
    }

    action send_back() {
        /*inference terminated*/

        bit<48> tmp = hdr.ethernet.dst_addr;
        hdr.ethernet.dst_addr = hdr.ethernet.src_addr;
        hdr.ethernet.src_addr = tmp;
        ig_tm_md.ucast_egress_port = (bit<9>)CPU_PORT;
    }

    table egress_behaviour {
        actions = {
            pop_recirc; nrs_recirc; to_next_layer; send_back;
        }
        key = {
            hdr.bnn_pkt.layer_no: exact;
            hdr.bnn_pkt.pop_recirc: exact;
            hdr.bnn_pkt.nrs_recirc: ternary;
        }
        const entries = {
            ( 0, WIDTH_IX_L0, HEIGTH_IX_L0 &&& 0xFF ) : to_next_layer();
            ( 1, WIDTH_IX_L1, HEIGTH_IX_L1 &&& 0xFF ) : to_next_layer();
            ( 2, WIDTH_IX_L2, HEIGTH_IX_L2 &&& 0xFF ) : send_back();
            ( 0, WIDTH_IX_L0, 0 &&& 0x00 )            : nrs_recirc();
            ( 1, WIDTH_IX_L1, 0 &&& 0x00 )            : nrs_recirc();
            ( 2, WIDTH_IX_L2, 0 &&& 0x00 )            : nrs_recirc();
        }
        const default_action = pop_recirc();
        size=(LAST_LAYER_NO+1)+(LAST_LAYER_NO+1);
    }

    POP_ACCUMULATE(1)
    POP_ACCUMULATE(2)
    POP_ACCUMULATE(3)
    POP_ACCUMULATE(4)

    apply { 

        /* -------------- SET ACTIVATIONS AND WEIGHTS FOR EACH LAYER -------------- */
        if(hdr.bnn_pkt.layer_no == 0) {
            /* get register input */
            nr1 = get_bnn_input_reg.execute(hdr.bnn_pkt.pop_recirc);
            COPY()
            l0_weights.apply();
            
        } else if(hdr.bnn_pkt.layer_no == 1){
            /* get l0 output */
            if(hdr.bnn_pkt.pop_recirc == 0) {
                nr1 = hdr.bnn_pkt.l0_out[31:16];
            } else if (hdr.bnn_pkt.pop_recirc == 1) {
                nr1 = hdr.bnn_pkt.l0_out[15:0];
            }
            COPY()
            l1_weights.apply();
        } else if(hdr.bnn_pkt.layer_no == 2){
            nr1 = (bit<16>)hdr.bnn_pkt.l1_out;
            nr2 = nr1; //COPY()
            l2_weights.apply();
        }

        APPLY_POP()

        /* ---- PARTIAL AND FINAL INFERENCE RESULT LOGIC FOR EACH LAYER ---- */
        if(hdr.bnn_pkt.layer_no == 0 && hdr.bnn_pkt.pop_recirc == WIDTH_IX_L0) {
            if (hdr.bnn_pkt.nrs_recirc == 0) {
                WRITE_SIGN(28,29,30,31, l0_out, 0x40);
            } else if (hdr.bnn_pkt.nrs_recirc == 1) {
                WRITE_SIGN(24,25,26,27, l0_out, 0x40);
            } else if (hdr.bnn_pkt.nrs_recirc == 2) {
                WRITE_SIGN(20,21,22,23, l0_out, 0x40);
            } else if (hdr.bnn_pkt.nrs_recirc == 3) {
                WRITE_SIGN(16,17,18,19, l0_out, 0x40);
            } else if (hdr.bnn_pkt.nrs_recirc == 4) {
                WRITE_SIGN(12,13,14,15, l0_out, 0x40);
            } else if (hdr.bnn_pkt.nrs_recirc == 5) {
                WRITE_SIGN(8,9,10,11,   l0_out, 0x40);
            } else if (hdr.bnn_pkt.nrs_recirc == 6) {
                WRITE_SIGN(4,5,6,7,     l0_out, 0x40);
            } else {
                WRITE_SIGN(0,1,2,3,     l0_out, 0x40);
            }
        } else if(hdr.bnn_pkt.layer_no == 1 && hdr.bnn_pkt.pop_recirc == WIDTH_IX_L1) {
            if(hdr.bnn_pkt.nrs_recirc == 0) {
                WRITE_SIGN(4,5,6,7, l1_out, 0x10)
            } else if(hdr.bnn_pkt.nrs_recirc == 1) {
                WRITE_SIGN(0,1,2,3, l1_out, 0x10)
            }
        } else if(hdr.bnn_pkt.layer_no == 2 && hdr.bnn_pkt.pop_recirc == WIDTH_IX_L2) {
            WRITE_SIGN_BIN(0, 1, l2_out, 0x4)
        }
        /* -------------------------------------------------------------------- */


        /* egress port selection */
        egress_behaviour.apply();

        ig_tm_md.bypass_egress = 1w1;
    }
}

control BnnIngressDeparser(
    packet_out      pkt,
    inout bnn_headers_t hdr,
    in   empty_metadata_t meta,
    in   ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md)
{
    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.bnn_pkt);
    }
}



Pipeline(
    BnnIngressParser(),
    BnnIngress(),
    BnnIngressDeparser(),
    EmptyEgressParser(),
    EmptyEgress(),
    EmptyEgressDeparser()
) bnn_executor;
// Switch(bnn_executor) main;
