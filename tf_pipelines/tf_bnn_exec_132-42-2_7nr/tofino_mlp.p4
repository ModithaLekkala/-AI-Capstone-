/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
// #include "../common/headers.p4"
#include "common/headers.p4"
#include "common/util.p4"

#define WIDTH_IX_L0 9 /* (l0 weights width. / 16) -1  */
#define WIDTH_IX_L1 2
#define HEIGTH_IX_L0 5 /* (l0 neurons no. / 16) -1  */
#define HEIGTH_IX_L1 0
#define LAST_LAYER_NO 1 /* number of layers -1 */
#define INPUT_LAYER_THRESHOLD 0x42

#define POP_ACCUMULATE(y)\
    action pop_act##y(popcount_t popvalue) { hdr.bnn_pkt.pop##y## = hdr.bnn_pkt.pop##y## + popvalue;}\
    table pop##y{\
        actions = { pop_act##y; }\
        key = { nr##y##: exact; }\
        size = 16384;\
    }

#define WRITE_SIGN(frst, snd, thrd, frth, fifth, six, svn, layer, th) \
    if(hdr.bnn_pkt.pop1 >= th) hdr.bnn_pkt.##layer##[##svn##:##svn##] = 0; else {hdr.bnn_pkt.##layer##[##svn##:##svn##] = 1;hdr.bnn_pkt.l0_popcount = hdr.bnn_pkt.l0_popcount + 1;} \
    if(hdr.bnn_pkt.pop2 >= th) hdr.bnn_pkt.##layer##[##six##:##six##] = 0; else {hdr.bnn_pkt.##layer##[##six##:##six##] = 1;hdr.bnn_pkt.l0_popcount = hdr.bnn_pkt.l0_popcount + 1;} \
    if(hdr.bnn_pkt.pop3 >= th) hdr.bnn_pkt.##layer##[##fifth##:##fifth##] = 0; else {hdr.bnn_pkt.##layer##[##fifth##:##fifth##] = 1;hdr.bnn_pkt.l0_popcount = hdr.bnn_pkt.l0_popcount + 1;} \
    if(hdr.bnn_pkt.pop4 >= th) hdr.bnn_pkt.##layer##[##frth##:##frth##] = 0; else {hdr.bnn_pkt.##layer##[##frth##:##frth##] = 1;hdr.bnn_pkt.l0_popcount = hdr.bnn_pkt.l0_popcount + 1;} \
    if(hdr.bnn_pkt.pop5 >= th) hdr.bnn_pkt.##layer##[##thrd##:##thrd##] = 0; else {hdr.bnn_pkt.##layer##[##thrd##:##thrd##] = 1;hdr.bnn_pkt.l0_popcount = hdr.bnn_pkt.l0_popcount + 1;} \
    if(hdr.bnn_pkt.pop6 >= th) hdr.bnn_pkt.##layer##[##snd##:##snd##] = 0; else {hdr.bnn_pkt.##layer##[##snd##:##snd##] = 1;hdr.bnn_pkt.l0_popcount = hdr.bnn_pkt.l0_popcount + 1;} \
    if(hdr.bnn_pkt.pop7 >= th) hdr.bnn_pkt.##layer##[##frst##:##frst##] = 0; else {hdr.bnn_pkt.##layer##[##frst##:##frst##] = 1;hdr.bnn_pkt.l0_popcount = hdr.bnn_pkt.l0_popcount + 1;}

#define WRITE_SIGN_BIN(frst, snd, layer, th)\
    if(hdr.bnn_pkt.pop2 >= th) hdr.bnn_pkt.##layer##[##frst##:##frst##] = 0; else hdr.bnn_pkt.##layer##[##frst##:##frst##] = 1;\
    if(hdr.bnn_pkt.pop1 >= th) hdr.bnn_pkt.##layer##[##snd##:##snd##] = 0; else hdr.bnn_pkt.##layer##[##snd##:##snd##] = 1;

#define APPLY_POP()\
    pop1.apply();\
    pop2.apply();\
    if(hdr.bnn_pkt.layer_no == 0) {\
        pop3.apply();\
        pop4.apply();\
        pop5.apply();\
        pop6.apply();\
        pop7.apply();\
    }

#define FREE_POP()\
    hdr.bnn_pkt.pop1 = 0;\
    hdr.bnn_pkt.pop2 = 0;\
    hdr.bnn_pkt.pop3 = 0;\
    hdr.bnn_pkt.pop4 = 0;\
    hdr.bnn_pkt.pop5 = 0;\
    hdr.bnn_pkt.pop6 = 0;\
    hdr.bnn_pkt.pop7 = 0;

#define COPY()\
    nr2 = nr1;\
    nr3 = nr1;\
    nr4 = nr1;\
    nr5 = nr1;\
    nr6 = nr1;\
    nr7 = nr1;

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
    bit<14> nr1=0;
    bit<14> nr2=0;
    bit<14> nr3=0;
    bit<14> nr4=0;
    bit<14> nr5=0;
    bit<14> nr6=0;
    bit<14> nr7=0;

    Register<bit<16>, bit<16>>(9000) bnn_input_reg;
    RegisterAction<bit<16>,bit<16>, bit<14>>(bnn_input_reg) get_bnn_input_reg = {
        void apply(inout bit<16> bnn_input, out bit<14> out_var) {
            out_var = (bit<14>)bnn_input;
        }
    };

    action get_weights(bit<14> nr1_w, bit<14> nr2_w, bit<14> nr3_w, bit<14> nr4_w, bit<14> nr5_w, bit<14> nr6_w, bit<14> nr7_w) {
        nr1 = nr1_w ^ nr1;
        nr2 = nr2_w ^ nr2;
        nr3 = nr3_w ^ nr3;
        nr4 = nr4_w ^ nr4;
        nr5 = nr5_w ^ nr5;
        nr6 = nr6_w ^ nr6;
        nr7 = nr7_w ^ nr7;
    }
    
    action get_bin_weights(bit<14> nr1_w, bit<14> nr2_w) {
        nr1 = nr1_w ^ nr1;
        nr2 = nr2_w ^ nr2;
    }

    table l0_weights{
        actions = { get_weights; }
        key = { 
            hdr.bnn_pkt.pop_recirc: exact;
            hdr.bnn_pkt.nrs_recirc: exact;
        }
    }

    table l1_weights{
        actions = { get_bin_weights; }
        key = {
            hdr.bnn_pkt.pop_recirc: exact;
            hdr.bnn_pkt.nrs_recirc: exact;
        }
    }

    /* ---- Confidence Lookup Table (populated by CP) ---- */
    action set_confidence(bit<8> confident) {
        hdr.bnn_pkt.is_pred_confident = confident;
    }

    table confidence_lookup {
        actions = { set_confidence; }
        key = {
            hdr.bnn_pkt.l0_popcount: exact;
        }
        default_action = set_confidence(0);
    }

    action pop_recirc() {
        ig_tm_md.ucast_egress_port = POP_RECIRC_PORT;
        hdr.bnn_pkt.pop_recirc = hdr.bnn_pkt.pop_recirc + 1;
    }

    action nrs_recirc() {
        FREE_POP()
                
        hdr.bnn_pkt.pop_recirc = 0;
        hdr.bnn_pkt.nrs_recirc = hdr.bnn_pkt.nrs_recirc + 1;
        hdr.bnn_pkt.input_offset= hdr.bnn_pkt.input_offset_cp;
        ig_tm_md.ucast_egress_port = POP_RECIRC_PORT;
    }

    action to_next_layer() {
        FREE_POP()
        /* current layer completed executed 
            send result for next layer processing */
        hdr.bnn_pkt.layer_no = hdr.bnn_pkt.layer_no + 1;
        hdr.bnn_pkt.pop_recirc = 0;
        hdr.bnn_pkt.nrs_recirc = 0;
        hdr.bnn_pkt.input_offset= 0;
        ig_tm_md.ucast_egress_port = LAYER_RECIRC_PORT;
    }

    action send_back() {
        /*inference terminated*/
        ig_tm_md.ucast_egress_port = (bit<9>)CPU_PORT;
    }

    action drop_pkt() {
        ig_dprsr_md.drop_ctl = 1;
    }

    /* handles recirculations and egress behavior */
    table egress_behaviour {
        actions = {
            pop_recirc; nrs_recirc; to_next_layer; send_back; drop_pkt;
        }
        key = {
            hdr.bnn_pkt.layer_no: exact;
            hdr.bnn_pkt.pop_recirc: exact;
            hdr.bnn_pkt.nrs_recirc: ternary;
            hdr.bnn_pkt.is_pred_confident: ternary;
            hdr.bnn_pkt.l1_out: ternary;
        }
        const entries = {
            // L0 done → next layer
            ( 0, WIDTH_IX_L0, HEIGTH_IX_L0 &&& 0xFF, 0 &&& 0x00, 0 &&& 0x00 ) : to_next_layer();
            // Inference done, confident + legit (bit[1]==0) → drop
            ( 1, WIDTH_IX_L1, HEIGTH_IX_L1 &&& 0xFF, 1 &&& 0xFF, 0 &&& 0x02 ) : drop_pkt();
            // Inference done, all other cases → send to CPU
            ( 1, WIDTH_IX_L1, HEIGTH_IX_L1 &&& 0xFF, 0 &&& 0x00, 0 &&& 0x00 ) : send_back();
            // L0 intermediate recirculations
            ( 0, WIDTH_IX_L0, 0 &&& 0x00, 0 &&& 0x00, 0 &&& 0x00 )            : nrs_recirc();
            // L1 intermediate recirculations
            ( 1, WIDTH_IX_L1, 0 &&& 0x00, 0 &&& 0x00, 0 &&& 0x00 )            : nrs_recirc();
        }
        const default_action = pop_recirc();
        size=256;
    }

    POP_ACCUMULATE(1)
    POP_ACCUMULATE(2)
    POP_ACCUMULATE(3)
    POP_ACCUMULATE(4)
    POP_ACCUMULATE(5)
    POP_ACCUMULATE(6)
    POP_ACCUMULATE(7)

    apply { 

        /* -------------- SET ACTIVATIONS AND WEIGHTS FOR EACH LAYER -------------- */
        if(hdr.bnn_pkt.layer_no == 0) {
            /* get register input */
            nr1 = get_bnn_input_reg.execute(hdr.bnn_pkt.input_offset); //hdr.bnn_pkt.pop_recirc == input register offset indexed by cp
            COPY()
            l0_weights.apply();
        } else if(hdr.bnn_pkt.layer_no == 1){
            if(hdr.bnn_pkt.pop_recirc == 0) {
                nr1 = ((bit<14>)hdr.bnn_pkt.l0_out_1 << 7) | (bit<14>)hdr.bnn_pkt.l0_out_2;
            } else if (hdr.bnn_pkt.pop_recirc == 1) {
                nr1 = ((bit<14>)hdr.bnn_pkt.l0_out_3 << 7) | (bit<14>)hdr.bnn_pkt.l0_out_4;
            } 
            else if (hdr.bnn_pkt.pop_recirc == 2) {
                nr1 = ((bit<14>)hdr.bnn_pkt.l0_out_5 << 7) | (bit<14>)hdr.bnn_pkt.l0_out_6;
            }
            nr2 = nr1; //COPY()
            l1_weights.apply();
        }

        APPLY_POP()

        /* ---- PARTIAL AND FINAL INFERENCE RESULT LOGIC FOR EACH LAYER ---- */
        if(hdr.bnn_pkt.layer_no == 0 && hdr.bnn_pkt.pop_recirc == WIDTH_IX_L0) {
            if (hdr.bnn_pkt.nrs_recirc == 0) {
                WRITE_SIGN(0,1,2,3,4,5,6,   l0_out_1, INPUT_LAYER_THRESHOLD);
            } else if (hdr.bnn_pkt.nrs_recirc == 1) {
                WRITE_SIGN(0,1,2,3,4,5,6,   l0_out_2, INPUT_LAYER_THRESHOLD);
            } else if (hdr.bnn_pkt.nrs_recirc == 2) {
                WRITE_SIGN(0,1,2,3,4,5,6,   l0_out_3, INPUT_LAYER_THRESHOLD);
            } else if (hdr.bnn_pkt.nrs_recirc == 3) {
                WRITE_SIGN(0,1,2,3,4,5,6,   l0_out_4, INPUT_LAYER_THRESHOLD);
            } else if (hdr.bnn_pkt.nrs_recirc == 4) {
                WRITE_SIGN(0,1,2,3,4,5,6,   l0_out_5, INPUT_LAYER_THRESHOLD);
            } else {
                WRITE_SIGN(0,1,2,3,4,5,6,   l0_out_6, INPUT_LAYER_THRESHOLD);
            } 
        } 
        else if(hdr.bnn_pkt.layer_no == 1 && hdr.bnn_pkt.pop_recirc == WIDTH_IX_L1) {
            WRITE_SIGN_BIN(0, 1, l1_out, 0x15)
            confidence_lookup.apply();
        }
        /* -------------------------------------------------------------------- */

        /* Update input index */
        if(hdr.bnn_pkt.layer_no == 0 && hdr.bnn_pkt.pop_recirc < WIDTH_IX_L0) {
            hdr.bnn_pkt.input_offset = hdr.bnn_pkt.input_offset+1;
        }

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
