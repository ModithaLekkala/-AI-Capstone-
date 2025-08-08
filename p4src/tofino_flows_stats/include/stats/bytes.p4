#include "../common/global.p4"

/* use hdr.ipv4.total_len instead of eg_it_md.total_length because I need to estimate the total bytes on ingress processing. */
/* That's because I need to resubmit the packet and the resubmission can only be done in ingress deparser. */

/* I resubmit the pkt to compute the other direction of the statistics. */
/* 1. src->dst statistics */
/* 2. resubmit */
/* 1. dst->stc statistics */

control Bytes(inout headers_t hdr, inout metadata_t meta, in ingress_intrinsic_metadata_t ig_intr_md) {
    Register<bit<16>, bit<16>>(FLOWS_NO) flows_bytes;
    Register<bit<16>, bit<16>>(FLOWS_NO) flows_eth_bytes;


    RegisterAction<bit<16>, bit<16>, bit<16>>(flows_bytes) update_flows_bytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            // flow_bytes = flow_bytes + eg_intr_md.pkt_length;
            flow_bytes = flow_bytes + hdr.ipv4.total_len;
            rv = flow_bytes;
        }
    };
    RegisterAction<bit<16>, bit<16>, bit<16>>(flows_bytes) get_flows_bytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
        }
    };


    /* 14B Ethernet header + 4 Ethernet CRC */
    RegisterAction<bit<16>, bit<16>, bit<16>>(flows_eth_bytes) update_flows_eth_bytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            flow_bytes = flow_bytes + 18;
            rv = flow_bytes;
        }
    };
    RegisterAction<bit<16>, bit<16>, bit<16>>(flows_eth_bytes) get_flows_eth_bytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
        }
    };

    bit<16> tmp_bytes = 0;
    bit<16> tmp_bytes_eth = 0;

    action compute_smean() {
        hdr.partial_bnn.smean = hdr.partial_bnn.sbytes >> 3;
    }

    action compute_dmean() {
        hdr.bnn.dmean = hdr.bnn.dbytes >> 3;
    }
    

    apply {
        if(NOT_RESUB_PKT) {
            tmp_bytes = update_flows_bytes.execute(meta.flow_index);
            tmp_bytes_eth = update_flows_eth_bytes.execute(meta.flow_index);
            if(hdr.partial_bnn.spkts == FLOW_MATURE_TIME) {
                hdr.partial_bnn.sbytes = tmp_bytes+tmp_bytes_eth;
                compute_smean();
            }
        } else {
            tmp_bytes = get_flows_bytes.execute(meta.reverse_flow_index);
            tmp_bytes_eth = get_flows_eth_bytes.execute(meta.reverse_flow_index);
            hdr.bnn.dbytes = tmp_bytes+tmp_bytes_eth;
            compute_dmean();
        }
    }  
}