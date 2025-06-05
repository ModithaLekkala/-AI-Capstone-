/*******************************************************************************
 *  Copyright (C) 2024 Intel Corporation
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing,
 *  software distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions
 *  and limitations under the License.
 *
 *
 *  SPDX-License-Identifier: Apache-2.0
 ******************************************************************************/

typedef bit<48> mac_addr_t;
typedef bit<32> ipv4_addr_t;
typedef bit<16> ether_type_t;
typedef bit<16> bnnpk_type_t;
typedef bit<8>  popcount_t;
typedef bit<16> bnn_input_t;


const ether_type_t ETHERTYPE_IPV4 = 0x0800;
const bnnpk_type_t BNN_PKT_ETYPE = 0x2323;
const PortId_t POP_RECIRC_PORT = 68;
const PortId_t LAYER_RECIRC_PORT = 71;


const bit<48> MAC_SND       = 0x00000000000a;

const bit<8> m1_8 = 0x55;
const bit<8> m2_8 = 0x33;
const bit<8> m4_8 = 0x0f;

const bit<32> m1_32 = 0x55555555;
const bit<32> m2_32 = 0x33333333;
const bit<32> m4_32 = 0x0f0f0f0f;
const bit<32> m8_32 = 0x00ff00ff;
const bit<32> m16_32 = 0x0000ffff;

struct empty_header_t {}
struct empty_metadata_t {}

header ethernet_h {
    mac_addr_t dst_addr;
    mac_addr_t src_addr;
    bit<16> ether_type;
}

header ipv4_h {
    bit<4> version;
    bit<4> ihl;
    bit<8> diffserv;
    bit<16> total_len;
    bit<16> identification;
    bit<3> flags;
    bit<13> frag_offset;
    bit<8> ttl;
    bit<8> protocol;
    bit<16> hdr_checksum;
    ipv4_addr_t src_addr;
    ipv4_addr_t dst_addr;
}

header bnn_pkt_h {
	bit<16> x;
}

header l1_t {
	bit<128> nr_inpt1;
	bit<128> nr_inpt2;
	bit<128> nr_inpt3;
	bit<128> nr_inpt4;
	bit<128> nr_inpt5;
	bit<128> nr_inpt6;
	bit<128> nr_inpt7;
	bit<128> nr_inpt8;
}

header recirc_h {
    bit<16> original_port;
    bit<8> pop_recirc;
    bit<8> nrs_recirc;
    
    popcount_t pop1;
    popcount_t pop2;
    popcount_t pop3;
    popcount_t pop4;
    popcount_t pop5;
    popcount_t pop6;
    popcount_t pop7;
    popcount_t pop8;
}

struct headers_t {
	ethernet_h ethernet;
	// ipv4_h ipv4;
	bnn_pkt_h bnn_pkt;
	l1_t bnn_l1;
    recirc_h recirc;
}

struct bnn_reg_input_t {
    bit<16> input;
    bit<4>  pop; 
}

struct metadata_t {
    bit<16> nr1;
    bit<16> nr2;
    bit<16> nr3;
    bit<16> nr4;
    bit<16> nr5;
    bit<16> nr6;
    bit<16> nr7;
    bit<16> nr8;
    bit<16> nr1_w;
    bit<16> nr2_w;
    bit<16> nr3_w;
    bit<16> nr4_w;
    bit<16> nr5_w;
    bit<16> nr6_w;
    bit<16> nr7_w;
    bit<16> nr8_w;
}
