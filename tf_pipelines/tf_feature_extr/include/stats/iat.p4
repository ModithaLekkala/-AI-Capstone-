#include "../common/global.p4"

struct paired_iat {
    timestamp iat;
    bit<32> done;
}

control IAT(inout collector_headers_t hdr, 
            inout metadata_t meta, 
            in ingress_intrinsic_metadata_from_parser_t ig_prsr_md) {
    
    Register<paired_iat, bit<16>>(FLOWS_NO) flows_last_pkt_1;
    Register<paired_iat, bit<16>>(FLOWS_NO) flows_last_pkt_2;

    RegisterAction<_, bit<16>, void>(flows_last_pkt_1) update_iat_1 = {
        void apply(inout paired_iat last_pkt) {
            if(last_pkt.done == 0) {
                last_pkt.iat = ig_prsr_md.global_tstamp[31:0];
            }
        }
    };

    RegisterAction<_, bit<16>, bit<32>>(flows_last_pkt_1) get_synack = {
        void apply(inout paired_iat last_pkt, out bit<32> rv) {
            if(last_pkt.done == 0) {
                last_pkt.iat = last_pkt.iat - ig_prsr_md.global_tstamp[31:0];
                last_pkt.done = 1;
                rv = last_pkt.iat;
            } else {
                rv = last_pkt.iat;
            }
        }
    };

    RegisterAction<_, bit<16>, void>(flows_last_pkt_2) update_iat_2 = {
        void apply(inout paired_iat last_pkt) {
            if(last_pkt.done == 0) {
                last_pkt.iat = ig_prsr_md.global_tstamp[31:0];
            }
        }
    };

    RegisterAction<_, bit<16>, bit<32>>(flows_last_pkt_2) get_ackdat = {
        void apply(inout paired_iat last_pkt, out bit<32> rv) {
            if(last_pkt.done == 0) {
                last_pkt.iat = last_pkt.iat - ig_prsr_md.global_tstamp[31:0];
                last_pkt.done = 1;
                rv = last_pkt.iat;
            } else {
                rv = last_pkt.iat;
            }
        }
    };
    
    apply {
        if(meta.tcp_type==PKT_TYPE_SYN) {
            update_iat_1.execute(meta.flow_index);
        }

        if(meta.tcp_type==PKT_TYPE_SYNACK) {
            hdr.bnn.synack = (bit<8>)get_synack.execute(meta.reverse_flow_index);
            update_iat_2.execute(meta.flow_index);
        } 
        
        if(meta.tcp_type==PKT_TYPE_ACK) {
            hdr.bnn.ackdat = (bit<8>)get_ackdat.execute(meta.reverse_flow_index);
        }

        hdr.bnn.ackdat = (bit<8>)get_ackdat.execute(meta.reverse_flow_index);
        hdr.bnn.synack = (bit<8>)get_synack.execute(meta.reverse_flow_index);
    }
}
