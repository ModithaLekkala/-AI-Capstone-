#include "../common/global.p4"
#define PROCESS_COUNTERS(flag)\
    hdr.bnn.##flag##_cnt=update_flows_##flag##.execute(meta.flow_index);

#define CHECK_FLAG(flg)\
    if(meta.##flg##_flag==1) {\
        flow_##flg##+=1;\
    }\
    rv = (bit<4>)flow_##flg##;

control PacketType(inout collector_headers_t hdr, inout metadata_t meta) {
    Register<bit<16>, bit<8>>(FLOWS_NO) flows_syn;
    Register<bit<16>, bit<8>>(FLOWS_NO) flows_fin;
    Register<bit<16>, bit<8>>(FLOWS_NO) flows_ece;
    Register<bit<16>, bit<8>>(FLOWS_NO) flows_ack;
    Register<bit<16>, bit<8>>(FLOWS_NO) flows_psh;
    Register<bit<16>, bit<8>>(FLOWS_NO) flows_rst;

    RegisterAction<_, bit<16>, bit<4>>(flows_syn) update_flows_syn = {
        void apply(inout bit<8> flow_syn, out bit<4> rv) {
            CHECK_FLAG(syn)
        }
    };

    RegisterAction<_, bit<16>, bit<4>>(flows_fin) update_flows_fin = {
        void apply(inout bit<8> flow_fin, out bit<4> rv) {
            CHECK_FLAG(fin)
        }
    };
       
    RegisterAction<_, bit<16>, bit<4>>(flows_ece) update_flows_ece = {
        void apply(inout bit<8> flow_ece, out bit<4> rv) {
            CHECK_FLAG(ece)
        }
    };

    RegisterAction<_, bit<16>, bit<4>>(flows_ack) update_flows_ack = {
        void apply(inout bit<8> flow_ack, out bit<4> rv) {
            CHECK_FLAG(ack)
        }
    };

    RegisterAction<_, bit<16>, bit<4>>(flows_psh) update_flows_psh = {
        void apply(inout bit<8> flow_psh, out bit<4> rv) {
            CHECK_FLAG(psh)
        }
    };

    RegisterAction<_, bit<16>, bit<4>>(flows_rst) update_flows_rst = {
        void apply(inout bit<8> flow_rst, out bit<4> rv) {
            CHECK_FLAG(rst)
        }
    };
    action nop() {
    }
    action mark_SYN(){
        meta.syn_flag=1;
    } 
    action mark_SYN_FIN(){  
        meta.fin_flag=1;
        meta.syn_flag=1;
    } 
    action mark_SYN_ECE(){  
        meta.syn_flag=1;
        meta.ece_flag=1;
    } 
    action mark_SYNACK_ECE(){  
        meta.syn_flag=1;
        meta.ack_flag=1;
        meta.ece_flag=1;
    }

    action mark_SYN_PSH(){  
        meta.syn_flag=1;
        meta.psh_flag=1;
    }
    action mark_ACK(){ 
        meta.ack_flag=1;
    } 
    action mark_ACK_FIN(){ 
        meta.ack_flag=1;
        meta.fin_flag=1;
    } 
    action mark_ACK_ECE(){ 
        meta.ack_flag=1;
        meta.ece_flag=1;
    }    
    action mark_SYNACK(){   
        meta.syn_flag=1;
        meta.ack_flag=1;
    } 
    action mark_SYNACK_PSH(){  
        meta.syn_flag=1;
        meta.ack_flag=1;
        meta.psh_flag=1;
    } 
    action mark_SYNACK_FIN(){   
        meta.syn_flag=1;
        meta.ack_flag=1;
        meta.fin_flag=1;
    }
    action mark_FIN() {
        meta.fin_flag=1;
    }
    action mark_RST() {
        meta.rst_flag=1;
    }
    table tb_decide_packet_type {
        key = {
            hdr.tcp.flags: ternary;
            hdr.ipv4.total_len: range;
        }
        actions = {
            nop;
            mark_SYN;
            mark_SYN_FIN;
            mark_SYN_ECE;
            mark_SYNACK_ECE;
            mark_SYN_PSH;
            mark_ACK;
            mark_ACK_FIN;
            mark_ACK_ECE;
            mark_SYNACK;
            mark_SYNACK_PSH;
            mark_SYNACK_FIN;
            mark_FIN;
            mark_RST;
        }
        default_action = nop();
        size = 32;
        const entries = {
            // SYN only
            (TCP_FLAGS_S, _): mark_SYN();

            // SYN with ECN
            (TCP_FLAGS_S + TCP_FLAGS_E, _): mark_SYN_ECE(); // SYN with ECE
            (TCP_FLAGS_S + TCP_FLAGS_C, _): mark_SYN(); // SYN with CWR
            (TCP_FLAGS_S + TCP_FLAGS_E + TCP_FLAGS_C, _): mark_SYN_ECE(); // SYN with ECE and CWR

            // SYN-ACK
            (TCP_FLAGS_S + TCP_FLAGS_A, _): mark_SYNACK(); // SYN-ACK
            (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_E, _): mark_SYNACK_ECE(); // SYN-ACK with ECE
            (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_C, _): mark_SYNACK(); // SYN-ACK with CWR
            (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_E + TCP_FLAGS_C, _): mark_SYNACK_ECE(); // SYN-ACK with ECE and CWR

            // ACK only
            (TCP_FLAGS_A, 0..80): mark_ACK(); // ACK without SYN

            // ACK with ECN
            (TCP_FLAGS_A + TCP_FLAGS_E, 0..80): mark_ACK_ECE(); // ACK with ECE
            (TCP_FLAGS_A + TCP_FLAGS_C, 0..80): mark_ACK(); // ACK with CWR
            (TCP_FLAGS_A + TCP_FLAGS_E + TCP_FLAGS_C, 0..80): mark_ACK(); // ACK with ECE and CWR

            // Extended Cases
            (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_U, _): mark_SYNACK(); // SYN+ACK+URG
            (TCP_FLAGS_A + TCP_FLAGS_U, 0..80): mark_ACK(); // ACK+URG
            (TCP_FLAGS_S + TCP_FLAGS_F, _): mark_SYN_FIN(); // SYN+FIN
            (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_F, _): mark_SYNACK_FIN(); // SYN+ACK+FIN

            // Additional Edge Cases
            (TCP_FLAGS_S + TCP_FLAGS_P, _): mark_SYN_PSH(); // SYN with PSH
            (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_P, _): mark_SYNACK_PSH(); // SYN+ACK with PSH
            (TCP_FLAGS_A + TCP_FLAGS_F, 0..80): mark_ACK_FIN(); // ACK with FIN

            // General cases
            (_, 80..1600): nop(); // General sequence packets
            (TCP_FLAGS_R, _): mark_RST(); // Reset flag
            (TCP_FLAGS_F, _): mark_FIN(); // Fin flag
            (TCP_FLAGS_F + TCP_FLAGS_A, _): mark_FIN(); // Fin flag
        }
    }

    apply {
        tb_decide_packet_type.apply();

        PROCESS_COUNTERS(syn)
        PROCESS_COUNTERS(ack)
        PROCESS_COUNTERS(rst)
        PROCESS_COUNTERS(psh)
        PROCESS_COUNTERS(ece)
        PROCESS_COUNTERS(fin)
    }
}