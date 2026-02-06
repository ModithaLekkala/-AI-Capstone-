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

typedef bit<8>  popcount_t;
typedef bit<16> bnn_input_t;

const PortId_t POP_RECIRC_PORT = 192;
const PortId_t LAYER_RECIRC_PORT = 193;
const PortId_t CPU_PORT = 65;

header bnn_pkt {
    bit<8> layer_no;
    // bit<8> instead of bit<7> for optimization purposes
    bit<8> l0_out_1;
    bit<8> l0_out_2;
    bit<8> l0_out_3;
    bit<8> l0_out_4;
    bit<8> l0_out_5;
    bit<8> l0_out_6;
    bit<8> l1_out;

    bit<8> l0_popcount;
    bit<8> is_pred_confident;

    bit<16> input_offset;
    bit<16> input_offset_cp;

    bit<8> pop_recirc;
    bit<8> nrs_recirc;
    
    popcount_t pop1;
    popcount_t pop2;
    popcount_t pop3;
    popcount_t pop4;
    popcount_t pop5;
    popcount_t pop6;
    popcount_t pop7;
}

struct bnn_headers_t {
	ethernet_h ethernet;
    bnn_pkt bnn_pkt;
}