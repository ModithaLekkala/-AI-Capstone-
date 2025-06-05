/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>

#include "common/headers.p4"
#include "common/util.p4"

#define WRITE_POP_STEP(x) \
	cpy_32_8(); \
	step_pop_32_8_and(m##x##_32); \
	step_pop_32_8_shift(##x); \
	step_pop_32_8_shift_and(m##x##_32); \

parser IngressParser(
    packet_in pkt,
    out headers_t ig_hdr,
    out metadata_t ig_md,
    out ingress_intrinsic_metadata_t ig_intr_md)
{
    state start {
		pkt.extract(ig_intr_md);
        pkt.advance(PORT_METADATA_SIZE);

		pkt.extract(ig_hdr.ethernet);
		transition select(ig_hdr.ethernet.ether_type) {
			BNN_PKT_ETYPE : bnn_found;
			default       : accept;
		}
	}

	state bnn_found {
		pkt.extract(ig_hdr.bnn_pkt);
		transition accept;
	}
}
control Ingress(
    inout headers_t ig_hdr,
    inout metadata_t ig_md,
    in ingress_intrinsic_metadata_t ig_intr_md,
    in ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t ig_tm_md)
{
    action _drop() {
		ig_dprsr_md.drop_ctl = 1;
	}

	action send_back() {
		bit<48> tmp;
		/* Swap the MAC addresses */
		tmp = ig_hdr.ethernet.dst_addr;
		ig_hdr.ethernet.dst_addr = ig_hdr.ethernet.src_addr;
		ig_hdr.ethernet.src_addr = tmp;

		/* Send the packet back to the port it came from */
        ig_tm_md.ucast_egress_port = ig_intr_md.ingress_port;
	}

	action xor_32_8(bit<32> w_1, bit<32> w_2, bit<32> w_3, bit<32> w_4, bit<32> w_5, bit<32> w_6, bit<32> w_7, bit<32> w_8){
		ig_md.meta32_8.x1_0 = (ig_md.meta32_8.x1_0 ^ w_1);
		ig_md.meta32_8.x2_0 = (ig_md.meta32_8.x2_0 ^ w_2);
		ig_md.meta32_8.x3_0 = (ig_md.meta32_8.x3_0 ^ w_3);
		ig_md.meta32_8.x4_0 = (ig_md.meta32_8.x4_0 ^ w_4);
		ig_md.meta32_8.x5_0 = (ig_md.meta32_8.x5_0 ^ w_5);
		ig_md.meta32_8.x6_0 = (ig_md.meta32_8.x6_0 ^ w_6);
		ig_md.meta32_8.x7_0 = (ig_md.meta32_8.x7_0 ^ w_7);
		ig_md.meta32_8.x8_0 = (ig_md.meta32_8.x8_0 ^ w_8);
	}

	action step_pop_32_8_and(bit<32> m){
		ig_md.meta32_8.x1_0 = (ig_md.meta32_8.x1_0 & m);
		ig_md.meta32_8.x2_0 = (ig_md.meta32_8.x2_0 & m);
		ig_md.meta32_8.x3_0 = (ig_md.meta32_8.x3_0 & m);
		ig_md.meta32_8.x4_0 = (ig_md.meta32_8.x4_0 & m);
		ig_md.meta32_8.x5_0 = (ig_md.meta32_8.x5_0 & m);
		ig_md.meta32_8.x6_0 = (ig_md.meta32_8.x6_0 & m);
		ig_md.meta32_8.x7_0 = (ig_md.meta32_8.x7_0 & m);
		ig_md.meta32_8.x8_0 = (ig_md.meta32_8.x8_0 & m);
	}

	action step_pop_32_8_shift(bit<8> s){
		ig_md.meta32_8.x1_1 = ((ig_md.meta32_8.x1_1 >> s));
		ig_md.meta32_8.x2_1 = ((ig_md.meta32_8.x2_1 >> s));
		ig_md.meta32_8.x3_1 = ((ig_md.meta32_8.x3_1 >> s));
		ig_md.meta32_8.x4_1 = ((ig_md.meta32_8.x4_1 >> s));
		ig_md.meta32_8.x5_1 = ((ig_md.meta32_8.x5_1 >> s));
		ig_md.meta32_8.x6_1 = ((ig_md.meta32_8.x6_1 >> s));
		ig_md.meta32_8.x7_1 = ((ig_md.meta32_8.x7_1 >> s));
		ig_md.meta32_8.x8_1 = ((ig_md.meta32_8.x8_1 >> s));
	}
	action step_pop_32_8_shift_and(bit<32> m){
		ig_md.meta32_8.x1_1 = (ig_md.meta32_8.x1_1 & m);
		ig_md.meta32_8.x2_1 = (ig_md.meta32_8.x2_1 & m);
		ig_md.meta32_8.x3_1 = (ig_md.meta32_8.x3_1 & m);
		ig_md.meta32_8.x4_1 = (ig_md.meta32_8.x4_1 & m);
		ig_md.meta32_8.x5_1 = (ig_md.meta32_8.x5_1 & m);
		ig_md.meta32_8.x6_1 = (ig_md.meta32_8.x6_1 & m);
		ig_md.meta32_8.x7_1 = (ig_md.meta32_8.x7_1 & m);
	}
	action sum_32_8_a(){
		ig_md.meta32_8.x1_0 = ig_md.meta32_8.x1_0 + ig_md.meta32_8.x1_1;
		ig_md.meta32_8.x2_0 = ig_md.meta32_8.x2_0 + ig_md.meta32_8.x2_1;
		ig_md.meta32_8.x3_0 = ig_md.meta32_8.x3_0 + ig_md.meta32_8.x3_1;
		ig_md.meta32_8.x4_0 = ig_md.meta32_8.x4_0 + ig_md.meta32_8.x4_1;
		ig_md.meta32_8.x5_0 = ig_md.meta32_8.x5_0 + ig_md.meta32_8.x5_1;
		ig_md.meta32_8.x6_0 = ig_md.meta32_8.x6_0 + ig_md.meta32_8.x6_1;
		ig_md.meta32_8.x7_0 = ig_md.meta32_8.x7_0 + ig_md.meta32_8.x7_1;
		ig_md.meta32_8.x8_0 = ig_md.meta32_8.x8_0 + ig_md.meta32_8.x8_1;
	}

	action cpy_8_32(){
		ig_md.meta8_32.x1_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x2_1 = ig_md.meta8_32.x2_0;
		ig_md.meta8_32.x3_1 = ig_md.meta8_32.x3_0;
		ig_md.meta8_32.x4_1 = ig_md.meta8_32.x4_0;
		ig_md.meta8_32.x7_1 = ig_md.meta8_32.x7_0;
		ig_md.meta8_32.x9_1 = ig_md.meta8_32.x9_0;
		ig_md.meta8_32.x11_1 = ig_md.meta8_32.x11_0;
		ig_md.meta8_32.x12_1 = ig_md.meta8_32.x12_0;
		ig_md.meta8_32.x13_1 = ig_md.meta8_32.x13_0;
		ig_md.meta8_32.x14_1 = ig_md.meta8_32.x14_0;
		ig_md.meta8_32.x15_1 = ig_md.meta8_32.x15_0;
		ig_md.meta8_32.x16_1 = ig_md.meta8_32.x16_0;
		ig_md.meta8_32.x17_1 = ig_md.meta8_32.x17_0;
		ig_md.meta8_32.x18_1 = ig_md.meta8_32.x18_0;
		ig_md.meta8_32.x19_1 = ig_md.meta8_32.x19_0;
		ig_md.meta8_32.x20_1 = ig_md.meta8_32.x20_0;
		ig_md.meta8_32.x21_1 = ig_md.meta8_32.x21_0;
		ig_md.meta8_32.x22_1 = ig_md.meta8_32.x22_0;
		ig_md.meta8_32.x23_1 = ig_md.meta8_32.x23_0;
		ig_md.meta8_32.x24_1 = ig_md.meta8_32.x24_0;
		ig_md.meta8_32.x25_1 = ig_md.meta8_32.x25_0;
		ig_md.meta8_32.x26_1 = ig_md.meta8_32.x26_0;
		ig_md.meta8_32.x27_1 = ig_md.meta8_32.x27_0;
		ig_md.meta8_32.x28_1 = ig_md.meta8_32.x28_0;
		ig_md.meta8_32.x29_1 = ig_md.meta8_32.x29_0;
		ig_md.meta8_32.x30_1 = ig_md.meta8_32.x30_0;
		ig_md.meta8_32.x31_1 = ig_md.meta8_32.x31_0;
		ig_md.meta8_32.x32_1 = ig_md.meta8_32.x32_0;
	}

	action cpy_32_8(){
		ig_md.meta32_8.x1_1 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x2_1 = ig_md.meta32_8.x2_0;
		ig_md.meta32_8.x3_1 = ig_md.meta32_8.x3_0;
		ig_md.meta32_8.x4_1 = ig_md.meta32_8.x4_0;
		ig_md.meta32_8.x5_1 = ig_md.meta32_8.x5_0;
		ig_md.meta32_8.x6_1 = ig_md.meta32_8.x6_0;
		ig_md.meta32_8.x7_1 = ig_md.meta32_8.x7_0;
		ig_md.meta32_8.x8_1 = ig_md.meta32_8.x8_0;
	}

	action mcpy_8_32(){
		ig_md.meta8_32.x1_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x2_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x2_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x3_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x3_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x4_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x4_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x5_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x6_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x7_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x8_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x9_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x9_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x10_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x10_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x11_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x11_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x12_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x12_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x13_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x13_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x14_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x14_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x15_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x15_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x16_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x16_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x17_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x17_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x18_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x18_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x19_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x19_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x20_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x20_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x21_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x21_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x22_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x22_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x23_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x23_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x24_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x24_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x25_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x25_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x26_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x26_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x27_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x27_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x28_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x28_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x29_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x29_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x30_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x30_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x31_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x31_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x32_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x32_1 = ig_md.meta8_32.x1_0;
	}

	action mcpy_32_8(){
		ig_md.meta32_8.x1_1 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x2_0 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x2_1 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x3_0 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x3_1 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x4_0 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x4_1 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x5_0 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x5_1 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x6_0 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x6_1 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x7_0 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x7_1 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x8_0 = ig_md.meta32_8.x1_0;
		ig_md.meta32_8.x8_1 = ig_md.meta32_8.x1_0;
	}

	action l1_fold(){
		ig_md.meta8_32.x1_0[7:7] = ig_md.meta32_8.x1_0[0:0];
		ig_md.meta8_32.x1_0[6:6] = ig_md.meta32_8.x2_0[0:0];
		ig_md.meta8_32.x1_0[5:5] = ig_md.meta32_8.x3_0[0:0];
		ig_md.meta8_32.x1_0[4:4] = ig_md.meta32_8.x4_0[0:0];
		ig_md.meta8_32.x1_0[3:3] = ig_md.meta32_8.x5_0[0:0];
		ig_md.meta8_32.x1_0[2:2] = ig_md.meta32_8.x6_0[0:0];
		ig_md.meta8_32.x1_0[1:1] = ig_md.meta32_8.x7_0[0:0];
		ig_md.meta8_32.x1_0[0:0] = ig_md.meta32_8.x8_0[0:0];
	}


	/***** user actions *****/

	action get_nn_input(){
		//Here we can select the input features vector from packet header.
		ig_md.meta32_8.x1_0 = ig_hdr.bnn_pkt.x;

		//copy ig_md.meta32_8.x1_0 into ig_md.meta32_8.x**_0 and ig_md.meta32_8.x**_1
		mcpy_32_8();
	}

	action get_nn_output(){
		//Here we can select the destination packet header
		ig_hdr.bnn_pkt.x = ig_md.meta32_32.x1_0;
	}

	action fold() {
		l1_fold();
		mcpy_8_32();
	}

	table l1_xor_table {
		actions = { xor_32_8; NoAction; } 
		default_action = NoAction();
	}

	table fold_table{
		actions = {
			fold;
			_drop;
		}
		default_action = fold();
	}

	table sum_table{
		actions = {
			sum_32_8_a;
			_drop;
		}
		default_action = sum_32_8_a();
	}

	/****** user tables ******/

	table replication_table {

		key = {
			ig_hdr.ethernet.src_addr: exact;
		}
		actions = {
			get_nn_input;
		}
		const default_action = get_nn_input();
	}


	table get_nn_output_table {

		key = {
			ig_hdr.ethernet.src_addr: exact;
		}
		actions = {
			get_nn_output;
		}
		const default_action = get_nn_output();
	}


	table send_back_table {

		key = {
			ig_hdr.ethernet.src_addr: exact;
		}
		actions = {
			send_back;
			_drop;
		}
		const default_action = send_back();
		const entries = {
			MAC_SND : send_back();
		}

	}

	apply {
		replication_table.apply();

		l1_xor_table.apply();

		WRITE_POP_STEP(1)
		WRITE_POP_STEP(2)
		WRITE_POP_STEP(4)
		WRITE_POP_STEP(8)
		WRITE_POP_STEP(16)

		sum_table.apply();
		
		if (ig_md.meta32_8.x1_0 >= 16) 
			ig_md.meta32_8.x1_0 = 0;
		else 
			ig_md.meta32_8.x1_0 = 1;
		if (ig_md.meta32_8.x2_0 >= 16) 
			ig_md.meta32_8.x2_0 = 0;
		else 
			ig_md.meta32_8.x2_0 = 1;
		if (ig_md.meta32_8.x3_0 >= 16) 
			ig_md.meta32_8.x3_0 = 0;
		else 
			ig_md.meta32_8.x3_0 = 1;
		if (ig_md.meta32_8.x4_0 >= 16) 
			ig_md.meta32_8.x4_0 = 0;
		else 
			ig_md.meta32_8.x4_0 = 1;
		if (ig_md.meta32_8.x5_0 >= 16) 
			ig_md.meta32_8.x5_0 = 0;
		else 
			ig_md.meta32_8.x5_0 = 1;
		if (ig_md.meta32_8.x6_0 >= 16) 
			ig_md.meta32_8.x6_0 = 0;
		else 
			ig_md.meta32_8.x6_0 = 1;
		if (ig_md.meta32_8.x7_0 >= 16) 
			ig_md.meta32_8.x7_0 = 0;
		else 
			ig_md.meta32_8.x7_0 = 1;
		if (ig_md.meta32_8.x8_0 >= 16) 
			ig_md.meta32_8.x8_0 = 0;
		else 
			ig_md.meta32_8.x8_0 = 1;

		fold_table.apply();
		get_nn_output_table.apply();
		send_back_table.apply();

		ig_tm_md.bypass_egress = 1w1;
	}
}

control IngressDeparser(
    packet_out pkt,
    inout headers_t ig_hdr,
    in metadata_t ig_md,
    in ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md)
{
    apply {
		pkt.emit(ig_hdr);
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