/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>

#include "common/headers.p4"
#include "common/util.p4"


parser IngressParser(
    packet_in pkt,
    out headers_t ig_hdr,
    out metadata_t ig_md,
    out ingress_intrinsic_metadata_t ig_intr_md)
{
    state start {
		pkt.extract(ig_hdr.ethernet);
		transition select(ig_hdr.ethernet.ether_type) {
			0x800: parse_ipv4;
			BNN_PKT_ETYPE : bnn_found;
			default       : accept;
		}
	}

	state bnn_found {
		pkt.extract(ig_hdr.bnn_pkt);
		transition accept;
	}

	state parse_ipv4 {
        pkt.extract(ig_hdr.ipv4);
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

	action xor_32_32(bit<32> w_1, bit<32> w_2, bit<32> w_3, bit<32> w_4, bit<32> w_5, bit<32> w_6, bit<32> w_7, bit<32> w_8, bit<32> w_9, bit<32> w_10, bit<32> w_11, bit<32> w_12, bit<32> w_13, bit<32> w_14, bit<32> w_15, bit<32> w_16, bit<32> w_17, bit<32> w_18, bit<32> w_19, bit<32> w_20, bit<32> w_21, bit<32> w_22, bit<32> w_23, bit<32> w_24, bit<32> w_25, bit<32> w_26, bit<32> w_27, bit<32> w_28, bit<32> w_29, bit<32> w_30, bit<32> w_31, bit<32> w_32){
		ig_md.meta32_32.x1_0 = (ig_md.meta32_32.x1_0 ^ w_1);
		ig_md.meta32_32.x2_0 = (ig_md.meta32_32.x2_0 ^ w_2);
		ig_md.meta32_32.x3_0 = (ig_md.meta32_32.x3_0 ^ w_3);
		ig_md.meta32_32.x4_0 = (ig_md.meta32_32.x4_0 ^ w_4);
		ig_md.meta32_32.x5_0 = (ig_md.meta32_32.x5_0 ^ w_5);
		ig_md.meta32_32.x6_0 = (ig_md.meta32_32.x6_0 ^ w_6);
		ig_md.meta32_32.x7_0 = (ig_md.meta32_32.x7_0 ^ w_7);
		ig_md.meta32_32.x8_0 = (ig_md.meta32_32.x8_0 ^ w_8);
		ig_md.meta32_32.x9_0 = (ig_md.meta32_32.x9_0 ^ w_9);
		ig_md.meta32_32.x10_0 = (ig_md.meta32_32.x10_0 ^ w_10);
		ig_md.meta32_32.x11_0 = (ig_md.meta32_32.x11_0 ^ w_11);
		ig_md.meta32_32.x12_0 = (ig_md.meta32_32.x12_0 ^ w_12);
		ig_md.meta32_32.x13_0 = (ig_md.meta32_32.x13_0 ^ w_13);
		ig_md.meta32_32.x14_0 = (ig_md.meta32_32.x14_0 ^ w_14);
		ig_md.meta32_32.x15_0 = (ig_md.meta32_32.x15_0 ^ w_15);
		ig_md.meta32_32.x16_0 = (ig_md.meta32_32.x16_0 ^ w_16);
		ig_md.meta32_32.x17_0 = (ig_md.meta32_32.x17_0 ^ w_17);
		ig_md.meta32_32.x18_0 = (ig_md.meta32_32.x18_0 ^ w_18);
		ig_md.meta32_32.x19_0 = (ig_md.meta32_32.x19_0 ^ w_19);
		ig_md.meta32_32.x20_0 = (ig_md.meta32_32.x20_0 ^ w_20);
		ig_md.meta32_32.x21_0 = (ig_md.meta32_32.x21_0 ^ w_21);
		ig_md.meta32_32.x22_0 = (ig_md.meta32_32.x22_0 ^ w_22);
		ig_md.meta32_32.x23_0 = (ig_md.meta32_32.x23_0 ^ w_23);
		ig_md.meta32_32.x24_0 = (ig_md.meta32_32.x24_0 ^ w_24);
		ig_md.meta32_32.x25_0 = (ig_md.meta32_32.x25_0 ^ w_25);
		ig_md.meta32_32.x26_0 = (ig_md.meta32_32.x26_0 ^ w_26);
		ig_md.meta32_32.x27_0 = (ig_md.meta32_32.x27_0 ^ w_27);
		ig_md.meta32_32.x28_0 = (ig_md.meta32_32.x28_0 ^ w_28);
		ig_md.meta32_32.x29_0 = (ig_md.meta32_32.x29_0 ^ w_29);
		ig_md.meta32_32.x30_0 = (ig_md.meta32_32.x30_0 ^ w_30);
		ig_md.meta32_32.x31_0 = (ig_md.meta32_32.x31_0 ^ w_31);
		ig_md.meta32_32.x32_0 = (ig_md.meta32_32.x32_0 ^ w_32);
	}

	action xor_8_32(bit<8> w_1, bit<8> w_2, bit<8> w_3, bit<8> w_4, bit<8> w_5, bit<8> w_6, bit<8> w_7, bit<8> w_8, bit<8> w_9, bit<8> w_10, bit<8> w_11, bit<8> w_12, bit<8> w_13, bit<8> w_14, bit<8> w_15, bit<8> w_16, bit<8> w_17, bit<8> w_18, bit<8> w_19, bit<8> w_20, bit<8> w_21, bit<8> w_22, bit<8> w_23, bit<8> w_24, bit<8> w_25, bit<8> w_26, bit<8> w_27, bit<8> w_28, bit<8> w_29, bit<8> w_30, bit<8> w_31, bit<8> w_32){
		ig_md.meta8_32.x1_0 = (ig_md.meta8_32.x1_0 ^ w_1);
		ig_md.meta8_32.x2_0 = (ig_md.meta8_32.x2_0 ^ w_2);
		ig_md.meta8_32.x3_0 = (ig_md.meta8_32.x3_0 ^ w_3);
		ig_md.meta8_32.x4_0 = (ig_md.meta8_32.x4_0 ^ w_4);
		ig_md.meta8_32.x5_0 = (ig_md.meta8_32.x5_0 ^ w_5);
		ig_md.meta8_32.x6_0 = (ig_md.meta8_32.x6_0 ^ w_6);
		ig_md.meta8_32.x7_0 = (ig_md.meta8_32.x7_0 ^ w_7);
		ig_md.meta8_32.x8_0 = (ig_md.meta8_32.x8_0 ^ w_8);
		ig_md.meta8_32.x9_0 = (ig_md.meta8_32.x9_0 ^ w_9);
		ig_md.meta8_32.x10_0 = (ig_md.meta8_32.x10_0 ^ w_10);
		ig_md.meta8_32.x11_0 = (ig_md.meta8_32.x11_0 ^ w_11);
		ig_md.meta8_32.x12_0 = (ig_md.meta8_32.x12_0 ^ w_12);
		ig_md.meta8_32.x13_0 = (ig_md.meta8_32.x13_0 ^ w_13);
		ig_md.meta8_32.x14_0 = (ig_md.meta8_32.x14_0 ^ w_14);
		ig_md.meta8_32.x15_0 = (ig_md.meta8_32.x15_0 ^ w_15);
		ig_md.meta8_32.x16_0 = (ig_md.meta8_32.x16_0 ^ w_16);
		ig_md.meta8_32.x17_0 = (ig_md.meta8_32.x17_0 ^ w_17);
		ig_md.meta8_32.x18_0 = (ig_md.meta8_32.x18_0 ^ w_18);
		ig_md.meta8_32.x19_0 = (ig_md.meta8_32.x19_0 ^ w_19);
		ig_md.meta8_32.x20_0 = (ig_md.meta8_32.x20_0 ^ w_20);
		ig_md.meta8_32.x21_0 = (ig_md.meta8_32.x21_0 ^ w_21);
		ig_md.meta8_32.x22_0 = (ig_md.meta8_32.x22_0 ^ w_22);
		ig_md.meta8_32.x23_0 = (ig_md.meta8_32.x23_0 ^ w_23);
		ig_md.meta8_32.x24_0 = (ig_md.meta8_32.x24_0 ^ w_24);
		ig_md.meta8_32.x25_0 = (ig_md.meta8_32.x25_0 ^ w_25);
		ig_md.meta8_32.x26_0 = (ig_md.meta8_32.x26_0 ^ w_26);
		ig_md.meta8_32.x27_0 = (ig_md.meta8_32.x27_0 ^ w_27);
		ig_md.meta8_32.x28_0 = (ig_md.meta8_32.x28_0 ^ w_28);
		ig_md.meta8_32.x29_0 = (ig_md.meta8_32.x29_0 ^ w_29);
		ig_md.meta8_32.x30_0 = (ig_md.meta8_32.x30_0 ^ w_30);
		ig_md.meta8_32.x31_0 = (ig_md.meta8_32.x31_0 ^ w_31);
		ig_md.meta8_32.x32_0 = (ig_md.meta8_32.x32_0 ^ w_32);
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

	action step_pop_32_32(bit<32> m, bit<8> s){
		ig_md.meta32_32.x1_0 = (ig_md.meta32_32.x1_0 & m);
		ig_md.meta32_32.x1_1 = ((ig_md.meta32_32.x1_1 >> s) & m);
		ig_md.meta32_32.x2_0 = (ig_md.meta32_32.x2_0 & m);
		ig_md.meta32_32.x2_1 = ((ig_md.meta32_32.x2_1 >> s) & m);
		ig_md.meta32_32.x3_0 = (ig_md.meta32_32.x3_0 & m);
		ig_md.meta32_32.x3_1 = ((ig_md.meta32_32.x3_1 >> s) & m);
		ig_md.meta32_32.x4_0 = (ig_md.meta32_32.x4_0 & m);
		ig_md.meta32_32.x4_1 = ((ig_md.meta32_32.x4_1 >> s) & m);
		ig_md.meta32_32.x5_0 = (ig_md.meta32_32.x5_0 & m);
		ig_md.meta32_32.x5_1 = ((ig_md.meta32_32.x5_1 >> s) & m);
		ig_md.meta32_32.x6_0 = (ig_md.meta32_32.x6_0 & m);
		ig_md.meta32_32.x6_1 = ((ig_md.meta32_32.x6_1 >> s) & m);
		ig_md.meta32_32.x7_0 = (ig_md.meta32_32.x7_0 & m);
		ig_md.meta32_32.x7_1 = ((ig_md.meta32_32.x7_1 >> s) & m);
		ig_md.meta32_32.x8_0 = (ig_md.meta32_32.x8_0 & m);
		ig_md.meta32_32.x8_1 = ((ig_md.meta32_32.x8_1 >> s) & m);
		ig_md.meta32_32.x9_0 = (ig_md.meta32_32.x9_0 & m);
		ig_md.meta32_32.x9_1 = ((ig_md.meta32_32.x9_1 >> s) & m);
		ig_md.meta32_32.x10_0 = (ig_md.meta32_32.x10_0 & m);
		ig_md.meta32_32.x10_1 = ((ig_md.meta32_32.x10_1 >> s) & m);
		ig_md.meta32_32.x11_0 = (ig_md.meta32_32.x11_0 & m);
		ig_md.meta32_32.x11_1 = ((ig_md.meta32_32.x11_1 >> s) & m);
		ig_md.meta32_32.x12_0 = (ig_md.meta32_32.x12_0 & m);
		ig_md.meta32_32.x12_1 = ((ig_md.meta32_32.x12_1 >> s) & m);
		ig_md.meta32_32.x13_0 = (ig_md.meta32_32.x13_0 & m);
		ig_md.meta32_32.x13_1 = ((ig_md.meta32_32.x13_1 >> s) & m);
		ig_md.meta32_32.x14_0 = (ig_md.meta32_32.x14_0 & m);
		ig_md.meta32_32.x14_1 = ((ig_md.meta32_32.x14_1 >> s) & m);
		ig_md.meta32_32.x15_0 = (ig_md.meta32_32.x15_0 & m);
		ig_md.meta32_32.x15_1 = ((ig_md.meta32_32.x15_1 >> s) & m);
		ig_md.meta32_32.x16_0 = (ig_md.meta32_32.x16_0 & m);
		ig_md.meta32_32.x16_1 = ((ig_md.meta32_32.x16_1 >> s) & m);
		ig_md.meta32_32.x17_0 = (ig_md.meta32_32.x17_0 & m);
		ig_md.meta32_32.x17_1 = ((ig_md.meta32_32.x17_1 >> s) & m);
		ig_md.meta32_32.x18_0 = (ig_md.meta32_32.x18_0 & m);
		ig_md.meta32_32.x18_1 = ((ig_md.meta32_32.x18_1 >> s) & m);
		ig_md.meta32_32.x19_0 = (ig_md.meta32_32.x19_0 & m);
		ig_md.meta32_32.x19_1 = ((ig_md.meta32_32.x19_1 >> s) & m);
		ig_md.meta32_32.x20_0 = (ig_md.meta32_32.x20_0 & m);
		ig_md.meta32_32.x20_1 = ((ig_md.meta32_32.x20_1 >> s) & m);
		ig_md.meta32_32.x21_0 = (ig_md.meta32_32.x21_0 & m);
		ig_md.meta32_32.x21_1 = ((ig_md.meta32_32.x21_1 >> s) & m);
		ig_md.meta32_32.x22_0 = (ig_md.meta32_32.x22_0 & m);
		ig_md.meta32_32.x22_1 = ((ig_md.meta32_32.x22_1 >> s) & m);
		ig_md.meta32_32.x23_0 = (ig_md.meta32_32.x23_0 & m);
		ig_md.meta32_32.x23_1 = ((ig_md.meta32_32.x23_1 >> s) & m);
		ig_md.meta32_32.x24_0 = (ig_md.meta32_32.x24_0 & m);
		ig_md.meta32_32.x24_1 = ((ig_md.meta32_32.x24_1 >> s) & m);
		ig_md.meta32_32.x25_0 = (ig_md.meta32_32.x25_0 & m);
		ig_md.meta32_32.x25_1 = ((ig_md.meta32_32.x25_1 >> s) & m);
		ig_md.meta32_32.x26_0 = (ig_md.meta32_32.x26_0 & m);
		ig_md.meta32_32.x26_1 = ((ig_md.meta32_32.x26_1 >> s) & m);
		ig_md.meta32_32.x27_0 = (ig_md.meta32_32.x27_0 & m);
		ig_md.meta32_32.x27_1 = ((ig_md.meta32_32.x27_1 >> s) & m);
		ig_md.meta32_32.x28_0 = (ig_md.meta32_32.x28_0 & m);
		ig_md.meta32_32.x28_1 = ((ig_md.meta32_32.x28_1 >> s) & m);
		ig_md.meta32_32.x29_0 = (ig_md.meta32_32.x29_0 & m);
		ig_md.meta32_32.x29_1 = ((ig_md.meta32_32.x29_1 >> s) & m);
		ig_md.meta32_32.x30_0 = (ig_md.meta32_32.x30_0 & m);
		ig_md.meta32_32.x30_1 = ((ig_md.meta32_32.x30_1 >> s) & m);
		ig_md.meta32_32.x31_0 = (ig_md.meta32_32.x31_0 & m);
		ig_md.meta32_32.x31_1 = ((ig_md.meta32_32.x31_1 >> s) & m);
		ig_md.meta32_32.x32_0 = (ig_md.meta32_32.x32_0 & m);
		ig_md.meta32_32.x32_1 = ((ig_md.meta32_32.x32_1 >> s) & m);
	}

	action step_pop_8_32(bit<8> m, bit<8> s){
		ig_md.meta8_32.x1_0 = (ig_md.meta8_32.x1_0 & m);
		ig_md.meta8_32.x1_1 = ((ig_md.meta8_32.x1_1 >> s) & m);
		ig_md.meta8_32.x2_0 = (ig_md.meta8_32.x2_0 & m);
		ig_md.meta8_32.x2_1 = ((ig_md.meta8_32.x2_1 >> s) & m);
		ig_md.meta8_32.x3_0 = (ig_md.meta8_32.x3_0 & m);
		ig_md.meta8_32.x3_1 = ((ig_md.meta8_32.x3_1 >> s) & m);
		ig_md.meta8_32.x4_0 = (ig_md.meta8_32.x4_0 & m);
		ig_md.meta8_32.x4_1 = ((ig_md.meta8_32.x4_1 >> s) & m);
		ig_md.meta8_32.x5_0 = (ig_md.meta8_32.x5_0 & m);
		ig_md.meta8_32.x5_1 = ((ig_md.meta8_32.x5_1 >> s) & m);
		ig_md.meta8_32.x6_0 = (ig_md.meta8_32.x6_0 & m);
		ig_md.meta8_32.x6_1 = ((ig_md.meta8_32.x6_1 >> s) & m);
		ig_md.meta8_32.x7_0 = (ig_md.meta8_32.x7_0 & m);
		ig_md.meta8_32.x7_1 = ((ig_md.meta8_32.x7_1 >> s) & m);
		ig_md.meta8_32.x8_0 = (ig_md.meta8_32.x8_0 & m);
		ig_md.meta8_32.x8_1 = ((ig_md.meta8_32.x8_1 >> s) & m);
		ig_md.meta8_32.x9_0 = (ig_md.meta8_32.x9_0 & m);
		ig_md.meta8_32.x9_1 = ((ig_md.meta8_32.x9_1 >> s) & m);
		ig_md.meta8_32.x10_0 = (ig_md.meta8_32.x10_0 & m);
		ig_md.meta8_32.x10_1 = ((ig_md.meta8_32.x10_1 >> s) & m);
		ig_md.meta8_32.x11_0 = (ig_md.meta8_32.x11_0 & m);
		ig_md.meta8_32.x11_1 = ((ig_md.meta8_32.x11_1 >> s) & m);
		ig_md.meta8_32.x12_0 = (ig_md.meta8_32.x12_0 & m);
		ig_md.meta8_32.x12_1 = ((ig_md.meta8_32.x12_1 >> s) & m);
		ig_md.meta8_32.x13_0 = (ig_md.meta8_32.x13_0 & m);
		ig_md.meta8_32.x13_1 = ((ig_md.meta8_32.x13_1 >> s) & m);
		ig_md.meta8_32.x14_0 = (ig_md.meta8_32.x14_0 & m);
		ig_md.meta8_32.x14_1 = ((ig_md.meta8_32.x14_1 >> s) & m);
		ig_md.meta8_32.x15_0 = (ig_md.meta8_32.x15_0 & m);
		ig_md.meta8_32.x15_1 = ((ig_md.meta8_32.x15_1 >> s) & m);
		ig_md.meta8_32.x16_0 = (ig_md.meta8_32.x16_0 & m);
		ig_md.meta8_32.x16_1 = ((ig_md.meta8_32.x16_1 >> s) & m);
		ig_md.meta8_32.x17_0 = (ig_md.meta8_32.x17_0 & m);
		ig_md.meta8_32.x17_1 = ((ig_md.meta8_32.x17_1 >> s) & m);
		ig_md.meta8_32.x18_0 = (ig_md.meta8_32.x18_0 & m);
		ig_md.meta8_32.x18_1 = ((ig_md.meta8_32.x18_1 >> s) & m);
		ig_md.meta8_32.x19_0 = (ig_md.meta8_32.x19_0 & m);
		ig_md.meta8_32.x19_1 = ((ig_md.meta8_32.x19_1 >> s) & m);
		ig_md.meta8_32.x20_0 = (ig_md.meta8_32.x20_0 & m);
		ig_md.meta8_32.x20_1 = ((ig_md.meta8_32.x20_1 >> s) & m);
		ig_md.meta8_32.x21_0 = (ig_md.meta8_32.x21_0 & m);
		ig_md.meta8_32.x21_1 = ((ig_md.meta8_32.x21_1 >> s) & m);
		ig_md.meta8_32.x22_0 = (ig_md.meta8_32.x22_0 & m);
		ig_md.meta8_32.x22_1 = ((ig_md.meta8_32.x22_1 >> s) & m);
		ig_md.meta8_32.x23_0 = (ig_md.meta8_32.x23_0 & m);
		ig_md.meta8_32.x23_1 = ((ig_md.meta8_32.x23_1 >> s) & m);
		ig_md.meta8_32.x24_0 = (ig_md.meta8_32.x24_0 & m);
		ig_md.meta8_32.x24_1 = ((ig_md.meta8_32.x24_1 >> s) & m);
		ig_md.meta8_32.x25_0 = (ig_md.meta8_32.x25_0 & m);
		ig_md.meta8_32.x25_1 = ((ig_md.meta8_32.x25_1 >> s) & m);
		ig_md.meta8_32.x26_0 = (ig_md.meta8_32.x26_0 & m);
		ig_md.meta8_32.x26_1 = ((ig_md.meta8_32.x26_1 >> s) & m);
		ig_md.meta8_32.x27_0 = (ig_md.meta8_32.x27_0 & m);
		ig_md.meta8_32.x27_1 = ((ig_md.meta8_32.x27_1 >> s) & m);
		ig_md.meta8_32.x28_0 = (ig_md.meta8_32.x28_0 & m);
		ig_md.meta8_32.x28_1 = ((ig_md.meta8_32.x28_1 >> s) & m);
		ig_md.meta8_32.x29_0 = (ig_md.meta8_32.x29_0 & m);
		ig_md.meta8_32.x29_1 = ((ig_md.meta8_32.x29_1 >> s) & m);
		ig_md.meta8_32.x30_0 = (ig_md.meta8_32.x30_0 & m);
		ig_md.meta8_32.x30_1 = ((ig_md.meta8_32.x30_1 >> s) & m);
		ig_md.meta8_32.x31_0 = (ig_md.meta8_32.x31_0 & m);
		ig_md.meta8_32.x31_1 = ((ig_md.meta8_32.x31_1 >> s) & m);
		ig_md.meta8_32.x32_0 = (ig_md.meta8_32.x32_0 & m);
		ig_md.meta8_32.x32_1 = ((ig_md.meta8_32.x32_1 >> s) & m);
	}

	action step_pop_32_8(bit<32> m, bit<8> s){
		ig_md.meta32_8.x1_0 = (ig_md.meta32_8.x1_0 & m);
		ig_md.meta32_8.x1_1 = ((ig_md.meta32_8.x1_1 >> s) & m);
		ig_md.meta32_8.x2_0 = (ig_md.meta32_8.x2_0 & m);
		ig_md.meta32_8.x2_1 = ((ig_md.meta32_8.x2_1 >> s) & m);
		ig_md.meta32_8.x3_0 = (ig_md.meta32_8.x3_0 & m);
		ig_md.meta32_8.x3_1 = ((ig_md.meta32_8.x3_1 >> s) & m);
		ig_md.meta32_8.x4_0 = (ig_md.meta32_8.x4_0 & m);
		ig_md.meta32_8.x4_1 = ((ig_md.meta32_8.x4_1 >> s) & m);
		ig_md.meta32_8.x5_0 = (ig_md.meta32_8.x5_0 & m);
		ig_md.meta32_8.x5_1 = ((ig_md.meta32_8.x5_1 >> s) & m);
		ig_md.meta32_8.x6_0 = (ig_md.meta32_8.x6_0 & m);
		ig_md.meta32_8.x6_1 = ((ig_md.meta32_8.x6_1 >> s) & m);
		ig_md.meta32_8.x7_0 = (ig_md.meta32_8.x7_0 & m);
		ig_md.meta32_8.x7_1 = ((ig_md.meta32_8.x7_1 >> s) & m);
		ig_md.meta32_8.x8_0 = (ig_md.meta32_8.x8_0 & m);
		ig_md.meta32_8.x8_1 = ((ig_md.meta32_8.x8_1 >> s) & m);
	}

	action sum_32_32(){
		ig_md.meta32_32.x1_0 = (ig_md.meta32_32.x1_0 + ig_md.meta32_32.x1_1);
		ig_md.meta32_32.x2_0 = (ig_md.meta32_32.x2_0 + ig_md.meta32_32.x2_1);
		ig_md.meta32_32.x3_0 = (ig_md.meta32_32.x3_0 + ig_md.meta32_32.x3_1);
		ig_md.meta32_32.x4_0 = (ig_md.meta32_32.x4_0 + ig_md.meta32_32.x4_1);
		ig_md.meta32_32.x5_0 = (ig_md.meta32_32.x5_0 + ig_md.meta32_32.x5_1);
		ig_md.meta32_32.x6_0 = (ig_md.meta32_32.x6_0 + ig_md.meta32_32.x6_1);
		ig_md.meta32_32.x7_0 = (ig_md.meta32_32.x7_0 + ig_md.meta32_32.x7_1);
		ig_md.meta32_32.x8_0 = (ig_md.meta32_32.x8_0 + ig_md.meta32_32.x8_1);
		ig_md.meta32_32.x9_0 = (ig_md.meta32_32.x9_0 + ig_md.meta32_32.x9_1);
		ig_md.meta32_32.x10_0 = (ig_md.meta32_32.x10_0 + ig_md.meta32_32.x10_1);
		ig_md.meta32_32.x11_0 = (ig_md.meta32_32.x11_0 + ig_md.meta32_32.x11_1);
		ig_md.meta32_32.x12_0 = (ig_md.meta32_32.x12_0 + ig_md.meta32_32.x12_1);
		ig_md.meta32_32.x13_0 = (ig_md.meta32_32.x13_0 + ig_md.meta32_32.x13_1);
		ig_md.meta32_32.x14_0 = (ig_md.meta32_32.x14_0 + ig_md.meta32_32.x14_1);
		ig_md.meta32_32.x15_0 = (ig_md.meta32_32.x15_0 + ig_md.meta32_32.x15_1);
		ig_md.meta32_32.x16_0 = (ig_md.meta32_32.x16_0 + ig_md.meta32_32.x16_1);
		ig_md.meta32_32.x17_0 = (ig_md.meta32_32.x17_0 + ig_md.meta32_32.x17_1);
		ig_md.meta32_32.x18_0 = (ig_md.meta32_32.x18_0 + ig_md.meta32_32.x18_1);
		ig_md.meta32_32.x19_0 = (ig_md.meta32_32.x19_0 + ig_md.meta32_32.x19_1);
		ig_md.meta32_32.x20_0 = (ig_md.meta32_32.x20_0 + ig_md.meta32_32.x20_1);
		ig_md.meta32_32.x21_0 = (ig_md.meta32_32.x21_0 + ig_md.meta32_32.x21_1);
		ig_md.meta32_32.x22_0 = (ig_md.meta32_32.x22_0 + ig_md.meta32_32.x22_1);
		ig_md.meta32_32.x23_0 = (ig_md.meta32_32.x23_0 + ig_md.meta32_32.x23_1);
		ig_md.meta32_32.x24_0 = (ig_md.meta32_32.x24_0 + ig_md.meta32_32.x24_1);
		ig_md.meta32_32.x25_0 = (ig_md.meta32_32.x25_0 + ig_md.meta32_32.x25_1);
		ig_md.meta32_32.x26_0 = (ig_md.meta32_32.x26_0 + ig_md.meta32_32.x26_1);
		ig_md.meta32_32.x27_0 = (ig_md.meta32_32.x27_0 + ig_md.meta32_32.x27_1);
		ig_md.meta32_32.x28_0 = (ig_md.meta32_32.x28_0 + ig_md.meta32_32.x28_1);
		ig_md.meta32_32.x29_0 = (ig_md.meta32_32.x29_0 + ig_md.meta32_32.x29_1);
		ig_md.meta32_32.x30_0 = (ig_md.meta32_32.x30_0 + ig_md.meta32_32.x30_1);
		ig_md.meta32_32.x31_0 = (ig_md.meta32_32.x31_0 + ig_md.meta32_32.x31_1);
		ig_md.meta32_32.x32_0 = (ig_md.meta32_32.x32_0 + ig_md.meta32_32.x32_1);
	}

	action sum_8_32(){
		ig_md.meta8_32.x1_0 = (ig_md.meta8_32.x1_0 + ig_md.meta8_32.x1_1);
		ig_md.meta8_32.x2_0 = (ig_md.meta8_32.x2_0 + ig_md.meta8_32.x2_1);
		ig_md.meta8_32.x3_0 = (ig_md.meta8_32.x3_0 + ig_md.meta8_32.x3_1);
		ig_md.meta8_32.x4_0 = (ig_md.meta8_32.x4_0 + ig_md.meta8_32.x4_1);
		ig_md.meta8_32.x5_0 = (ig_md.meta8_32.x5_0 + ig_md.meta8_32.x5_1);
		ig_md.meta8_32.x6_0 = (ig_md.meta8_32.x6_0 + ig_md.meta8_32.x6_1);
		ig_md.meta8_32.x7_0 = (ig_md.meta8_32.x7_0 + ig_md.meta8_32.x7_1);
		ig_md.meta8_32.x8_0 = (ig_md.meta8_32.x8_0 + ig_md.meta8_32.x8_1);
		ig_md.meta8_32.x9_0 = (ig_md.meta8_32.x9_0 + ig_md.meta8_32.x9_1);
		ig_md.meta8_32.x10_0 = (ig_md.meta8_32.x10_0 + ig_md.meta8_32.x10_1);
		ig_md.meta8_32.x11_0 = (ig_md.meta8_32.x11_0 + ig_md.meta8_32.x11_1);
		ig_md.meta8_32.x12_0 = (ig_md.meta8_32.x12_0 + ig_md.meta8_32.x12_1);
		ig_md.meta8_32.x13_0 = (ig_md.meta8_32.x13_0 + ig_md.meta8_32.x13_1);
		ig_md.meta8_32.x14_0 = (ig_md.meta8_32.x14_0 + ig_md.meta8_32.x14_1);
		ig_md.meta8_32.x15_0 = (ig_md.meta8_32.x15_0 + ig_md.meta8_32.x15_1);
		ig_md.meta8_32.x16_0 = (ig_md.meta8_32.x16_0 + ig_md.meta8_32.x16_1);
		ig_md.meta8_32.x17_0 = (ig_md.meta8_32.x17_0 + ig_md.meta8_32.x17_1);
		ig_md.meta8_32.x18_0 = (ig_md.meta8_32.x18_0 + ig_md.meta8_32.x18_1);
		ig_md.meta8_32.x19_0 = (ig_md.meta8_32.x19_0 + ig_md.meta8_32.x19_1);
		ig_md.meta8_32.x20_0 = (ig_md.meta8_32.x20_0 + ig_md.meta8_32.x20_1);
		ig_md.meta8_32.x21_0 = (ig_md.meta8_32.x21_0 + ig_md.meta8_32.x21_1);
		ig_md.meta8_32.x22_0 = (ig_md.meta8_32.x22_0 + ig_md.meta8_32.x22_1);
		ig_md.meta8_32.x23_0 = (ig_md.meta8_32.x23_0 + ig_md.meta8_32.x23_1);
		ig_md.meta8_32.x24_0 = (ig_md.meta8_32.x24_0 + ig_md.meta8_32.x24_1);
		ig_md.meta8_32.x25_0 = (ig_md.meta8_32.x25_0 + ig_md.meta8_32.x25_1);
		ig_md.meta8_32.x26_0 = (ig_md.meta8_32.x26_0 + ig_md.meta8_32.x26_1);
		ig_md.meta8_32.x27_0 = (ig_md.meta8_32.x27_0 + ig_md.meta8_32.x27_1);
		ig_md.meta8_32.x28_0 = (ig_md.meta8_32.x28_0 + ig_md.meta8_32.x28_1);
		ig_md.meta8_32.x29_0 = (ig_md.meta8_32.x29_0 + ig_md.meta8_32.x29_1);
		ig_md.meta8_32.x30_0 = (ig_md.meta8_32.x30_0 + ig_md.meta8_32.x30_1);
		ig_md.meta8_32.x31_0 = (ig_md.meta8_32.x31_0 + ig_md.meta8_32.x31_1);
		ig_md.meta8_32.x32_0 = (ig_md.meta8_32.x32_0 + ig_md.meta8_32.x32_1);
	}

	action sum_32_8(){
		ig_md.meta32_8.x1_0 = (ig_md.meta32_8.x1_0 + ig_md.meta32_8.x1_1);
		ig_md.meta32_8.x2_0 = (ig_md.meta32_8.x2_0 + ig_md.meta32_8.x2_1);
		ig_md.meta32_8.x3_0 = (ig_md.meta32_8.x3_0 + ig_md.meta32_8.x3_1);
		ig_md.meta32_8.x4_0 = (ig_md.meta32_8.x4_0 + ig_md.meta32_8.x4_1);
		ig_md.meta32_8.x5_0 = (ig_md.meta32_8.x5_0 + ig_md.meta32_8.x5_1);
		ig_md.meta32_8.x6_0 = (ig_md.meta32_8.x6_0 + ig_md.meta32_8.x6_1);
		ig_md.meta32_8.x7_0 = (ig_md.meta32_8.x7_0 + ig_md.meta32_8.x7_1);
		ig_md.meta32_8.x8_0 = (ig_md.meta32_8.x8_0 + ig_md.meta32_8.x8_1);
	}

	action sign_8_32(){
		if (ig_md.meta8_32.x1_0 >= 4) 
			ig_md.meta8_32.x1_0 = 0;
		else 
			ig_md.meta8_32.x1_0 = 1;
		if (ig_md.meta8_32.x2_0 >= 4) 
			ig_md.meta8_32.x2_0 = 0;
		else 
			ig_md.meta8_32.x2_0 = 1;
		if (ig_md.meta8_32.x3_0 >= 4) 
			ig_md.meta8_32.x3_0 = 0;
		else 
			ig_md.meta8_32.x3_0 = 1;
		if (ig_md.meta8_32.x4_0 >= 4) 
			ig_md.meta8_32.x4_0 = 0;
		else 
			ig_md.meta8_32.x4_0 = 1;
		if (ig_md.meta8_32.x5_0 >= 4) 
			ig_md.meta8_32.x5_0 = 0;
		else 
			ig_md.meta8_32.x5_0 = 1;
		if (ig_md.meta8_32.x6_0 >= 4) 
			ig_md.meta8_32.x6_0 = 0;
		else 
			ig_md.meta8_32.x6_0 = 1;
		if (ig_md.meta8_32.x7_0 >= 4) 
			ig_md.meta8_32.x7_0 = 0;
		else 
			ig_md.meta8_32.x7_0 = 1;
		if (ig_md.meta8_32.x8_0 >= 4) 
			ig_md.meta8_32.x8_0 = 0;
		else 
			ig_md.meta8_32.x8_0 = 1;
		if (ig_md.meta8_32.x9_0 >= 4) 
			ig_md.meta8_32.x9_0 = 0;
		else 
			ig_md.meta8_32.x9_0 = 1;
		if (ig_md.meta8_32.x10_0 >= 4) 
			ig_md.meta8_32.x10_0 = 0;
		else 
			ig_md.meta8_32.x10_0 = 1;
		if (ig_md.meta8_32.x11_0 >= 4) 
			ig_md.meta8_32.x11_0 = 0;
		else 
			ig_md.meta8_32.x11_0 = 1;
		if (ig_md.meta8_32.x12_0 >= 4) 
			ig_md.meta8_32.x12_0 = 0;
		else 
			ig_md.meta8_32.x12_0 = 1;
		if (ig_md.meta8_32.x13_0 >= 4) 
			ig_md.meta8_32.x13_0 = 0;
		else 
			ig_md.meta8_32.x13_0 = 1;
		if (ig_md.meta8_32.x14_0 >= 4) 
			ig_md.meta8_32.x14_0 = 0;
		else 
			ig_md.meta8_32.x14_0 = 1;
		if (ig_md.meta8_32.x15_0 >= 4) 
			ig_md.meta8_32.x15_0 = 0;
		else 
			ig_md.meta8_32.x15_0 = 1;
		if (ig_md.meta8_32.x16_0 >= 4) 
			ig_md.meta8_32.x16_0 = 0;
		else 
			ig_md.meta8_32.x16_0 = 1;
		if (ig_md.meta8_32.x17_0 >= 4) 
			ig_md.meta8_32.x17_0 = 0;
		else 
			ig_md.meta8_32.x17_0 = 1;
		if (ig_md.meta8_32.x18_0 >= 4) 
			ig_md.meta8_32.x18_0 = 0;
		else 
			ig_md.meta8_32.x18_0 = 1;
		if (ig_md.meta8_32.x19_0 >= 4) 
			ig_md.meta8_32.x19_0 = 0;
		else 
			ig_md.meta8_32.x19_0 = 1;
		if (ig_md.meta8_32.x20_0 >= 4) 
			ig_md.meta8_32.x20_0 = 0;
		else 
			ig_md.meta8_32.x20_0 = 1;
		if (ig_md.meta8_32.x21_0 >= 4) 
			ig_md.meta8_32.x21_0 = 0;
		else 
			ig_md.meta8_32.x21_0 = 1;
		if (ig_md.meta8_32.x22_0 >= 4) 
			ig_md.meta8_32.x22_0 = 0;
		else 
			ig_md.meta8_32.x22_0 = 1;
		if (ig_md.meta8_32.x23_0 >= 4) 
			ig_md.meta8_32.x23_0 = 0;
		else 
			ig_md.meta8_32.x23_0 = 1;
		if (ig_md.meta8_32.x24_0 >= 4) 
			ig_md.meta8_32.x24_0 = 0;
		else 
			ig_md.meta8_32.x24_0 = 1;
		if (ig_md.meta8_32.x25_0 >= 4) 
			ig_md.meta8_32.x25_0 = 0;
		else 
			ig_md.meta8_32.x25_0 = 1;
		if (ig_md.meta8_32.x26_0 >= 4) 
			ig_md.meta8_32.x26_0 = 0;
		else 
			ig_md.meta8_32.x26_0 = 1;
		if (ig_md.meta8_32.x27_0 >= 4) 
			ig_md.meta8_32.x27_0 = 0;
		else 
			ig_md.meta8_32.x27_0 = 1;
		if (ig_md.meta8_32.x28_0 >= 4) 
			ig_md.meta8_32.x28_0 = 0;
		else 
			ig_md.meta8_32.x28_0 = 1;
		if (ig_md.meta8_32.x29_0 >= 4) 
			ig_md.meta8_32.x29_0 = 0;
		else 
			ig_md.meta8_32.x29_0 = 1;
		if (ig_md.meta8_32.x30_0 >= 4) 
			ig_md.meta8_32.x30_0 = 0;
		else 
			ig_md.meta8_32.x30_0 = 1;
		if (ig_md.meta8_32.x31_0 >= 4) 
			ig_md.meta8_32.x31_0 = 0;
		else 
			ig_md.meta8_32.x31_0 = 1;
		if (ig_md.meta8_32.x32_0 >= 4) 
			ig_md.meta8_32.x32_0 = 0;
		else 
			ig_md.meta8_32.x32_0 = 1;
	}

	action sign_32_8(){
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
	}

	action cpy_8_32(){
		ig_md.meta8_32.x1_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x2_1 = ig_md.meta8_32.x2_0;
		ig_md.meta8_32.x3_1 = ig_md.meta8_32.x3_0;
		ig_md.meta8_32.x4_1 = ig_md.meta8_32.x4_0;
		ig_md.meta8_32.x5_1 = ig_md.meta8_32.x5_0;
		ig_md.meta8_32.x6_1 = ig_md.meta8_32.x6_0;
		ig_md.meta8_32.x7_1 = ig_md.meta8_32.x7_0;
		ig_md.meta8_32.x8_1 = ig_md.meta8_32.x8_0;
		ig_md.meta8_32.x9_1 = ig_md.meta8_32.x9_0;
		ig_md.meta8_32.x10_1 = ig_md.meta8_32.x10_0;
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

	action mcpy_32_32(){
		ig_md.meta32_32.x1_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x2_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x2_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x3_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x3_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x4_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x4_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x5_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x5_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x6_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x6_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x7_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x7_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x8_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x8_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x9_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x9_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x10_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x10_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x11_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x11_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x12_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x12_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x13_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x13_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x14_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x14_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x15_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x15_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x16_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x16_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x17_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x17_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x18_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x18_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x19_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x19_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x20_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x20_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x21_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x21_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x22_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x22_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x23_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x23_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x24_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x24_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x25_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x25_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x26_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x26_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x27_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x27_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x28_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x28_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x29_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x29_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x30_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x30_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x31_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x31_1 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x32_0 = ig_md.meta32_32.x1_0;
		ig_md.meta32_32.x32_1 = ig_md.meta32_32.x1_0;
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
		ig_md.meta8_32.x5_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x6_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x6_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x7_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x7_1 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x8_0 = ig_md.meta8_32.x1_0;
		ig_md.meta8_32.x8_1 = ig_md.meta8_32.x1_0;
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

	action l1_popcount(){
		cpy_32_8();
		step_pop_32_8(m1_32,1);
		sum_32_8();
		cpy_32_8();
		step_pop_32_8(m2_32,2);
		sum_32_8();
		cpy_32_8();
		step_pop_32_8(m4_32,4);
		sum_32_8();
		cpy_32_8();
		step_pop_32_8(m8_32,8);
		sum_32_8();
		cpy_32_8();
		step_pop_32_8(m16_32,16);
		sum_32_8();
		sign_32_8();
		l1_fold();
		mcpy_8_32();
	}

	action l2_fold(){
		ig_md.meta32_32.x1_0[31:31] = ig_md.meta8_32.x1_0[0:0];
		ig_md.meta32_32.x1_0[30:30] = ig_md.meta8_32.x2_0[0:0];
		ig_md.meta32_32.x1_0[29:29] = ig_md.meta8_32.x3_0[0:0];
		ig_md.meta32_32.x1_0[28:28] = ig_md.meta8_32.x4_0[0:0];
		ig_md.meta32_32.x1_0[27:27] = ig_md.meta8_32.x5_0[0:0];
		ig_md.meta32_32.x1_0[26:26] = ig_md.meta8_32.x6_0[0:0];
		ig_md.meta32_32.x1_0[25:25] = ig_md.meta8_32.x7_0[0:0];
		ig_md.meta32_32.x1_0[24:24] = ig_md.meta8_32.x8_0[0:0];
		ig_md.meta32_32.x1_0[23:23] = ig_md.meta8_32.x9_0[0:0];
		ig_md.meta32_32.x1_0[22:22] = ig_md.meta8_32.x10_0[0:0];
		ig_md.meta32_32.x1_0[21:21] = ig_md.meta8_32.x11_0[0:0];
		ig_md.meta32_32.x1_0[20:20] = ig_md.meta8_32.x12_0[0:0];
		ig_md.meta32_32.x1_0[19:19] = ig_md.meta8_32.x13_0[0:0];
		ig_md.meta32_32.x1_0[18:18] = ig_md.meta8_32.x14_0[0:0];
		ig_md.meta32_32.x1_0[17:17] = ig_md.meta8_32.x15_0[0:0];
		ig_md.meta32_32.x1_0[16:16] = ig_md.meta8_32.x16_0[0:0];
		ig_md.meta32_32.x1_0[15:15] = ig_md.meta8_32.x17_0[0:0];
		ig_md.meta32_32.x1_0[14:14] = ig_md.meta8_32.x18_0[0:0];
		ig_md.meta32_32.x1_0[13:13] = ig_md.meta8_32.x19_0[0:0];
		ig_md.meta32_32.x1_0[12:12] = ig_md.meta8_32.x20_0[0:0];
		ig_md.meta32_32.x1_0[11:11] = ig_md.meta8_32.x21_0[0:0];
		ig_md.meta32_32.x1_0[10:10] = ig_md.meta8_32.x22_0[0:0];
		ig_md.meta32_32.x1_0[9:9] = ig_md.meta8_32.x23_0[0:0];
		ig_md.meta32_32.x1_0[8:8] = ig_md.meta8_32.x24_0[0:0];
		ig_md.meta32_32.x1_0[7:7] = ig_md.meta8_32.x25_0[0:0];
		ig_md.meta32_32.x1_0[6:6] = ig_md.meta8_32.x26_0[0:0];
		ig_md.meta32_32.x1_0[5:5] = ig_md.meta8_32.x27_0[0:0];
		ig_md.meta32_32.x1_0[4:4] = ig_md.meta8_32.x28_0[0:0];
		ig_md.meta32_32.x1_0[3:3] = ig_md.meta8_32.x29_0[0:0];
		ig_md.meta32_32.x1_0[2:2] = ig_md.meta8_32.x30_0[0:0];
		ig_md.meta32_32.x1_0[1:1] = ig_md.meta8_32.x31_0[0:0];
		ig_md.meta32_32.x1_0[0:0] = ig_md.meta8_32.x32_0[0:0];
	}

	action l2_popcount(){
		cpy_8_32();
		step_pop_8_32(m1_8,1);
		sum_8_32();
		cpy_8_32();
		step_pop_8_32(m2_8,2);
		sum_8_32();
		cpy_8_32();
		step_pop_8_32(m4_8,4);
		sum_8_32();
		sign_8_32();
		l2_fold();
		mcpy_32_32();
	}



	/***** user actions *****/

	action get_nn_input(){
		//Here we can select the input features vector from packet header.
		ig_md.meta32_8.x1_0 = ig_hdr.ipv4.src_addr;

		//copy ig_md.meta32_8.x1_0 into ig_md.meta32_8.x**_0 and ig_md.meta32_8.x**_1
		mcpy_32_8();
	}



	action get_nn_output(){
		//Here we can select the destination packet header
		ig_hdr.ipv4.src_addr = ig_md.meta32_32.x1_0;
	}



	table l1_xor_table {
		actions = { xor_32_8; NoAction; } 
		default_action = NoAction();
	}

	table l1_popcount_table {
		actions = { l1_popcount; } 
		default_action = l1_popcount();
	}

	table l2_xor_table {
		actions = { xor_8_32; NoAction; } 
		default_action = NoAction();
	}

	table l2_popcount_table {
		actions = { l2_popcount; } 
		default_action = l2_popcount();
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


	table folding_table {

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
		const default_action = _drop();
		const entries = {
			MAC_SND : send_back();
		}

	}

	apply {
		replication_table.apply();

		l1_xor_table.apply();
		l1_popcount_table.apply();
		l2_xor_table.apply();
		l2_popcount_table.apply();


		folding_table.apply();
		send_back_table.apply();
	}

}

control IngressDeparser(
    packet_out pkt,
    inout headers_t ig_hdr,
    in metadata_t ig_md,
    in ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md)
{
    apply {
        // emit headers for out-of-ingress packets here
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