// echo.p4
/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
#include "common/headers_8nrs.p4"
#include "common/util.p4"
#define POP_ACCUMULATE(y)\
    action pop_act##y(popcount_t popvalue) { hdr.bnn_pkt.pop##y## = hdr.bnn_pkt.pop##y## + popvalue;} \
    table pop##y{ \
        actions = { pop_act##y; } \
        key = { nr##y##: exact; } \
        size = 65535; \
        const default_action = pop_act##y(0xF); \
    }

#define WRITE_SIGN(frst, snd, thrd, frth, fifth, six, svn, eigt, layer) \
    if(hdr.bnn_pkt.pop1 >= 0x40) hdr.bnn_pkt.##layer##[##eigt##:##eigt##] = 0; else hdr.bnn_pkt.##layer##[##eigt##:##eigt##] = 1; \
    if(hdr.bnn_pkt.pop2 >= 0x40) hdr.bnn_pkt.##layer##[##svn##:##svn##] = 0; else hdr.bnn_pkt.##layer##[##svn##:##svn##] = 1; \
    if(hdr.bnn_pkt.pop3 >= 0x40) hdr.bnn_pkt.##layer##[##six##:##six##] = 0; else hdr.bnn_pkt.##layer##[##six##:##six##] = 1; \
    if(hdr.bnn_pkt.pop4 >= 0x40) hdr.bnn_pkt.##layer##[##fifth##:##fifth##] = 0; else hdr.bnn_pkt.##layer##[##fifth##:##fifth##] = 1; \
    if(hdr.bnn_pkt.pop5 >= 0x40) hdr.bnn_pkt.##layer##[##frth##:##frth##] = 0; else hdr.bnn_pkt.##layer##[##frth##:##frth##] = 1; \
    if(hdr.bnn_pkt.pop6 >= 0x40) hdr.bnn_pkt.##layer##[##thrd##:##thrd##] = 0; else hdr.bnn_pkt.##layer##[##thrd##:##thrd##] = 1; \
    if(hdr.bnn_pkt.pop7 >= 0x40) hdr.bnn_pkt.##layer##[##snd##:##snd##] = 0; else hdr.bnn_pkt.##layer##[##snd##:##snd##] = 1; \
    if(hdr.bnn_pkt.pop8 >= 0x40) hdr.bnn_pkt.##layer##[##frst##:##frst##] = 0; else hdr.bnn_pkt.##layer##[##frst##:##frst##] = 1; \

#define APPLY_POP() \
    pop1.apply(); \
    pop2.apply(); \
    pop3.apply(); \
    pop4.apply(); \
    pop5.apply(); \
    pop6.apply(); \
    pop7.apply(); \
    pop8.apply(); \

#define FREE_POP() \
    hdr.bnn_pkt.pop1 = 0; \
    hdr.bnn_pkt.pop2 = 0; \
    hdr.bnn_pkt.pop3 = 0; \
    hdr.bnn_pkt.pop4 = 0; \
    hdr.bnn_pkt.pop5 = 0; \
    hdr.bnn_pkt.pop6 = 0; \
    hdr.bnn_pkt.pop7 = 0; \
    hdr.bnn_pkt.pop8 = 0; \

#define COPY() \
    nr2 = nr1; \
    nr3 = nr1; \
    nr4 = nr1; \
    nr5 = nr1; \
    nr6 = nr1; \
    nr7 = nr1; \
    nr8 = nr1; \

#define WIDTH_IX_L0 7
#define WIDTH_IX_L1 1
#define HEIGTH_IX_L0 3
#define HEIGTH_IX_L1 0
#define INPUT_LEN 128
#define L0_WEIGHT_TB_SIZE 32
#define L1_WEIGHT_TB_SIZE 8
#define LAST_LAYER_NO 1

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
        transition accept;
        // transition select(ig_intr_md.ingress_port) {
        //     LAYER_RECIRC_PORT:  parse_bnn_pkt;
        //     POP_RECIRC_PORT: parse_recirc;
        //     default: parse_bnn_pkt; //start inference
        // }
    }

    // state parse_bnn_pkt {
    //     pkt.extract(hdr.bnn_pkt);
    //     transition accept;
    // }

    // state parse_recirc {
    //     pkt.extract(hdr.bnn_pkt);
    //     transition parse_bnn_pkt;
    // }

    // state parse_layer {
    //     pkt.extract(hdr.bnn_pkt);
    //     transition accept;
    // }
}

