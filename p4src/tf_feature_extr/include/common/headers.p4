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
typedef bit<32> timestamp;

#define TCP_PACKET hdr.tcp.isValid()

/*-------------MIRROR DEFINITION --------------*/ 
typedef bit<8>  pkt_type_t;
const pkt_type_t PKT_TYPE_NORMAL = 1;
const pkt_type_t PKT_TYPE_MIRROR = 2;

typedef bit<3> mirror_type_t;
const mirror_type_t MIRROR_TYPE_I2E = 1;
const mirror_type_t MIRROR_TYPE_E2E = 2;

header mirror_bridged_metadata_h {
    pkt_type_t pkt_type;
    bit<8> flow_pkts;
    @flexible bit<1> do_egr_mirroring;  //  Enable egress mirroring
    @flexible MirrorId_t egr_mir_ses;   // Egress mirror session ID
}

header mirror_h {
    pkt_type_t  pkt_type;
    
}
/*------------------------------------------*/ 

header bnn_input_h {
    bit<8> sttl;
    bit<8> dttl;
    bit<16> sbytes;
    bit<16> dbytes;
    bit<16> smaxbytes;
    bit<16> dmaxbytes;
    bit<16> sminbytes;
    bit<16> dminbytes;
    bit<4> syn_cnt;
    bit<4> fin_cnt;
    bit<4> ece_cnt;
    bit<4> psh_cnt;
    bit<4> rst_cnt;
    bit<4> ack_cnt;
    bit<16> smean;
    bit<16> dmean;
    bit<16> spkts;
    bit<16> dpkts;
    // bit<8> synack;
    // bit<8> ackdat;
}

struct metadata_t {
    bit<16> flow_index;
    bit<16> reverse_flow_index;
    bit<8> tcp_type;
    bit<8> proto;
    bit<8> flow_dir;
    ipv4_addr_t dummy;
    bit<8> flow_pkts;
    bit<16> frame_len;

    bit<1> do_ing_mirroring;  // Enable ingress mirroring
    bit<1> do_egr_mirroring;  // Enable egress mirroring
    MirrorId_t ing_mir_ses;   // Ingress mirror session ID
    MirrorId_t egr_mir_ses;   // Egress mirror session ID
    pkt_type_t pkt_type;

    bit<1> syn_flag;
    bit<1> ece_flag;
    bit<1> psh_flag;
    bit<1> rst_flag;
    bit<1> ack_flag;
    bit<1> fin_flag;
}

struct collector_headers_t {
    mirror_h mirrored_md;
    mirror_bridged_metadata_h bridged_md;
	ethernet_h ethernet;
    ipv4_h ipv4;
    tcp_h tcp;
    udp_h udp;
    bnn_input_h bnn;
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