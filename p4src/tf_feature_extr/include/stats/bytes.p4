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
    Register<bit<16>, bit<16>>(FLOWS_NO) flows_smaxbytes;
    Register<bit<16>, bit<16>>(FLOWS_NO) flows_dmaxbytes;
    Register<bit<16>, bit<16>>(FLOWS_NO) flows_sminbytes;
    Register<bit<16>, bit<16>>(FLOWS_NO) flows_dminbytes;


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
       
    RegisterAction<_, bit<16>, bit<16>>(flows_smaxbytes) update_flows_smaxbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            if(meta.frame_len > flow_bytes) {
                flow_bytes = meta.frame_len;
            }
            rv=flow_bytes;
        }
    };
    RegisterAction<_, bit<16>, bit<16>>(flows_smaxbytes) get_flows_smaxbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
        }
    };

    RegisterAction<_, bit<16>, bit<16>>(flows_dmaxbytes) update_flows_dmaxbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            if(meta.frame_len > flow_bytes) {
                flow_bytes = meta.frame_len;
            }
            rv=flow_bytes;
        }
    };
    RegisterAction<_, bit<16>, bit<16>>(flows_dmaxbytes) get_flows_dmaxbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
        }
    };

    RegisterAction<_, bit<16>, bit<16>>(flows_sminbytes) update_flows_sminbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            if(meta.frame_len < flow_bytes) {
                flow_bytes = meta.frame_len;
            }
            rv=flow_bytes;
        }
    };
    RegisterAction<_, bit<16>, bit<16>>(flows_sminbytes) get_flows_sminbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
        }
    };

    RegisterAction<_, bit<16>, bit<16>>(flows_dminbytes) update_flows_dminbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            if(meta.frame_len < flow_bytes) {
                flow_bytes = meta.frame_len;
            }
            rv=flow_bytes;
        }
    };
    RegisterAction<_, bit<16>, bit<16>>(flows_dminbytes) get_flows_dminbytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
        }
    };

    action update_sminbytes() {
        hdr.bnn.sminbytes = update_flows_sminbytes.execute(meta.flow_index);
    }

    action update_dminbytes() {
        hdr.bnn.dminbytes = update_flows_dminbytes.execute(meta.flow_index);
    }

    action get_sminbytes() {
        hdr.bnn.sminbytes = get_flows_sminbytes.execute(meta.flow_index);
    }

    action get_dminbytes() {
        hdr.bnn.dminbytes = get_flows_dminbytes.execute(meta.flow_index);
    }

    action update_smaxbytes() {
        hdr.bnn.smaxbytes = update_flows_smaxbytes.execute(meta.flow_index);
    }

    action update_dmaxbytes() {
        hdr.bnn.dmaxbytes = update_flows_dmaxbytes.execute(meta.flow_index);
    }

    action get_smaxbytes() {
        hdr.bnn.smaxbytes = get_flows_smaxbytes.execute(meta.flow_index);
    }

    action get_dmaxbytes() {
        hdr.bnn.dmaxbytes = get_flows_dmaxbytes.execute(meta.flow_index);
    }

    action update_sbytes() {
        hdr.bnn.sbytes = update_flows_sbytes.execute(meta.flow_index);
    }

    action update_dbytes() {
        hdr.bnn.dbytes = update_flows_dbytes.execute(meta.flow_index);
    }

    action get_sbytes() {
        hdr.bnn.sbytes = get_flows_sbytes.execute(meta.flow_index);
    }

    action get_dbytes() {
        hdr.bnn.dbytes = get_flows_dbytes.execute(meta.flow_index);
    }
    
    apply {
        /* 14B Ethernet header + 4 Ethernet CRC */
        meta.frame_len = hdr.ipv4.total_len;

        if(FORWARD_DIR_PKT) {
            if(meta.flow_pkts <= BIDIRECTIONAL_FLOW_MATURE_TIME) {
                update_sbytes();
                update_smaxbytes();
                update_sminbytes();
            } else {
                get_sbytes();
                get_smaxbytes();
                get_sminbytes();
            }
            get_dbytes();
            get_dmaxbytes();
            get_dminbytes();
        } else {
            if(meta.flow_pkts <= BIDIRECTIONAL_FLOW_MATURE_TIME) {
                update_dbytes();
                update_dmaxbytes();
                update_dminbytes();
            } else {
                get_dbytes();
            }
            get_sbytes();
            get_smaxbytes();
            get_sminbytes();
        }
    }  
}