control Ingress(
    inout headers_t                                   hdr,
    inout metadata_t                              meta,
    in    ingress_intrinsic_metadata_t                 ig_intr_md,
    in    ingress_intrinsic_metadata_from_parser_t     ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t   ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t         ig_tm_md 
){
    bit<16> nr1=0;
    bit<16> nr2=0;
    bit<16> nr3=0;
    bit<16> nr4=0;
    bit<16> nr5=0;
    bit<16> nr6=0;
    bit<16> nr7=0;
    bit<16> nr8=0;

    Register<bit<16>, bit<16>>(8, 0x5555) bnn_input_reg;
    RegisterAction<bit<16>,bit<8>, bit<16>>(bnn_input_reg) get_bnn_input_reg = {
        void apply(inout bit<16> bnn_input, out bit<16> out_var) {
            out_var = bnn_input;
        }
    };


    action get_weights(bit<16> nr1_w, bit<16> nr2_w, bit<16> nr3_w, bit<16> nr4_w,
                          bit<16> nr5_w, bit<16> nr6_w, bit<16> nr7_w, bit<16> nr8_w) {
        nr1 = nr1_w ^ nr1;
        nr2 = nr2_w ^ nr2;
        nr3 = nr3_w ^ nr3;
        nr4 = nr4_w ^ nr4;
        nr5 = nr5_w ^ nr5;
        nr6 = nr6_w ^ nr6;
        nr7 = nr7_w ^ nr7;
        nr8 = nr8_w ^ nr8;
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
        hdr.bnn_pkt.layer_no += 1;
        // hdr.bnn_pkt.setInvalid();
        hdr.bnn_pkt.pop_recirc = 0;
        hdr.bnn_pkt.nrs_recirc = 0;
        ig_tm_md.ucast_egress_port = LAYER_RECIRC_PORT;
    }

    action send_back() {
        /*inference terminated*/
        // hdr.bnn_pkt.setInvalid();

        // bit<48> tmp = hdr.ethernet.dst_addr;
        hdr.ethernet.dst_addr = MAC_SND;
        // hdr.ethernet.src_addr = tmp;
        ig_tm_md.ucast_egress_port = (bit<9>)1;
        // ig_tm_md.ucast_egress_port = (bit<9>)hdr.bnn_pkt.original_port;
    }

    table egress_behaviour {
        actions = {
            pop_recirc; nrs_recirc; to_next_layer; send_back;
        }
        key = {
            hdr.bnn_pkt.layer_no: exact;
            hdr.bnn_pkt.pop_recirc: exact;
            hdr.bnn_pkt.nrs_recirc: exact;
        }
    }

    POP_ACCUMULATE(1)
    POP_ACCUMULATE(2)
    POP_ACCUMULATE(3)
    POP_ACCUMULATE(4)
    POP_ACCUMULATE(5)
    POP_ACCUMULATE(6)
    POP_ACCUMULATE(7)
    POP_ACCUMULATE(8)

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
        }

        APPLY_POP()

        /* ---- PARTIAL AND FINAL INFERENCE RESULT LOGIC FOR EACH LAYER ---- */
        if(hdr.bnn_pkt.pop_recirc == WIDTH_IX_L0 || hdr.bnn_pkt.pop_recirc == WIDTH_IX_L1) {
            if(hdr.bnn_pkt.layer_no == 0) {
                if(hdr.bnn_pkt.nrs_recirc == 0) {
                    WRITE_SIGN(24,25,26,27,28,29,30,31, l0_out)
                } else if(hdr.bnn_pkt.nrs_recirc == 1) {
                    WRITE_SIGN(16,17,18,19,20,21,22,23, l0_out)
                } else if(hdr.bnn_pkt.nrs_recirc == 2) {
                    WRITE_SIGN(8,9,10,11,12,13,14,15, l0_out)
                } else if(hdr.bnn_pkt.nrs_recirc >= HEIGTH_IX_L0) {
                    WRITE_SIGN(0,1,2,3,4,5,6,7, l0_out)
                }
            } else if(hdr.bnn_pkt.layer_no == 1) {
                WRITE_SIGN(0,1,2,3,4,5,6,7, l1_out)
            }
        }
        /* -------------------------------------------------------------------- */



        /*--------------------- EGRESS PORT SELECTION LOGIC --------------------*/

        /* generic orizontal recirculation logic*/
        egress_behaviour.apply();

        /*-----------------------------------------------------------------------*/

        // ig_tm_md.bypass_egress = 1w1;
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
    }
}



Pipeline(
    IngressParser(),
    Ingress(),
    IngressDeparser(),
    EmptyEgressParser(),
    EmptyEgress(),
    EmptyEgressDeparser()
) inethynn;
Switch(inethynn) main;
