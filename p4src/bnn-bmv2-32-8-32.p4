/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

/*
 * Standard ethernet header
 */
header ethernet_t {
	bit<48> dstAddr;
	bit<48> srcAddr;
	bit<16> etherType;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}


const bit<48> MAC_SND       = 0x00000000000a;
const bit<16> BNN_PKT_ETYPE = 0x2323;

const bit<8> m1_8 = 0x55;
const bit<8> m2_8 = 0x33;
const bit<8> m4_8 = 0x0f;

const bit<32> m1_32 = 0x55555555;
const bit<32> m2_32 = 0x33333333;
const bit<32> m4_32 = 0x0f0f0f0f;
const bit<32> m8_32 = 0x00ff00ff;
const bit<32> m16_32 = 0x0000ffff;



/*
 * BNN packet
 */

header bnn_pkt_t {
	bit<32> x;
}


/*
 * All headers must be assembled in a signle struct, no need to be instanctiated
 */
struct my_headers_t {
	ethernet_t ethernet;
	ipv4_t ipv4;
	bnn_pkt_t bnn_pkt;
}

struct meta32_32_t {
	bit<32> x1_0;
	bit<32> x1_1;
	bit<32> x2_0;
	bit<32> x2_1;
	bit<32> x3_0;
	bit<32> x3_1;
	bit<32> x4_0;
	bit<32> x4_1;
	bit<32> x5_0;
	bit<32> x5_1;
	bit<32> x6_0;
	bit<32> x6_1;
	bit<32> x7_0;
	bit<32> x7_1;
	bit<32> x8_0;
	bit<32> x8_1;
	bit<32> x9_0;
	bit<32> x9_1;
	bit<32> x10_0;
	bit<32> x10_1;
	bit<32> x11_0;
	bit<32> x11_1;
	bit<32> x12_0;
	bit<32> x12_1;
	bit<32> x13_0;
	bit<32> x13_1;
	bit<32> x14_0;
	bit<32> x14_1;
	bit<32> x15_0;
	bit<32> x15_1;
	bit<32> x16_0;
	bit<32> x16_1;
	bit<32> x17_0;
	bit<32> x17_1;
	bit<32> x18_0;
	bit<32> x18_1;
	bit<32> x19_0;
	bit<32> x19_1;
	bit<32> x20_0;
	bit<32> x20_1;
	bit<32> x21_0;
	bit<32> x21_1;
	bit<32> x22_0;
	bit<32> x22_1;
	bit<32> x23_0;
	bit<32> x23_1;
	bit<32> x24_0;
	bit<32> x24_1;
	bit<32> x25_0;
	bit<32> x25_1;
	bit<32> x26_0;
	bit<32> x26_1;
	bit<32> x27_0;
	bit<32> x27_1;
	bit<32> x28_0;
	bit<32> x28_1;
	bit<32> x29_0;
	bit<32> x29_1;
	bit<32> x30_0;
	bit<32> x30_1;
	bit<32> x31_0;
	bit<32> x31_1;
	bit<32> x32_0;
	bit<32> x32_1;
}

struct meta8_32_t {
	bit<8> x1_0;
	bit<8> x1_1;
	bit<8> x2_0;
	bit<8> x2_1;
	bit<8> x3_0;
	bit<8> x3_1;
	bit<8> x4_0;
	bit<8> x4_1;
	bit<8> x5_0;
	bit<8> x5_1;
	bit<8> x6_0;
	bit<8> x6_1;
	bit<8> x7_0;
	bit<8> x7_1;
	bit<8> x8_0;
	bit<8> x8_1;
	bit<8> x9_0;
	bit<8> x9_1;
	bit<8> x10_0;
	bit<8> x10_1;
	bit<8> x11_0;
	bit<8> x11_1;
	bit<8> x12_0;
	bit<8> x12_1;
	bit<8> x13_0;
	bit<8> x13_1;
	bit<8> x14_0;
	bit<8> x14_1;
	bit<8> x15_0;
	bit<8> x15_1;
	bit<8> x16_0;
	bit<8> x16_1;
	bit<8> x17_0;
	bit<8> x17_1;
	bit<8> x18_0;
	bit<8> x18_1;
	bit<8> x19_0;
	bit<8> x19_1;
	bit<8> x20_0;
	bit<8> x20_1;
	bit<8> x21_0;
	bit<8> x21_1;
	bit<8> x22_0;
	bit<8> x22_1;
	bit<8> x23_0;
	bit<8> x23_1;
	bit<8> x24_0;
	bit<8> x24_1;
	bit<8> x25_0;
	bit<8> x25_1;
	bit<8> x26_0;
	bit<8> x26_1;
	bit<8> x27_0;
	bit<8> x27_1;
	bit<8> x28_0;
	bit<8> x28_1;
	bit<8> x29_0;
	bit<8> x29_1;
	bit<8> x30_0;
	bit<8> x30_1;
	bit<8> x31_0;
	bit<8> x31_1;
	bit<8> x32_0;
	bit<8> x32_1;
}

struct meta32_8_t {
	bit<32> x1_0;
	bit<32> x1_1;
	bit<32> x2_0;
	bit<32> x2_1;
	bit<32> x3_0;
	bit<32> x3_1;
	bit<32> x4_0;
	bit<32> x4_1;
	bit<32> x5_0;
	bit<32> x5_1;
	bit<32> x6_0;
	bit<32> x6_1;
	bit<32> x7_0;
	bit<32> x7_1;
	bit<32> x8_0;
	bit<32> x8_1;
}

struct metadata {
	meta32_32_t meta32_32;
	meta8_32_t meta8_32;
	meta32_8_t meta32_8;
}




/*************************************************************************
 ***********************  P A R S E R  ***********************************
 *************************************************************************/

parser MyParser(
	packet_in packet,
	out my_headers_t hdr,
	inout metadata meta,
	inout standard_metadata_t standard_metadata)
{
	state start {
		packet.extract(hdr.ethernet);
		transition select(hdr.ethernet.etherType) {
			0x800: parse_ipv4;
			BNN_PKT_ETYPE : bnn_found;
			default       : accept;
		}
	}

	state bnn_found {
		packet.extract(hdr.bnn_pkt);
		transition accept;
	}

	state parse_ipv4 {
        packet.extract(hdr.ipv4);
		transition accept;
	}
}

/*************************************************************************
 ************   C H E C K S U M    V E R I F I C A T I O N   *************
 *************************************************************************/

