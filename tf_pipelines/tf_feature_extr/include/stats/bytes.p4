#include "../common/global.p4"

/* use hdr.ipv4.total_len instead of eg_it_md.total_length because I need to estimate the total bytes on ingress processing. */
/* That's because I need to resubmit the packet and the resubmission can only be done in ingress deparser. */

/* I resubmit the pkt to compute the other direction of the statistics. */
/* 1. src->dst statistics */
/* 2. resubmit */
/* 1. dst->stc statistics */

control Bytes(inout collector_headers_t hdr, inout metadata_t meta) {
    Register<bit<16>, bit<16>>(FLOWS_NO) flows_sbytes;
    Register<bit<16>, bit<16>>(FLOWS_NO) flows_dbytes;

    RegisterAction<_, bit<16>, bit<16>>(flows_sbytes) update_flows_sbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            flow_bytes = flow_bytes + meta.frame_len;
            rv = flow_bytes;
        }
    };
    RegisterAction<_, bit<16>, bit<16>>(flows_sbytes) get_flows_sbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
        }
    };

    RegisterAction<_, bit<16>, bit<16>>(flows_dbytes) update_flows_dbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            flow_bytes = flow_bytes + meta.frame_len;
            rv = flow_bytes;
        }
    };
    RegisterAction<_, bit<16>, bit<16>>(flows_dbytes) get_flows_dbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
            
        }
    };

    action update_sbytes() {
        hdr.bnn.sbytes=update_flows_sbytes.execute(meta.flow_index);
    }

    action update_dbytes() {
        hdr.bnn.dbytes=update_flows_dbytes.execute(meta.flow_index);
    }

    action get_sbytes() {
        hdr.bnn.sbytes = get_flows_sbytes.execute(meta.flow_index);
    }

    action get_dbytes() {
        hdr.bnn.dbytes = get_flows_dbytes.execute(meta.flow_index);
    }

    /* assumption: both flow directions are balanced */
    action compute_means() {
        hdr.bnn.smean = hdr.bnn.sbytes >> 3;
        hdr.bnn.dmean = hdr.bnn.dbytes >> 3;
    }
    
    apply {
        /* 14B Ethernet header + 4 Ethernet CRC */
        meta.frame_len = hdr.ipv4.total_len + 18;

        if(FORWARD_DIR_PKT) {
            if(meta.flow_pkts <= BIDIRECTIONAL_FLOW_MATURE_TIME) {
                update_sbytes();
            } else {
                get_sbytes();
            }
            get_dbytes();
        } else {
            if(meta.flow_pkts <= BIDIRECTIONAL_FLOW_MATURE_TIME) {
                update_dbytes();
            } else {
                get_dbytes();
            }
            get_sbytes();
        }
        compute_means();
    }  
}