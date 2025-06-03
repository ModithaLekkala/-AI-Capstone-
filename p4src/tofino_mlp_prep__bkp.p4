// echo.p4
/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
#include "common/headers.p4"
#include "common/util.p4"
#define WRITE_POP_PROC(y)\
    action pop_act##y(popcount_t popvalue) { o_nr##y##_pop__16 = popvalue; } \
    table pop##y{ \
        actions = { pop_act##y; } \ 
        key = { o_nr##y##_var__16: exact; } \
        size = 65535; \
        const default_action = pop_act##y(0xF); \
    }

parser IngressParser(
    packet_in pkt,
    out headers_t hdr,
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
        transition select(hdr.bnn_pkt.layer_ix) {
            4w0: parse_l1;
        }
    }

    state parse_l1 {
        pkt.extract(hdr.bnn_l1);
        transition accept;
    }


}

control Ingress(
    inout headers_t                                   hdr,
    inout empty_metadata_t                              meta,
    in    ingress_intrinsic_metadata_t                 ig_intr_md,
    in    ingress_intrinsic_metadata_from_parser_t     ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t   ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t         ig_tm_md 
){

    Register<bnn_input_t, _>(8) bnn_input_reg;  // A single 128-bit register cell (index 0)
    RegisterAction<bnn_input_t,_,void>(bnn_input_reg) get_bnn_input = {
        void apply(inout bnn_input_t bnn_input, out bnn_input_t output) {
            output = bnn_input;
        }
    }


    action trigger_counter(hdr.bnn_l1.pop1) {
        get_bnn_input.execute();
    }

    bit<128> o_nr1 = 0;
    bit<128> o_nr2 = 0;
    bit<128> o_nr3 = 0;
    bit<128> o_nr4 = 0;
    bit<128> o_nr5 = 0;
    bit<128> o_nr6 = 0;
    bit<128> o_nr7 = 0;
    bit<128> o_nr8 = 0;

    bit<128> o_nr1_w = 0;
    bit<128> o_nr2_w = 0;
    bit<128> o_nr3_w = 0;
    bit<128> o_nr4_w = 0;
    bit<128> o_nr5_w = 0;
    bit<128> o_nr6_w = 0;
    bit<128> o_nr7_w = 0;
    bit<128> o_nr8_w = 0;

    bit<16> o_nr1_var__16 = 0;
    bit<16> o_nr2_var__16 = 0;
    bit<16> o_nr3_var__16 = 0;
    bit<16> o_nr4_var__16 = 0;
    bit<16> o_nr5_var__16 = 0;
    bit<16> o_nr6_var__16 = 0;
    bit<16> o_nr7_var__16 = 0;
    bit<16> o_nr8_var__16 = 0;

    bit<8> o_nr1_pop__16 = 0;
    bit<8> o_nr2_pop__16 = 0;
    bit<8> o_nr3_pop__16 = 0;
    bit<8> o_nr4_pop__16 = 0;
    bit<8> o_nr5_pop__16 = 0;
    bit<8> o_nr6_pop__16 = 0;
    bit<8> o_nr7_pop__16 = 0;
    bit<8> o_nr8_pop__16 = 0;

    bit<8> l_out;

	action get_nn_input(){
		hdr.bnn_l1.nr_inpt1 = hdr.bnn_pkt.x;
        hdr.bnn_l1.nr_inpt2 = hdr.bnn_pkt.x;
        hdr.bnn_l1.nr_inpt3 = hdr.bnn_pkt.x;
        hdr.bnn_l1.nr_inpt4 = hdr.bnn_pkt.x;
        hdr.bnn_l1.nr_inpt5 = hdr.bnn_pkt.x;
        hdr.bnn_l1.nr_inpt6 = hdr.bnn_pkt.x;
        hdr.bnn_l1.nr_inpt7 = hdr.bnn_pkt.x;
        hdr.bnn_l1.nr_inpt8 = hdr.bnn_pkt.x;
	}

    // action set_nn_output() { hdr.bnn_pkt.x = (bit<128>)l_out;}

    action get_l1_weights(bit<128> nr1_w, bit<128> nr2_w, bit<128> nr3_w, bit<128> nr4_w, bit<128> nr5_w, bit<128> nr6_w, bit<128> nr7_w, bit<128> nr8_w) {
        o_nr1_w = nr1_w;
        o_nr2_w = nr2_w;
        o_nr3_w = nr3_w;
        o_nr4_w = nr4_w;
        o_nr5_w = nr5_w;
        o_nr6_w = nr6_w;
        o_nr7_w = nr7_w;
        o_nr8_w = nr8_w;
    }
    
    table l1_weights{
        actions = {
            get_l1_weights;
        }
        size = 8;
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
        // first input received
        if(ig_intr_md.ingress_port != POP_RECIRC_PORT && 
           ig_intr_md.ingress_port != LAYER_RECIRC_PORT) {
            hdr.bnn_pkt.original_port = ig_intr_md.ingress_port;
            // get_nn_input();
        }

        // first step inference
        if(ig_intr_md.ingress_port != POP_RECIRC_PORT ) {
            l1_weights.apply();
            o_nr1_w = hdr.bnn_l1.nr_inpt1 ^ o_nr1_w;
            o_nr2_w = hdr.bnn_l1.nr_inpt2 ^ o_nr2_w;
            o_nr3_w = hdr.bnn_l1.nr_inpt3 ^ o_nr3_w;
            o_nr4_w = hdr.bnn_l1.nr_inpt4 ^ o_nr4_w;
            o_nr5_w = hdr.bnn_l1.nr_inpt5 ^ o_nr5_w;
            o_nr6_w = hdr.bnn_l1.nr_inpt6 ^ o_nr6_w;
            o_nr7_w = hdr.bnn_l1.nr_inpt7 ^ o_nr7_w;
            o_nr8_w = hdr.bnn_l1.nr_inpt8 ^ o_nr8_w;

            o_nr1_var__16 = o_nr1_w[15:0];
            o_nr2_var__16 = o_nr2_w[15:0];
            o_nr3_var__16 = o_nr3_w[15:0];
            o_nr4_var__16 = o_nr4_w[15:0];
            o_nr5_var__16 = o_nr5_w[15:0];
            o_nr6_var__16 = o_nr6_w[15:0];
            o_nr7_var__16 = o_nr7_w[15:0];
            o_nr8_var__16 = o_nr8_w[15:0];
        } else {
            o_nr1_var__16 = hdr.bnn_l1.nr_inpt1[15:0];
            o_nr2_var__16 = hdr.bnn_l1.nr_inpt2[15:0];
            o_nr3_var__16 = hdr.bnn_l1.nr_inpt3[15:0];
            o_nr4_var__16 = hdr.bnn_l1.nr_inpt4[15:0];
            o_nr5_var__16 = hdr.bnn_l1.nr_inpt5[15:0];
            o_nr6_var__16 = hdr.bnn_l1.nr_inpt6[15:0];
            o_nr7_var__16 = hdr.bnn_l1.nr_inpt7[15:0];
            o_nr8_var__16 = hdr.bnn_l1.nr_inpt8[15:0];
        }

        pop1.apply();
        pop2.apply();
        pop3.apply();
        pop4.apply();
        pop5.apply();
        pop6.apply();
        pop7.apply();
        pop8.apply();

        // save partial popcount
        hdr.bnn_l1.pop1 += o_nr1_pop__16;
        hdr.bnn_l1.pop2 += o_nr2_pop__16;
        hdr.bnn_l1.pop3 += o_nr3_pop__16;
        hdr.bnn_l1.pop4 += o_nr4_pop__16;
        hdr.bnn_l1.pop5 += o_nr5_pop__16;
        hdr.bnn_l1.pop6 += o_nr6_pop__16;
        hdr.bnn_l1.pop7 += o_nr7_pop__16;
        hdr.bnn_l1.pop8 += o_nr8_pop__16;

        
        if(hdr.bnn_pkt.layer_ix == 1) { // 4 layer arch
            if(hdr.bnn_pkt.pop_recirc < 7) { // 8 recirculuation for (128-8) layer
                hdr.bnn_pkt.pop_recirc = hdr.bnn_pkt.pop_recirc + 1;
                ig_tm_md.ucast_egress_port = POP_RECIRC_PORT;

                hdr.bnn_l1.nr_inpt1 = hdr.bnn_l1.nr_inpt1 >> 16;
                hdr.bnn_l1.nr_inpt2 = hdr.bnn_l1.nr_inpt2 >> 16;
                hdr.bnn_l1.nr_inpt3 = hdr.bnn_l1.nr_inpt3 >> 16;
                hdr.bnn_l1.nr_inpt4 = hdr.bnn_l1.nr_inpt4 >> 16;
                hdr.bnn_l1.nr_inpt5 = hdr.bnn_l1.nr_inpt5 >> 16;
                hdr.bnn_l1.nr_inpt6 = hdr.bnn_l1.nr_inpt6 >> 16;
                hdr.bnn_l1.nr_inpt7 = hdr.bnn_l1.nr_inpt7 >> 16;
                hdr.bnn_l1.nr_inpt8 = hdr.bnn_l1.nr_inpt8 >> 16;
            } else {
                if(hdr.bnn_l1.pop1 >= 8) l_out[0:0] = 0; else l_out[0:0] = 1;
                if(hdr.bnn_l1.pop2 >= 8) l_out[1:1] = 0; else l_out[1:1] = 1;
                if(hdr.bnn_l1.pop3 >= 8) l_out[2:2] = 0; else l_out[2:2] = 1;
                if(hdr.bnn_l1.pop4 >= 8) l_out[3:3] = 0; else l_out[3:3] = 1;
                if(hdr.bnn_l1.pop5 >= 8) l_out[4:4] = 0; else l_out[4:4] = 1;
                if(hdr.bnn_l1.pop6 >= 8) l_out[5:5] = 0; else l_out[5:5] = 1;
                if(hdr.bnn_l1.pop7 >= 8) l_out[6:6] = 0; else l_out[6:6] = 1;
                if(hdr.bnn_l1.pop8 >= 8) l_out[7:7] = 0; else l_out[7:7] = 1;
                
                hdr.bnn_pkt.pop_recirc = 0;
                hdr.bnn_pkt.layer_ix = hdr.bnn_pkt.layer_ix + 1;
                ig_tm_md.ucast_egress_port = LAYER_RECIRC_PORT;

                /* set input for next layer*/
                hdr.bnn_pkt.prev_l_out = (bit<8>)l_out;

                bit<48> tmp = hdr.ethernet.dst_addr;
                hdr.ethernet.dst_addr = hdr.ethernet.src_addr;
                hdr.ethernet.src_addr = tmp;
                ig_tm_md.ucast_egress_port = hdr.bnn_pkt.original_port;
            }
        }
        // set_nn_output();
        ig_tm_md.bypass_egress = 1w1;
    }
}

control IngressDeparser(
    packet_out      pkt,
    inout headers_t hdr,
    in   empty_metadata_t meta,
    in   ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md)
{
    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.bnn_pkt);       
        pkt.emit(hdr.bnn_l1);    
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