control MyVerifyChecksum(
	inout  my_headers_t   hdr,
	inout metadata meta)
{
	apply { }
}
/*************************************************************************
 **************  I N G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/

control MyIngress(
	inout my_headers_t     hdr,
	inout metadata meta,
	inout standard_metadata_t standard_metadata)
{
	action _drop() {
		mark_to_drop(standard_metadata);
	}

	action send_back() {
		bit<48> tmp;
		/* Swap the MAC addresses */
		tmp = hdr.ethernet.dstAddr;
		hdr.ethernet.dstAddr = hdr.ethernet.srcAddr;
		hdr.ethernet.srcAddr = tmp;
		bit<32> tmp2;

		/* Send the packet back to the port it came from */
		standard_metadata.egress_spec = standard_metadata.ingress_port;
	}

	action xor_32_32(bit<32> w_1, bit<32> w_2, bit<32> w_3, bit<32> w_4, bit<32> w_5, bit<32> w_6, bit<32> w_7, bit<32> w_8, bit<32> w_9, bit<32> w_10, bit<32> w_11, bit<32> w_12, bit<32> w_13, bit<32> w_14, bit<32> w_15, bit<32> w_16, bit<32> w_17, bit<32> w_18, bit<32> w_19, bit<32> w_20, bit<32> w_21, bit<32> w_22, bit<32> w_23, bit<32> w_24, bit<32> w_25, bit<32> w_26, bit<32> w_27, bit<32> w_28, bit<32> w_29, bit<32> w_30, bit<32> w_31, bit<32> w_32){
		meta.meta32_32.x1_0 = (meta.meta32_32.x1_0 ^ w_1);
		meta.meta32_32.x2_0 = (meta.meta32_32.x2_0 ^ w_2);
		meta.meta32_32.x3_0 = (meta.meta32_32.x3_0 ^ w_3);
		meta.meta32_32.x4_0 = (meta.meta32_32.x4_0 ^ w_4);
		meta.meta32_32.x5_0 = (meta.meta32_32.x5_0 ^ w_5);
		meta.meta32_32.x6_0 = (meta.meta32_32.x6_0 ^ w_6);
		meta.meta32_32.x7_0 = (meta.meta32_32.x7_0 ^ w_7);
		meta.meta32_32.x8_0 = (meta.meta32_32.x8_0 ^ w_8);
		meta.meta32_32.x9_0 = (meta.meta32_32.x9_0 ^ w_9);
		meta.meta32_32.x10_0 = (meta.meta32_32.x10_0 ^ w_10);
		meta.meta32_32.x11_0 = (meta.meta32_32.x11_0 ^ w_11);
		meta.meta32_32.x12_0 = (meta.meta32_32.x12_0 ^ w_12);
		meta.meta32_32.x13_0 = (meta.meta32_32.x13_0 ^ w_13);
		meta.meta32_32.x14_0 = (meta.meta32_32.x14_0 ^ w_14);
		meta.meta32_32.x15_0 = (meta.meta32_32.x15_0 ^ w_15);
		meta.meta32_32.x16_0 = (meta.meta32_32.x16_0 ^ w_16);
		meta.meta32_32.x17_0 = (meta.meta32_32.x17_0 ^ w_17);
		meta.meta32_32.x18_0 = (meta.meta32_32.x18_0 ^ w_18);
		meta.meta32_32.x19_0 = (meta.meta32_32.x19_0 ^ w_19);
		meta.meta32_32.x20_0 = (meta.meta32_32.x20_0 ^ w_20);
		meta.meta32_32.x21_0 = (meta.meta32_32.x21_0 ^ w_21);
		meta.meta32_32.x22_0 = (meta.meta32_32.x22_0 ^ w_22);
		meta.meta32_32.x23_0 = (meta.meta32_32.x23_0 ^ w_23);
		meta.meta32_32.x24_0 = (meta.meta32_32.x24_0 ^ w_24);
		meta.meta32_32.x25_0 = (meta.meta32_32.x25_0 ^ w_25);
		meta.meta32_32.x26_0 = (meta.meta32_32.x26_0 ^ w_26);
		meta.meta32_32.x27_0 = (meta.meta32_32.x27_0 ^ w_27);
		meta.meta32_32.x28_0 = (meta.meta32_32.x28_0 ^ w_28);
		meta.meta32_32.x29_0 = (meta.meta32_32.x29_0 ^ w_29);
		meta.meta32_32.x30_0 = (meta.meta32_32.x30_0 ^ w_30);
		meta.meta32_32.x31_0 = (meta.meta32_32.x31_0 ^ w_31);
		meta.meta32_32.x32_0 = (meta.meta32_32.x32_0 ^ w_32);
	}

	action xor_8_32(bit<8> w_1, bit<8> w_2, bit<8> w_3, bit<8> w_4, bit<8> w_5, bit<8> w_6, bit<8> w_7, bit<8> w_8, bit<8> w_9, bit<8> w_10, bit<8> w_11, bit<8> w_12, bit<8> w_13, bit<8> w_14, bit<8> w_15, bit<8> w_16, bit<8> w_17, bit<8> w_18, bit<8> w_19, bit<8> w_20, bit<8> w_21, bit<8> w_22, bit<8> w_23, bit<8> w_24, bit<8> w_25, bit<8> w_26, bit<8> w_27, bit<8> w_28, bit<8> w_29, bit<8> w_30, bit<8> w_31, bit<8> w_32){
		meta.meta8_32.x1_0 = (meta.meta8_32.x1_0 ^ w_1);
		meta.meta8_32.x2_0 = (meta.meta8_32.x2_0 ^ w_2);
		meta.meta8_32.x3_0 = (meta.meta8_32.x3_0 ^ w_3);
		meta.meta8_32.x4_0 = (meta.meta8_32.x4_0 ^ w_4);
		meta.meta8_32.x5_0 = (meta.meta8_32.x5_0 ^ w_5);
		meta.meta8_32.x6_0 = (meta.meta8_32.x6_0 ^ w_6);
		meta.meta8_32.x7_0 = (meta.meta8_32.x7_0 ^ w_7);
		meta.meta8_32.x8_0 = (meta.meta8_32.x8_0 ^ w_8);
		meta.meta8_32.x9_0 = (meta.meta8_32.x9_0 ^ w_9);
		meta.meta8_32.x10_0 = (meta.meta8_32.x10_0 ^ w_10);
		meta.meta8_32.x11_0 = (meta.meta8_32.x11_0 ^ w_11);
		meta.meta8_32.x12_0 = (meta.meta8_32.x12_0 ^ w_12);
		meta.meta8_32.x13_0 = (meta.meta8_32.x13_0 ^ w_13);
		meta.meta8_32.x14_0 = (meta.meta8_32.x14_0 ^ w_14);
		meta.meta8_32.x15_0 = (meta.meta8_32.x15_0 ^ w_15);
		meta.meta8_32.x16_0 = (meta.meta8_32.x16_0 ^ w_16);
		meta.meta8_32.x17_0 = (meta.meta8_32.x17_0 ^ w_17);
		meta.meta8_32.x18_0 = (meta.meta8_32.x18_0 ^ w_18);
		meta.meta8_32.x19_0 = (meta.meta8_32.x19_0 ^ w_19);
		meta.meta8_32.x20_0 = (meta.meta8_32.x20_0 ^ w_20);
		meta.meta8_32.x21_0 = (meta.meta8_32.x21_0 ^ w_21);
		meta.meta8_32.x22_0 = (meta.meta8_32.x22_0 ^ w_22);
		meta.meta8_32.x23_0 = (meta.meta8_32.x23_0 ^ w_23);
		meta.meta8_32.x24_0 = (meta.meta8_32.x24_0 ^ w_24);
		meta.meta8_32.x25_0 = (meta.meta8_32.x25_0 ^ w_25);
		meta.meta8_32.x26_0 = (meta.meta8_32.x26_0 ^ w_26);
		meta.meta8_32.x27_0 = (meta.meta8_32.x27_0 ^ w_27);
		meta.meta8_32.x28_0 = (meta.meta8_32.x28_0 ^ w_28);
		meta.meta8_32.x29_0 = (meta.meta8_32.x29_0 ^ w_29);
		meta.meta8_32.x30_0 = (meta.meta8_32.x30_0 ^ w_30);
		meta.meta8_32.x31_0 = (meta.meta8_32.x31_0 ^ w_31);
		meta.meta8_32.x32_0 = (meta.meta8_32.x32_0 ^ w_32);
	}

	action xor_32_8(bit<32> w_1, bit<32> w_2, bit<32> w_3, bit<32> w_4, bit<32> w_5, bit<32> w_6, bit<32> w_7, bit<32> w_8){
		meta.meta32_8.x1_0 = (meta.meta32_8.x1_0 ^ w_1);
		meta.meta32_8.x2_0 = (meta.meta32_8.x2_0 ^ w_2);
		meta.meta32_8.x3_0 = (meta.meta32_8.x3_0 ^ w_3);
		meta.meta32_8.x4_0 = (meta.meta32_8.x4_0 ^ w_4);
		meta.meta32_8.x5_0 = (meta.meta32_8.x5_0 ^ w_5);
		meta.meta32_8.x6_0 = (meta.meta32_8.x6_0 ^ w_6);
		meta.meta32_8.x7_0 = (meta.meta32_8.x7_0 ^ w_7);
		meta.meta32_8.x8_0 = (meta.meta32_8.x8_0 ^ w_8);
	}

	action step_pop_32_32(bit<32> m, bit<8> s){
		meta.meta32_32.x1_0 = (meta.meta32_32.x1_0 & m);
		meta.meta32_32.x1_1 = ((meta.meta32_32.x1_1 >> s) & m);
		meta.meta32_32.x2_0 = (meta.meta32_32.x2_0 & m);
		meta.meta32_32.x2_1 = ((meta.meta32_32.x2_1 >> s) & m);
		meta.meta32_32.x3_0 = (meta.meta32_32.x3_0 & m);
		meta.meta32_32.x3_1 = ((meta.meta32_32.x3_1 >> s) & m);
		meta.meta32_32.x4_0 = (meta.meta32_32.x4_0 & m);
		meta.meta32_32.x4_1 = ((meta.meta32_32.x4_1 >> s) & m);
		meta.meta32_32.x5_0 = (meta.meta32_32.x5_0 & m);
		meta.meta32_32.x5_1 = ((meta.meta32_32.x5_1 >> s) & m);
		meta.meta32_32.x6_0 = (meta.meta32_32.x6_0 & m);
		meta.meta32_32.x6_1 = ((meta.meta32_32.x6_1 >> s) & m);
		meta.meta32_32.x7_0 = (meta.meta32_32.x7_0 & m);
		meta.meta32_32.x7_1 = ((meta.meta32_32.x7_1 >> s) & m);
		meta.meta32_32.x8_0 = (meta.meta32_32.x8_0 & m);
		meta.meta32_32.x8_1 = ((meta.meta32_32.x8_1 >> s) & m);
		meta.meta32_32.x9_0 = (meta.meta32_32.x9_0 & m);
		meta.meta32_32.x9_1 = ((meta.meta32_32.x9_1 >> s) & m);
		meta.meta32_32.x10_0 = (meta.meta32_32.x10_0 & m);
		meta.meta32_32.x10_1 = ((meta.meta32_32.x10_1 >> s) & m);
		meta.meta32_32.x11_0 = (meta.meta32_32.x11_0 & m);
		meta.meta32_32.x11_1 = ((meta.meta32_32.x11_1 >> s) & m);
		meta.meta32_32.x12_0 = (meta.meta32_32.x12_0 & m);
		meta.meta32_32.x12_1 = ((meta.meta32_32.x12_1 >> s) & m);
		meta.meta32_32.x13_0 = (meta.meta32_32.x13_0 & m);
		meta.meta32_32.x13_1 = ((meta.meta32_32.x13_1 >> s) & m);
		meta.meta32_32.x14_0 = (meta.meta32_32.x14_0 & m);
		meta.meta32_32.x14_1 = ((meta.meta32_32.x14_1 >> s) & m);
		meta.meta32_32.x15_0 = (meta.meta32_32.x15_0 & m);
		meta.meta32_32.x15_1 = ((meta.meta32_32.x15_1 >> s) & m);
		meta.meta32_32.x16_0 = (meta.meta32_32.x16_0 & m);
		meta.meta32_32.x16_1 = ((meta.meta32_32.x16_1 >> s) & m);
		meta.meta32_32.x17_0 = (meta.meta32_32.x17_0 & m);
		meta.meta32_32.x17_1 = ((meta.meta32_32.x17_1 >> s) & m);
		meta.meta32_32.x18_0 = (meta.meta32_32.x18_0 & m);
		meta.meta32_32.x18_1 = ((meta.meta32_32.x18_1 >> s) & m);
		meta.meta32_32.x19_0 = (meta.meta32_32.x19_0 & m);
		meta.meta32_32.x19_1 = ((meta.meta32_32.x19_1 >> s) & m);
		meta.meta32_32.x20_0 = (meta.meta32_32.x20_0 & m);
		meta.meta32_32.x20_1 = ((meta.meta32_32.x20_1 >> s) & m);
		meta.meta32_32.x21_0 = (meta.meta32_32.x21_0 & m);
		meta.meta32_32.x21_1 = ((meta.meta32_32.x21_1 >> s) & m);
		meta.meta32_32.x22_0 = (meta.meta32_32.x22_0 & m);
		meta.meta32_32.x22_1 = ((meta.meta32_32.x22_1 >> s) & m);
		meta.meta32_32.x23_0 = (meta.meta32_32.x23_0 & m);
		meta.meta32_32.x23_1 = ((meta.meta32_32.x23_1 >> s) & m);
		meta.meta32_32.x24_0 = (meta.meta32_32.x24_0 & m);
		meta.meta32_32.x24_1 = ((meta.meta32_32.x24_1 >> s) & m);
		meta.meta32_32.x25_0 = (meta.meta32_32.x25_0 & m);
		meta.meta32_32.x25_1 = ((meta.meta32_32.x25_1 >> s) & m);
		meta.meta32_32.x26_0 = (meta.meta32_32.x26_0 & m);
		meta.meta32_32.x26_1 = ((meta.meta32_32.x26_1 >> s) & m);
		meta.meta32_32.x27_0 = (meta.meta32_32.x27_0 & m);
		meta.meta32_32.x27_1 = ((meta.meta32_32.x27_1 >> s) & m);
		meta.meta32_32.x28_0 = (meta.meta32_32.x28_0 & m);
		meta.meta32_32.x28_1 = ((meta.meta32_32.x28_1 >> s) & m);
		meta.meta32_32.x29_0 = (meta.meta32_32.x29_0 & m);
		meta.meta32_32.x29_1 = ((meta.meta32_32.x29_1 >> s) & m);
		meta.meta32_32.x30_0 = (meta.meta32_32.x30_0 & m);
		meta.meta32_32.x30_1 = ((meta.meta32_32.x30_1 >> s) & m);
		meta.meta32_32.x31_0 = (meta.meta32_32.x31_0 & m);
		meta.meta32_32.x31_1 = ((meta.meta32_32.x31_1 >> s) & m);
		meta.meta32_32.x32_0 = (meta.meta32_32.x32_0 & m);
		meta.meta32_32.x32_1 = ((meta.meta32_32.x32_1 >> s) & m);
	}

	action step_pop_8_32(bit<8> m, bit<8> s){
		meta.meta8_32.x1_0 = (meta.meta8_32.x1_0 & m);
		meta.meta8_32.x1_1 = ((meta.meta8_32.x1_1 >> s) & m);
		meta.meta8_32.x2_0 = (meta.meta8_32.x2_0 & m);
		meta.meta8_32.x2_1 = ((meta.meta8_32.x2_1 >> s) & m);
		meta.meta8_32.x3_0 = (meta.meta8_32.x3_0 & m);
		meta.meta8_32.x3_1 = ((meta.meta8_32.x3_1 >> s) & m);
		meta.meta8_32.x4_0 = (meta.meta8_32.x4_0 & m);
		meta.meta8_32.x4_1 = ((meta.meta8_32.x4_1 >> s) & m);
		meta.meta8_32.x5_0 = (meta.meta8_32.x5_0 & m);
		meta.meta8_32.x5_1 = ((meta.meta8_32.x5_1 >> s) & m);
		meta.meta8_32.x6_0 = (meta.meta8_32.x6_0 & m);
		meta.meta8_32.x6_1 = ((meta.meta8_32.x6_1 >> s) & m);
		meta.meta8_32.x7_0 = (meta.meta8_32.x7_0 & m);
		meta.meta8_32.x7_1 = ((meta.meta8_32.x7_1 >> s) & m);
		meta.meta8_32.x8_0 = (meta.meta8_32.x8_0 & m);
		meta.meta8_32.x8_1 = ((meta.meta8_32.x8_1 >> s) & m);
		meta.meta8_32.x9_0 = (meta.meta8_32.x9_0 & m);
		meta.meta8_32.x9_1 = ((meta.meta8_32.x9_1 >> s) & m);
		meta.meta8_32.x10_0 = (meta.meta8_32.x10_0 & m);
		meta.meta8_32.x10_1 = ((meta.meta8_32.x10_1 >> s) & m);
		meta.meta8_32.x11_0 = (meta.meta8_32.x11_0 & m);
		meta.meta8_32.x11_1 = ((meta.meta8_32.x11_1 >> s) & m);
		meta.meta8_32.x12_0 = (meta.meta8_32.x12_0 & m);
		meta.meta8_32.x12_1 = ((meta.meta8_32.x12_1 >> s) & m);
		meta.meta8_32.x13_0 = (meta.meta8_32.x13_0 & m);
		meta.meta8_32.x13_1 = ((meta.meta8_32.x13_1 >> s) & m);
		meta.meta8_32.x14_0 = (meta.meta8_32.x14_0 & m);
		meta.meta8_32.x14_1 = ((meta.meta8_32.x14_1 >> s) & m);
		meta.meta8_32.x15_0 = (meta.meta8_32.x15_0 & m);
		meta.meta8_32.x15_1 = ((meta.meta8_32.x15_1 >> s) & m);
		meta.meta8_32.x16_0 = (meta.meta8_32.x16_0 & m);
		meta.meta8_32.x16_1 = ((meta.meta8_32.x16_1 >> s) & m);
		meta.meta8_32.x17_0 = (meta.meta8_32.x17_0 & m);
		meta.meta8_32.x17_1 = ((meta.meta8_32.x17_1 >> s) & m);
		meta.meta8_32.x18_0 = (meta.meta8_32.x18_0 & m);
		meta.meta8_32.x18_1 = ((meta.meta8_32.x18_1 >> s) & m);
		meta.meta8_32.x19_0 = (meta.meta8_32.x19_0 & m);
		meta.meta8_32.x19_1 = ((meta.meta8_32.x19_1 >> s) & m);
		meta.meta8_32.x20_0 = (meta.meta8_32.x20_0 & m);
		meta.meta8_32.x20_1 = ((meta.meta8_32.x20_1 >> s) & m);
		meta.meta8_32.x21_0 = (meta.meta8_32.x21_0 & m);
		meta.meta8_32.x21_1 = ((meta.meta8_32.x21_1 >> s) & m);
		meta.meta8_32.x22_0 = (meta.meta8_32.x22_0 & m);
		meta.meta8_32.x22_1 = ((meta.meta8_32.x22_1 >> s) & m);
		meta.meta8_32.x23_0 = (meta.meta8_32.x23_0 & m);
		meta.meta8_32.x23_1 = ((meta.meta8_32.x23_1 >> s) & m);
		meta.meta8_32.x24_0 = (meta.meta8_32.x24_0 & m);
		meta.meta8_32.x24_1 = ((meta.meta8_32.x24_1 >> s) & m);
		meta.meta8_32.x25_0 = (meta.meta8_32.x25_0 & m);
		meta.meta8_32.x25_1 = ((meta.meta8_32.x25_1 >> s) & m);
		meta.meta8_32.x26_0 = (meta.meta8_32.x26_0 & m);
		meta.meta8_32.x26_1 = ((meta.meta8_32.x26_1 >> s) & m);
		meta.meta8_32.x27_0 = (meta.meta8_32.x27_0 & m);
		meta.meta8_32.x27_1 = ((meta.meta8_32.x27_1 >> s) & m);
		meta.meta8_32.x28_0 = (meta.meta8_32.x28_0 & m);
		meta.meta8_32.x28_1 = ((meta.meta8_32.x28_1 >> s) & m);
		meta.meta8_32.x29_0 = (meta.meta8_32.x29_0 & m);
		meta.meta8_32.x29_1 = ((meta.meta8_32.x29_1 >> s) & m);
		meta.meta8_32.x30_0 = (meta.meta8_32.x30_0 & m);
		meta.meta8_32.x30_1 = ((meta.meta8_32.x30_1 >> s) & m);
		meta.meta8_32.x31_0 = (meta.meta8_32.x31_0 & m);
		meta.meta8_32.x31_1 = ((meta.meta8_32.x31_1 >> s) & m);
		meta.meta8_32.x32_0 = (meta.meta8_32.x32_0 & m);
		meta.meta8_32.x32_1 = ((meta.meta8_32.x32_1 >> s) & m);
	}

	action step_pop_32_8(bit<32> m, bit<8> s){
		meta.meta32_8.x1_0 = (meta.meta32_8.x1_0 & m);
		meta.meta32_8.x1_1 = ((meta.meta32_8.x1_1 >> s) & m);
		meta.meta32_8.x2_0 = (meta.meta32_8.x2_0 & m);
		meta.meta32_8.x2_1 = ((meta.meta32_8.x2_1 >> s) & m);
		meta.meta32_8.x3_0 = (meta.meta32_8.x3_0 & m);
		meta.meta32_8.x3_1 = ((meta.meta32_8.x3_1 >> s) & m);
		meta.meta32_8.x4_0 = (meta.meta32_8.x4_0 & m);
		meta.meta32_8.x4_1 = ((meta.meta32_8.x4_1 >> s) & m);
		meta.meta32_8.x5_0 = (meta.meta32_8.x5_0 & m);
		meta.meta32_8.x5_1 = ((meta.meta32_8.x5_1 >> s) & m);
		meta.meta32_8.x6_0 = (meta.meta32_8.x6_0 & m);
		meta.meta32_8.x6_1 = ((meta.meta32_8.x6_1 >> s) & m);
		meta.meta32_8.x7_0 = (meta.meta32_8.x7_0 & m);
		meta.meta32_8.x7_1 = ((meta.meta32_8.x7_1 >> s) & m);
		meta.meta32_8.x8_0 = (meta.meta32_8.x8_0 & m);
		meta.meta32_8.x8_1 = ((meta.meta32_8.x8_1 >> s) & m);
	}

	action sum_32_32(){
		meta.meta32_32.x1_0 = (meta.meta32_32.x1_0 + meta.meta32_32.x1_1);
		meta.meta32_32.x2_0 = (meta.meta32_32.x2_0 + meta.meta32_32.x2_1);
		meta.meta32_32.x3_0 = (meta.meta32_32.x3_0 + meta.meta32_32.x3_1);
		meta.meta32_32.x4_0 = (meta.meta32_32.x4_0 + meta.meta32_32.x4_1);
		meta.meta32_32.x5_0 = (meta.meta32_32.x5_0 + meta.meta32_32.x5_1);
		meta.meta32_32.x6_0 = (meta.meta32_32.x6_0 + meta.meta32_32.x6_1);
		meta.meta32_32.x7_0 = (meta.meta32_32.x7_0 + meta.meta32_32.x7_1);
		meta.meta32_32.x8_0 = (meta.meta32_32.x8_0 + meta.meta32_32.x8_1);
		meta.meta32_32.x9_0 = (meta.meta32_32.x9_0 + meta.meta32_32.x9_1);
		meta.meta32_32.x10_0 = (meta.meta32_32.x10_0 + meta.meta32_32.x10_1);
		meta.meta32_32.x11_0 = (meta.meta32_32.x11_0 + meta.meta32_32.x11_1);
		meta.meta32_32.x12_0 = (meta.meta32_32.x12_0 + meta.meta32_32.x12_1);
		meta.meta32_32.x13_0 = (meta.meta32_32.x13_0 + meta.meta32_32.x13_1);
		meta.meta32_32.x14_0 = (meta.meta32_32.x14_0 + meta.meta32_32.x14_1);
		meta.meta32_32.x15_0 = (meta.meta32_32.x15_0 + meta.meta32_32.x15_1);
		meta.meta32_32.x16_0 = (meta.meta32_32.x16_0 + meta.meta32_32.x16_1);
		meta.meta32_32.x17_0 = (meta.meta32_32.x17_0 + meta.meta32_32.x17_1);
		meta.meta32_32.x18_0 = (meta.meta32_32.x18_0 + meta.meta32_32.x18_1);
		meta.meta32_32.x19_0 = (meta.meta32_32.x19_0 + meta.meta32_32.x19_1);
		meta.meta32_32.x20_0 = (meta.meta32_32.x20_0 + meta.meta32_32.x20_1);
		meta.meta32_32.x21_0 = (meta.meta32_32.x21_0 + meta.meta32_32.x21_1);
		meta.meta32_32.x22_0 = (meta.meta32_32.x22_0 + meta.meta32_32.x22_1);
		meta.meta32_32.x23_0 = (meta.meta32_32.x23_0 + meta.meta32_32.x23_1);
		meta.meta32_32.x24_0 = (meta.meta32_32.x24_0 + meta.meta32_32.x24_1);
		meta.meta32_32.x25_0 = (meta.meta32_32.x25_0 + meta.meta32_32.x25_1);
		meta.meta32_32.x26_0 = (meta.meta32_32.x26_0 + meta.meta32_32.x26_1);
		meta.meta32_32.x27_0 = (meta.meta32_32.x27_0 + meta.meta32_32.x27_1);
		meta.meta32_32.x28_0 = (meta.meta32_32.x28_0 + meta.meta32_32.x28_1);
		meta.meta32_32.x29_0 = (meta.meta32_32.x29_0 + meta.meta32_32.x29_1);
		meta.meta32_32.x30_0 = (meta.meta32_32.x30_0 + meta.meta32_32.x30_1);
		meta.meta32_32.x31_0 = (meta.meta32_32.x31_0 + meta.meta32_32.x31_1);
		meta.meta32_32.x32_0 = (meta.meta32_32.x32_0 + meta.meta32_32.x32_1);
	}

	action sum_8_32(){
		meta.meta8_32.x1_0 = (meta.meta8_32.x1_0 + meta.meta8_32.x1_1);
		meta.meta8_32.x2_0 = (meta.meta8_32.x2_0 + meta.meta8_32.x2_1);
		meta.meta8_32.x3_0 = (meta.meta8_32.x3_0 + meta.meta8_32.x3_1);
		meta.meta8_32.x4_0 = (meta.meta8_32.x4_0 + meta.meta8_32.x4_1);
		meta.meta8_32.x5_0 = (meta.meta8_32.x5_0 + meta.meta8_32.x5_1);
		meta.meta8_32.x6_0 = (meta.meta8_32.x6_0 + meta.meta8_32.x6_1);
		meta.meta8_32.x7_0 = (meta.meta8_32.x7_0 + meta.meta8_32.x7_1);
		meta.meta8_32.x8_0 = (meta.meta8_32.x8_0 + meta.meta8_32.x8_1);
		meta.meta8_32.x9_0 = (meta.meta8_32.x9_0 + meta.meta8_32.x9_1);
		meta.meta8_32.x10_0 = (meta.meta8_32.x10_0 + meta.meta8_32.x10_1);
		meta.meta8_32.x11_0 = (meta.meta8_32.x11_0 + meta.meta8_32.x11_1);
		meta.meta8_32.x12_0 = (meta.meta8_32.x12_0 + meta.meta8_32.x12_1);
		meta.meta8_32.x13_0 = (meta.meta8_32.x13_0 + meta.meta8_32.x13_1);
		meta.meta8_32.x14_0 = (meta.meta8_32.x14_0 + meta.meta8_32.x14_1);
		meta.meta8_32.x15_0 = (meta.meta8_32.x15_0 + meta.meta8_32.x15_1);
		meta.meta8_32.x16_0 = (meta.meta8_32.x16_0 + meta.meta8_32.x16_1);
		meta.meta8_32.x17_0 = (meta.meta8_32.x17_0 + meta.meta8_32.x17_1);
		meta.meta8_32.x18_0 = (meta.meta8_32.x18_0 + meta.meta8_32.x18_1);
		meta.meta8_32.x19_0 = (meta.meta8_32.x19_0 + meta.meta8_32.x19_1);
		meta.meta8_32.x20_0 = (meta.meta8_32.x20_0 + meta.meta8_32.x20_1);
		meta.meta8_32.x21_0 = (meta.meta8_32.x21_0 + meta.meta8_32.x21_1);
		meta.meta8_32.x22_0 = (meta.meta8_32.x22_0 + meta.meta8_32.x22_1);
		meta.meta8_32.x23_0 = (meta.meta8_32.x23_0 + meta.meta8_32.x23_1);
		meta.meta8_32.x24_0 = (meta.meta8_32.x24_0 + meta.meta8_32.x24_1);
		meta.meta8_32.x25_0 = (meta.meta8_32.x25_0 + meta.meta8_32.x25_1);
		meta.meta8_32.x26_0 = (meta.meta8_32.x26_0 + meta.meta8_32.x26_1);
		meta.meta8_32.x27_0 = (meta.meta8_32.x27_0 + meta.meta8_32.x27_1);
		meta.meta8_32.x28_0 = (meta.meta8_32.x28_0 + meta.meta8_32.x28_1);
		meta.meta8_32.x29_0 = (meta.meta8_32.x29_0 + meta.meta8_32.x29_1);
		meta.meta8_32.x30_0 = (meta.meta8_32.x30_0 + meta.meta8_32.x30_1);
		meta.meta8_32.x31_0 = (meta.meta8_32.x31_0 + meta.meta8_32.x31_1);
		meta.meta8_32.x32_0 = (meta.meta8_32.x32_0 + meta.meta8_32.x32_1);
	}

	action sum_32_8(){
		meta.meta32_8.x1_0 = (meta.meta32_8.x1_0 + meta.meta32_8.x1_1);
		meta.meta32_8.x2_0 = (meta.meta32_8.x2_0 + meta.meta32_8.x2_1);
		meta.meta32_8.x3_0 = (meta.meta32_8.x3_0 + meta.meta32_8.x3_1);
		meta.meta32_8.x4_0 = (meta.meta32_8.x4_0 + meta.meta32_8.x4_1);
		meta.meta32_8.x5_0 = (meta.meta32_8.x5_0 + meta.meta32_8.x5_1);
		meta.meta32_8.x6_0 = (meta.meta32_8.x6_0 + meta.meta32_8.x6_1);
		meta.meta32_8.x7_0 = (meta.meta32_8.x7_0 + meta.meta32_8.x7_1);
		meta.meta32_8.x8_0 = (meta.meta32_8.x8_0 + meta.meta32_8.x8_1);
	}

	action sign_32_32(){
		if (meta.meta32_32.x1_0 >= 16) 
			meta.meta32_32.x1_0 = 0;
		else 
			meta.meta32_32.x1_0 = 1;
		if (meta.meta32_32.x2_0 >= 16) 
			meta.meta32_32.x2_0 = 0;
		else 
			meta.meta32_32.x2_0 = 1;
		if (meta.meta32_32.x3_0 >= 16) 
			meta.meta32_32.x3_0 = 0;
		else 
			meta.meta32_32.x3_0 = 1;
		if (meta.meta32_32.x4_0 >= 16) 
			meta.meta32_32.x4_0 = 0;
		else 
			meta.meta32_32.x4_0 = 1;
		if (meta.meta32_32.x5_0 >= 16) 
			meta.meta32_32.x5_0 = 0;
		else 
			meta.meta32_32.x5_0 = 1;
		if (meta.meta32_32.x6_0 >= 16) 
			meta.meta32_32.x6_0 = 0;
		else 
			meta.meta32_32.x6_0 = 1;
		if (meta.meta32_32.x7_0 >= 16) 
			meta.meta32_32.x7_0 = 0;
		else 
			meta.meta32_32.x7_0 = 1;
		if (meta.meta32_32.x8_0 >= 16) 
			meta.meta32_32.x8_0 = 0;
		else 
			meta.meta32_32.x8_0 = 1;
		if (meta.meta32_32.x9_0 >= 16) 
			meta.meta32_32.x9_0 = 0;
		else 
			meta.meta32_32.x9_0 = 1;
		if (meta.meta32_32.x10_0 >= 16) 
			meta.meta32_32.x10_0 = 0;
		else 
			meta.meta32_32.x10_0 = 1;
		if (meta.meta32_32.x11_0 >= 16) 
			meta.meta32_32.x11_0 = 0;
		else 
			meta.meta32_32.x11_0 = 1;
		if (meta.meta32_32.x12_0 >= 16) 
			meta.meta32_32.x12_0 = 0;
		else 
			meta.meta32_32.x12_0 = 1;
		if (meta.meta32_32.x13_0 >= 16) 
			meta.meta32_32.x13_0 = 0;
		else 
			meta.meta32_32.x13_0 = 1;
		if (meta.meta32_32.x14_0 >= 16) 
			meta.meta32_32.x14_0 = 0;
		else 
			meta.meta32_32.x14_0 = 1;
		if (meta.meta32_32.x15_0 >= 16) 
			meta.meta32_32.x15_0 = 0;
		else 
			meta.meta32_32.x15_0 = 1;
		if (meta.meta32_32.x16_0 >= 16) 
			meta.meta32_32.x16_0 = 0;
		else 
			meta.meta32_32.x16_0 = 1;
		if (meta.meta32_32.x17_0 >= 16) 
			meta.meta32_32.x17_0 = 0;
		else 
			meta.meta32_32.x17_0 = 1;
		if (meta.meta32_32.x18_0 >= 16) 
			meta.meta32_32.x18_0 = 0;
		else 
			meta.meta32_32.x18_0 = 1;
		if (meta.meta32_32.x19_0 >= 16) 
			meta.meta32_32.x19_0 = 0;
		else 
			meta.meta32_32.x19_0 = 1;
		if (meta.meta32_32.x20_0 >= 16) 
			meta.meta32_32.x20_0 = 0;
		else 
			meta.meta32_32.x20_0 = 1;
		if (meta.meta32_32.x21_0 >= 16) 
			meta.meta32_32.x21_0 = 0;
		else 
			meta.meta32_32.x21_0 = 1;
		if (meta.meta32_32.x22_0 >= 16) 
			meta.meta32_32.x22_0 = 0;
		else 
			meta.meta32_32.x22_0 = 1;
		if (meta.meta32_32.x23_0 >= 16) 
			meta.meta32_32.x23_0 = 0;
		else 
			meta.meta32_32.x23_0 = 1;
		if (meta.meta32_32.x24_0 >= 16) 
			meta.meta32_32.x24_0 = 0;
		else 
			meta.meta32_32.x24_0 = 1;
		if (meta.meta32_32.x25_0 >= 16) 
			meta.meta32_32.x25_0 = 0;
		else 
			meta.meta32_32.x25_0 = 1;
		if (meta.meta32_32.x26_0 >= 16) 
			meta.meta32_32.x26_0 = 0;
		else 
			meta.meta32_32.x26_0 = 1;
		if (meta.meta32_32.x27_0 >= 16) 
			meta.meta32_32.x27_0 = 0;
		else 
			meta.meta32_32.x27_0 = 1;
		if (meta.meta32_32.x28_0 >= 16) 
			meta.meta32_32.x28_0 = 0;
		else 
			meta.meta32_32.x28_0 = 1;
		if (meta.meta32_32.x29_0 >= 16) 
			meta.meta32_32.x29_0 = 0;
		else 
			meta.meta32_32.x29_0 = 1;
		if (meta.meta32_32.x30_0 >= 16) 
			meta.meta32_32.x30_0 = 0;
		else 
			meta.meta32_32.x30_0 = 1;
		if (meta.meta32_32.x31_0 >= 16) 
			meta.meta32_32.x31_0 = 0;
		else 
			meta.meta32_32.x31_0 = 1;
		if (meta.meta32_32.x32_0 >= 16) 
			meta.meta32_32.x32_0 = 0;
		else 
			meta.meta32_32.x32_0 = 1;
	}

	action sign_8_32(){
		if (meta.meta8_32.x1_0 >= 4) 
			meta.meta8_32.x1_0 = 0;
		else 
			meta.meta8_32.x1_0 = 1;
		if (meta.meta8_32.x2_0 >= 4) 
			meta.meta8_32.x2_0 = 0;
		else 
			meta.meta8_32.x2_0 = 1;
		if (meta.meta8_32.x3_0 >= 4) 
			meta.meta8_32.x3_0 = 0;
		else 
			meta.meta8_32.x3_0 = 1;
		if (meta.meta8_32.x4_0 >= 4) 
			meta.meta8_32.x4_0 = 0;
		else 
			meta.meta8_32.x4_0 = 1;
		if (meta.meta8_32.x5_0 >= 4) 
			meta.meta8_32.x5_0 = 0;
		else 
			meta.meta8_32.x5_0 = 1;
		if (meta.meta8_32.x6_0 >= 4) 
			meta.meta8_32.x6_0 = 0;
		else 
			meta.meta8_32.x6_0 = 1;
		if (meta.meta8_32.x7_0 >= 4) 
			meta.meta8_32.x7_0 = 0;
		else 
			meta.meta8_32.x7_0 = 1;
		if (meta.meta8_32.x8_0 >= 4) 
			meta.meta8_32.x8_0 = 0;
		else 
			meta.meta8_32.x8_0 = 1;
		if (meta.meta8_32.x9_0 >= 4) 
			meta.meta8_32.x9_0 = 0;
		else 
			meta.meta8_32.x9_0 = 1;
		if (meta.meta8_32.x10_0 >= 4) 
			meta.meta8_32.x10_0 = 0;
		else 
			meta.meta8_32.x10_0 = 1;
		if (meta.meta8_32.x11_0 >= 4) 
			meta.meta8_32.x11_0 = 0;
		else 
			meta.meta8_32.x11_0 = 1;
		if (meta.meta8_32.x12_0 >= 4) 
			meta.meta8_32.x12_0 = 0;
		else 
			meta.meta8_32.x12_0 = 1;
		if (meta.meta8_32.x13_0 >= 4) 
			meta.meta8_32.x13_0 = 0;
		else 
			meta.meta8_32.x13_0 = 1;
		if (meta.meta8_32.x14_0 >= 4) 
			meta.meta8_32.x14_0 = 0;
		else 
			meta.meta8_32.x14_0 = 1;
		if (meta.meta8_32.x15_0 >= 4) 
			meta.meta8_32.x15_0 = 0;
		else 
			meta.meta8_32.x15_0 = 1;
		if (meta.meta8_32.x16_0 >= 4) 
			meta.meta8_32.x16_0 = 0;
		else 
			meta.meta8_32.x16_0 = 1;
		if (meta.meta8_32.x17_0 >= 4) 
			meta.meta8_32.x17_0 = 0;
		else 
			meta.meta8_32.x17_0 = 1;
		if (meta.meta8_32.x18_0 >= 4) 
			meta.meta8_32.x18_0 = 0;
		else 
			meta.meta8_32.x18_0 = 1;
		if (meta.meta8_32.x19_0 >= 4) 
			meta.meta8_32.x19_0 = 0;
		else 
			meta.meta8_32.x19_0 = 1;
		if (meta.meta8_32.x20_0 >= 4) 
			meta.meta8_32.x20_0 = 0;
		else 
			meta.meta8_32.x20_0 = 1;
		if (meta.meta8_32.x21_0 >= 4) 
			meta.meta8_32.x21_0 = 0;
		else 
			meta.meta8_32.x21_0 = 1;
		if (meta.meta8_32.x22_0 >= 4) 
			meta.meta8_32.x22_0 = 0;
		else 
			meta.meta8_32.x22_0 = 1;
		if (meta.meta8_32.x23_0 >= 4) 
			meta.meta8_32.x23_0 = 0;
		else 
			meta.meta8_32.x23_0 = 1;
		if (meta.meta8_32.x24_0 >= 4) 
			meta.meta8_32.x24_0 = 0;
		else 
			meta.meta8_32.x24_0 = 1;
		if (meta.meta8_32.x25_0 >= 4) 
			meta.meta8_32.x25_0 = 0;
		else 
			meta.meta8_32.x25_0 = 1;
		if (meta.meta8_32.x26_0 >= 4) 
			meta.meta8_32.x26_0 = 0;
		else 
			meta.meta8_32.x26_0 = 1;
		if (meta.meta8_32.x27_0 >= 4) 
			meta.meta8_32.x27_0 = 0;
		else 
			meta.meta8_32.x27_0 = 1;
		if (meta.meta8_32.x28_0 >= 4) 
			meta.meta8_32.x28_0 = 0;
		else 
			meta.meta8_32.x28_0 = 1;
		if (meta.meta8_32.x29_0 >= 4) 
			meta.meta8_32.x29_0 = 0;
		else 
			meta.meta8_32.x29_0 = 1;
		if (meta.meta8_32.x30_0 >= 4) 
			meta.meta8_32.x30_0 = 0;
		else 
			meta.meta8_32.x30_0 = 1;
		if (meta.meta8_32.x31_0 >= 4) 
			meta.meta8_32.x31_0 = 0;
		else 
			meta.meta8_32.x31_0 = 1;
		if (meta.meta8_32.x32_0 >= 4) 
			meta.meta8_32.x32_0 = 0;
		else 
			meta.meta8_32.x32_0 = 1;
	}

	action sign_32_8(){
		if (meta.meta32_8.x1_0 >= 16) 
			meta.meta32_8.x1_0 = 0;
		else 
			meta.meta32_8.x1_0 = 1;
		if (meta.meta32_8.x2_0 >= 16) 
			meta.meta32_8.x2_0 = 0;
		else 
			meta.meta32_8.x2_0 = 1;
		if (meta.meta32_8.x3_0 >= 16) 
			meta.meta32_8.x3_0 = 0;
		else 
			meta.meta32_8.x3_0 = 1;
		if (meta.meta32_8.x4_0 >= 16) 
			meta.meta32_8.x4_0 = 0;
		else 
			meta.meta32_8.x4_0 = 1;
		if (meta.meta32_8.x5_0 >= 16) 
			meta.meta32_8.x5_0 = 0;
		else 
			meta.meta32_8.x5_0 = 1;
		if (meta.meta32_8.x6_0 >= 16) 
			meta.meta32_8.x6_0 = 0;
		else 
			meta.meta32_8.x6_0 = 1;
		if (meta.meta32_8.x7_0 >= 16) 
			meta.meta32_8.x7_0 = 0;
		else 
			meta.meta32_8.x7_0 = 1;
		if (meta.meta32_8.x8_0 >= 16) 
			meta.meta32_8.x8_0 = 0;
		else 
			meta.meta32_8.x8_0 = 1;
	}

	action cpy_32_32(){
		meta.meta32_32.x1_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x2_1 = meta.meta32_32.x2_0;
		meta.meta32_32.x3_1 = meta.meta32_32.x3_0;
		meta.meta32_32.x4_1 = meta.meta32_32.x4_0;
		meta.meta32_32.x5_1 = meta.meta32_32.x5_0;
		meta.meta32_32.x6_1 = meta.meta32_32.x6_0;
		meta.meta32_32.x7_1 = meta.meta32_32.x7_0;
		meta.meta32_32.x8_1 = meta.meta32_32.x8_0;
		meta.meta32_32.x9_1 = meta.meta32_32.x9_0;
		meta.meta32_32.x10_1 = meta.meta32_32.x10_0;
		meta.meta32_32.x11_1 = meta.meta32_32.x11_0;
		meta.meta32_32.x12_1 = meta.meta32_32.x12_0;
		meta.meta32_32.x13_1 = meta.meta32_32.x13_0;
		meta.meta32_32.x14_1 = meta.meta32_32.x14_0;
		meta.meta32_32.x15_1 = meta.meta32_32.x15_0;
		meta.meta32_32.x16_1 = meta.meta32_32.x16_0;
		meta.meta32_32.x17_1 = meta.meta32_32.x17_0;
		meta.meta32_32.x18_1 = meta.meta32_32.x18_0;
		meta.meta32_32.x19_1 = meta.meta32_32.x19_0;
		meta.meta32_32.x20_1 = meta.meta32_32.x20_0;
		meta.meta32_32.x21_1 = meta.meta32_32.x21_0;
		meta.meta32_32.x22_1 = meta.meta32_32.x22_0;
		meta.meta32_32.x23_1 = meta.meta32_32.x23_0;
		meta.meta32_32.x24_1 = meta.meta32_32.x24_0;
		meta.meta32_32.x25_1 = meta.meta32_32.x25_0;
		meta.meta32_32.x26_1 = meta.meta32_32.x26_0;
		meta.meta32_32.x27_1 = meta.meta32_32.x27_0;
		meta.meta32_32.x28_1 = meta.meta32_32.x28_0;
		meta.meta32_32.x29_1 = meta.meta32_32.x29_0;
		meta.meta32_32.x30_1 = meta.meta32_32.x30_0;
		meta.meta32_32.x31_1 = meta.meta32_32.x31_0;
		meta.meta32_32.x32_1 = meta.meta32_32.x32_0;
	}

	action cpy_8_32(){
		meta.meta8_32.x1_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x2_1 = meta.meta8_32.x2_0;
		meta.meta8_32.x3_1 = meta.meta8_32.x3_0;
		meta.meta8_32.x4_1 = meta.meta8_32.x4_0;
		meta.meta8_32.x5_1 = meta.meta8_32.x5_0;
		meta.meta8_32.x6_1 = meta.meta8_32.x6_0;
		meta.meta8_32.x7_1 = meta.meta8_32.x7_0;
		meta.meta8_32.x8_1 = meta.meta8_32.x8_0;
		meta.meta8_32.x9_1 = meta.meta8_32.x9_0;
		meta.meta8_32.x10_1 = meta.meta8_32.x10_0;
		meta.meta8_32.x11_1 = meta.meta8_32.x11_0;
		meta.meta8_32.x12_1 = meta.meta8_32.x12_0;
		meta.meta8_32.x13_1 = meta.meta8_32.x13_0;
		meta.meta8_32.x14_1 = meta.meta8_32.x14_0;
		meta.meta8_32.x15_1 = meta.meta8_32.x15_0;
		meta.meta8_32.x16_1 = meta.meta8_32.x16_0;
		meta.meta8_32.x17_1 = meta.meta8_32.x17_0;
		meta.meta8_32.x18_1 = meta.meta8_32.x18_0;
		meta.meta8_32.x19_1 = meta.meta8_32.x19_0;
		meta.meta8_32.x20_1 = meta.meta8_32.x20_0;
		meta.meta8_32.x21_1 = meta.meta8_32.x21_0;
		meta.meta8_32.x22_1 = meta.meta8_32.x22_0;
		meta.meta8_32.x23_1 = meta.meta8_32.x23_0;
		meta.meta8_32.x24_1 = meta.meta8_32.x24_0;
		meta.meta8_32.x25_1 = meta.meta8_32.x25_0;
		meta.meta8_32.x26_1 = meta.meta8_32.x26_0;
		meta.meta8_32.x27_1 = meta.meta8_32.x27_0;
		meta.meta8_32.x28_1 = meta.meta8_32.x28_0;
		meta.meta8_32.x29_1 = meta.meta8_32.x29_0;
		meta.meta8_32.x30_1 = meta.meta8_32.x30_0;
		meta.meta8_32.x31_1 = meta.meta8_32.x31_0;
		meta.meta8_32.x32_1 = meta.meta8_32.x32_0;
	}

	action cpy_32_8(){
		meta.meta32_8.x1_1 = meta.meta32_8.x1_0;
		meta.meta32_8.x2_1 = meta.meta32_8.x2_0;
		meta.meta32_8.x3_1 = meta.meta32_8.x3_0;
		meta.meta32_8.x4_1 = meta.meta32_8.x4_0;
		meta.meta32_8.x5_1 = meta.meta32_8.x5_0;
		meta.meta32_8.x6_1 = meta.meta32_8.x6_0;
		meta.meta32_8.x7_1 = meta.meta32_8.x7_0;
		meta.meta32_8.x8_1 = meta.meta32_8.x8_0;
	}

	action mcpy_32_32(){
		meta.meta32_32.x1_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x2_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x2_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x3_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x3_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x4_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x4_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x5_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x5_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x6_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x6_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x7_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x7_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x8_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x8_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x9_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x9_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x10_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x10_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x11_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x11_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x12_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x12_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x13_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x13_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x14_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x14_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x15_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x15_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x16_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x16_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x17_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x17_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x18_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x18_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x19_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x19_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x20_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x20_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x21_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x21_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x22_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x22_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x23_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x23_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x24_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x24_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x25_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x25_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x26_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x26_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x27_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x27_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x28_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x28_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x29_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x29_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x30_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x30_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x31_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x31_1 = meta.meta32_32.x1_0;
		meta.meta32_32.x32_0 = meta.meta32_32.x1_0;
		meta.meta32_32.x32_1 = meta.meta32_32.x1_0;
	}

	action mcpy_8_32(){
		meta.meta8_32.x1_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x2_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x2_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x3_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x3_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x4_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x4_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x5_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x5_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x6_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x6_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x7_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x7_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x8_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x8_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x9_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x9_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x10_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x10_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x11_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x11_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x12_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x12_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x13_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x13_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x14_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x14_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x15_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x15_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x16_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x16_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x17_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x17_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x18_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x18_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x19_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x19_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x20_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x20_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x21_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x21_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x22_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x22_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x23_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x23_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x24_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x24_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x25_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x25_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x26_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x26_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x27_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x27_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x28_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x28_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x29_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x29_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x30_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x30_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x31_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x31_1 = meta.meta8_32.x1_0;
		meta.meta8_32.x32_0 = meta.meta8_32.x1_0;
		meta.meta8_32.x32_1 = meta.meta8_32.x1_0;
	}

	action mcpy_32_8(){
		meta.meta32_8.x1_1 = meta.meta32_8.x1_0;
		meta.meta32_8.x2_0 = meta.meta32_8.x1_0;
		meta.meta32_8.x2_1 = meta.meta32_8.x1_0;
		meta.meta32_8.x3_0 = meta.meta32_8.x1_0;
		meta.meta32_8.x3_1 = meta.meta32_8.x1_0;
		meta.meta32_8.x4_0 = meta.meta32_8.x1_0;
		meta.meta32_8.x4_1 = meta.meta32_8.x1_0;
		meta.meta32_8.x5_0 = meta.meta32_8.x1_0;
		meta.meta32_8.x5_1 = meta.meta32_8.x1_0;
		meta.meta32_8.x6_0 = meta.meta32_8.x1_0;
		meta.meta32_8.x6_1 = meta.meta32_8.x1_0;
		meta.meta32_8.x7_0 = meta.meta32_8.x1_0;
		meta.meta32_8.x7_1 = meta.meta32_8.x1_0;
		meta.meta32_8.x8_0 = meta.meta32_8.x1_0;
		meta.meta32_8.x8_1 = meta.meta32_8.x1_0;
	}

	action l1_fold(){
		meta.meta8_32.x1_0[7:7] = meta.meta32_8.x1_0[0:0];
		meta.meta8_32.x1_0[6:6] = meta.meta32_8.x2_0[0:0];
		meta.meta8_32.x1_0[5:5] = meta.meta32_8.x3_0[0:0];
		meta.meta8_32.x1_0[4:4] = meta.meta32_8.x4_0[0:0];
		meta.meta8_32.x1_0[3:3] = meta.meta32_8.x5_0[0:0];
		meta.meta8_32.x1_0[2:2] = meta.meta32_8.x6_0[0:0];
		meta.meta8_32.x1_0[1:1] = meta.meta32_8.x7_0[0:0];
		meta.meta8_32.x1_0[0:0] = meta.meta32_8.x8_0[0:0];
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
		meta.meta32_32.x1_0[31:31] = meta.meta8_32.x1_0[0:0];
		meta.meta32_32.x1_0[30:30] = meta.meta8_32.x2_0[0:0];
		meta.meta32_32.x1_0[29:29] = meta.meta8_32.x3_0[0:0];
		meta.meta32_32.x1_0[28:28] = meta.meta8_32.x4_0[0:0];
		meta.meta32_32.x1_0[27:27] = meta.meta8_32.x5_0[0:0];
		meta.meta32_32.x1_0[26:26] = meta.meta8_32.x6_0[0:0];
		meta.meta32_32.x1_0[25:25] = meta.meta8_32.x7_0[0:0];
		meta.meta32_32.x1_0[24:24] = meta.meta8_32.x8_0[0:0];
		meta.meta32_32.x1_0[23:23] = meta.meta8_32.x9_0[0:0];
		meta.meta32_32.x1_0[22:22] = meta.meta8_32.x10_0[0:0];
		meta.meta32_32.x1_0[21:21] = meta.meta8_32.x11_0[0:0];
		meta.meta32_32.x1_0[20:20] = meta.meta8_32.x12_0[0:0];
		meta.meta32_32.x1_0[19:19] = meta.meta8_32.x13_0[0:0];
		meta.meta32_32.x1_0[18:18] = meta.meta8_32.x14_0[0:0];
		meta.meta32_32.x1_0[17:17] = meta.meta8_32.x15_0[0:0];
		meta.meta32_32.x1_0[16:16] = meta.meta8_32.x16_0[0:0];
		meta.meta32_32.x1_0[15:15] = meta.meta8_32.x17_0[0:0];
		meta.meta32_32.x1_0[14:14] = meta.meta8_32.x18_0[0:0];
		meta.meta32_32.x1_0[13:13] = meta.meta8_32.x19_0[0:0];
		meta.meta32_32.x1_0[12:12] = meta.meta8_32.x20_0[0:0];
		meta.meta32_32.x1_0[11:11] = meta.meta8_32.x21_0[0:0];
		meta.meta32_32.x1_0[10:10] = meta.meta8_32.x22_0[0:0];
		meta.meta32_32.x1_0[9:9] = meta.meta8_32.x23_0[0:0];
		meta.meta32_32.x1_0[8:8] = meta.meta8_32.x24_0[0:0];
		meta.meta32_32.x1_0[7:7] = meta.meta8_32.x25_0[0:0];
		meta.meta32_32.x1_0[6:6] = meta.meta8_32.x26_0[0:0];
		meta.meta32_32.x1_0[5:5] = meta.meta8_32.x27_0[0:0];
		meta.meta32_32.x1_0[4:4] = meta.meta8_32.x28_0[0:0];
		meta.meta32_32.x1_0[3:3] = meta.meta8_32.x29_0[0:0];
		meta.meta32_32.x1_0[2:2] = meta.meta8_32.x30_0[0:0];
		meta.meta32_32.x1_0[1:1] = meta.meta8_32.x31_0[0:0];
		meta.meta32_32.x1_0[0:0] = meta.meta8_32.x32_0[0:0];
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
		meta.meta32_8.x1_0 = hdr.ipv4.srcAddr;

		//copy meta.meta32_8.x1_0 into meta.meta32_8.x**_0 and meta.meta32_8.x**_1
		mcpy_32_8();
	}



	action get_nn_output(){
		//Here we can select the destination packet header
		hdr.ipv4.srcAddr = meta.meta32_32.x1_0;
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
			hdr.ethernet.srcAddr: exact;
		}
		actions = {
			get_nn_input;
		}
		const default_action = get_nn_input();
	}


	table folding_table {

		key = {
			hdr.ethernet.srcAddr: exact;
		}
		actions = {
			get_nn_output;
		}
		const default_action = get_nn_output();
	}


	table send_back_table {

		key = {
			hdr.ethernet.srcAddr: exact;
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
/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/

control MyEgress(
	inout my_headers_t        hdr,
	inout metadata meta,
	inout standard_metadata_t standard_metadata)
{
	apply {   }
}

/*************************************************************************
 *************   C H E C K S U M    C O M P U T A T I O N   **************
 *************************************************************************/
control MyComputeChecksum(
	inout my_headers_t  hdr,
	inout metadata meta)
{
	apply {   }
}

/*************************************************************************
 ***********************  D E P A R S E R  *******************************
 *************************************************************************/
control MyDeparser(
	packet_out      packet,
	in my_headers_t hdr)
{
	apply {
		packet.emit(hdr.ethernet);
		packet.emit(hdr.bnn_pkt);
	}
}



V1Switch(
	MyParser(),
	MyVerifyChecksum(),
	MyIngress(),
	MyEgress(),
	MyComputeChecksum(),
	MyDeparser()
) main;
