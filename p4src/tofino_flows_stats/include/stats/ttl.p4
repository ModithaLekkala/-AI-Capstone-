#include "../common/global.p4"

control TTL(inout collector_headers_t hdr, inout metadata_t meta, in ingress_intrinsic_metadata_t ig_intr_md) {
    Register<bit<8>,bit<16>>(FLOWS_NO) flows_sttl;
    Register<bit<8>,bit<16>>(FLOWS_NO) flows_dttl;

    RegisterAction<_, bit<16>, bit<8>>(flows_sttl) update_flow_sttl = {
        void apply(inout bit<8> ttl, out bit<8> rv) {
            ttl =  hdr.ipv4.ttl;
            rv = ttl;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_sttl) get_flow_sttl = {
        void apply(inout bit<8> ttl, out bit<8> rv) {
            rv = ttl;
        }
    };

    RegisterAction<_, bit<16>, bit<8>>(flows_dttl) update_flow_dttl = {
        void apply(inout bit<8> ttl, out bit<8> rv) {
            ttl =  hdr.ipv4.ttl;
            rv = ttl;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_dttl) get_flow_dttl = {
        void apply(inout bit<8> ttl, out bit<8> rv) {
            rv = ttl;
        }
    };

    action update_sttl() {
        hdr.bnn.sttl = update_flow_sttl.execute(meta.flow_index);
    }

    action update_dttl() {
        hdr.bnn.dttl = update_flow_dttl.execute(meta.flow_index);
    }

    action get_sttl() {
        hdr.bnn.sttl = get_flow_sttl.execute(meta.flow_index);
    }

    action get_dttl() {
        hdr.bnn.dttl = get_flow_dttl.execute(meta.flow_index);
    }

    apply {
        if(FORWARD_DIR_PKT) {
            if(meta.flow_pkts <= BIDIRECTIONAL_FLOW_MATURE_TIME) {
                update_sttl();
            } else {
                get_sttl();
            }
            get_dttl();
        } else {
            if(meta.flow_pkts <= BIDIRECTIONAL_FLOW_MATURE_TIME) {
                update_dttl();
            } else {
                get_dttl();
            }
            get_sttl();
        }
    }
}