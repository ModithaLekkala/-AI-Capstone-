#include "../common/global.p4"

control PacketType(inout headers_t hdr, inout metadata_t meta) {
   
    action nop() {
    }
    action mark_SYN(){  
        meta.tcp_type=PKT_TYPE_SYN;  
    } 
    action mark_SEQ(){  
        meta.tcp_type=PKT_TYPE_SEQ;  
    } 
    action mark_ACK(){ 
        meta.tcp_type=PKT_TYPE_ACK; 
    } 
    action mark_SYNACK(){   
        meta.tcp_type=PKT_TYPE_SYNACK; 
    } 
    action drop_and_exit(){ 
        exit;
    } 
    action mark_FIN_RST() {
        meta.tcp_type=PKT_TYPE_FIN_RST; 
    }
    table tb_decide_packet_type {
        key = {
            hdr.tcp.flags: ternary;
            hdr.ipv4.total_len: range;
        }
        actions = {
            mark_SEQ;
            mark_SYN;
            mark_SYNACK;
            mark_ACK;
            mark_FIN_RST;
            drop_and_exit;
            nop;
        }
        default_action = nop();
        size = 32;
        const entries = {
            // SYN only
            (TCP_FLAGS_S, _): mark_SYN();

            // SYN with ECN
            //(TCP_FLAGS_S + TCP_FLAGS_E, _): mark_SYN(); // SYN with ECE
            //(TCP_FLAGS_S + TCP_FLAGS_C, _): mark_SYN(); // SYN with CWR
            //(TCP_FLAGS_S + TCP_FLAGS_E + TCP_FLAGS_C, _): mark_SYN(); // SYN with ECE and CWR

            // SYN-ACK
            (TCP_FLAGS_S + TCP_FLAGS_A, _): mark_SYNACK(); // SYN-ACK
            //(TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_E, _): mark_SYNACK(); // SYN-ACK with ECE
            //(TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_C, _): mark_SYNACK(); // SYN-ACK with CWR
            //(TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_E + TCP_FLAGS_C, _): mark_SYNACK(); // SYN-ACK with ECE and CWR

            // ACK only
            (TCP_FLAGS_A, 0..80): mark_ACK(); // ACK without SYN

            // ACK with ECN
            // (TCP_FLAGS_A + TCP_FLAGS_E, 0..80): mark_ACK(); // ACK with ECE
            // (TCP_FLAGS_A + TCP_FLAGS_C, 0..80): mark_ACK(); // ACK with CWR
            // (TCP_FLAGS_A + TCP_FLAGS_E + TCP_FLAGS_C, 0..80): mark_ACK(); // ACK with ECE and CWR

            // Extended Cases
            // (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_U, _): mark_SYNACK(); // SYN+ACK+URG
            // (TCP_FLAGS_A + TCP_FLAGS_U, 0..80): mark_ACK(); // ACK+URG
            // (TCP_FLAGS_S + TCP_FLAGS_F, _): mark_SYN(); // SYN+FIN
            // (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_F, _): mark_SYNACK(); // SYN+ACK+FIN

            // Additional Edge Cases
            // (TCP_FLAGS_S + TCP_FLAGS_P, _): mark_SYN(); // SYN with PSH
            // (TCP_FLAGS_S + TCP_FLAGS_A + TCP_FLAGS_P, _): mark_SYNACK(); // SYN+ACK with PSH
            // (TCP_FLAGS_A + TCP_FLAGS_F, 0..80): mark_ACK(); // ACK with FIN

            // General cases
            (_, 80..1600): mark_SEQ(); // General sequence packets
            (TCP_FLAGS_R, _): mark_FIN_RST(); // Reset flag
            (TCP_FLAGS_F, _): mark_FIN_RST(); // Fin flag
            (TCP_FLAGS_F + TCP_FLAGS_A, _): mark_FIN_RST(); // Fin flag
        }
    }

    apply {
        tb_decide_packet_type.apply();
    }
}