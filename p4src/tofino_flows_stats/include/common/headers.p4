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
typedef bit<32> timestamp;


#define TCP_PACKET hdr.tcp.isValid()

const ether_type_t ETHERTYPE_IPV4 = 0x0800;

struct empty_header_t {}
struct empty_metadata_t {}

struct metadata_t {
    bit<16> flow_index;
    bit<16> reverse_flow_index;
    bit<8> tcp_type;
    bit<8> proto;
}

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

header tcp_h{
    bit<16> src_port;
    bit<16> dst_port;
    bit<32> seq_no;
    bit<32> ack_no;
    bit<4> data_offset;
    bit<4> res;
    bit<8> flags;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgent_ptr;
}

header udp_h{
    bit<16> src_port;
    bit<16> dst_port;
    bit<16> len;
    bit<16> checksum;
}

header bnn_input_h {
    bit<8> sttl;
    bit<8> dttl;
    bit<16> sbytes;
    bit<16> dbytes;
    bit<16> smean;
    bit<16> dmean;
    bit<16> spkts;
    bit<16> dpkts;
    bit<8> synack;
    bit<8> ackdat;
}

header partial_bnn_h {
    bit<8> sttl;
    bit<16> sbytes;
    bit<16> smean;
    bit<16> spkts;
}

struct headers_t {
	ethernet_h ethernet;
    ipv4_h ipv4;
    tcp_h tcp;
    udp_h udp;
    bnn_input_h bnn;
    partial_bnn_h partial_bnn;
}

typedef bit<8> tcp_flags_t;
const tcp_flags_t TCP_FLAGS_F = 1;
const tcp_flags_t TCP_FLAGS_S = 2;
const tcp_flags_t TCP_FLAGS_R = 4;
const tcp_flags_t TCP_FLAGS_P = 8;
const tcp_flags_t TCP_FLAGS_A = 16;
const tcp_flags_t TCP_FLAGS_U = 32; // URG flag
const tcp_flags_t TCP_FLAGS_E = 64; // ECE flag
const tcp_flags_t TCP_FLAGS_C = 128; // CWR flag