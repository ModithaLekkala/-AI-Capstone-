#include "../common/global.p4"

control PacketsCounter(inout collector_headers_t hdr, inout metadata_t meta, in ingress_intrinsic_metadata_t ig_intr_md) {
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_spkts;
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_dpkts;
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_pkts;

    RegisterAction<_, bit<16>, bit<8>>(flows_spkts) update_and_get_flows_spkts = {
        void apply(inout bit<8> flow_pkts, out bit<8> rv) {
            flow_pkts = flow_pkts + 1;
            rv = flow_pkts;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_spkts) get_flows_spkts = {
        void apply(inout bit<8> flow_pkts, out bit<8> rv) {
            rv = flow_pkts;
        }
    };

    RegisterAction<_, bit<16>, bit<8>>(flows_dpkts) update_and_get_flows_dpkts = {
        void apply(inout bit<8> flow_pkts, out bit<8> rv) {
            flow_pkts = flow_pkts + 1;
            rv = flow_pkts;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_dpkts) get_flows_dpkts = {
        void apply(inout bit<8> flow_pkts, out bit<8> rv) {
            rv = flow_pkts;
        }
    };

    RegisterAction<_, bit<16>, bit<8>>(flows_pkts) update_flows_pkts = {
        void apply(inout bit<8> flow_pkts, out bit<8> rv) {
            flow_pkts = flow_pkts + 1;
            rv = flow_pkts;
        }
    };

    action update_spkts() {
        hdr.bnn.spkts = update_and_get_flows_spkts.execute(meta.flow_index);
    }

    action get_spkts() {
        hdr.bnn.spkts = get_flows_spkts.execute(meta.flow_index);
    }

    action update_dpkts() {
        hdr.bnn.dpkts = update_and_get_flows_dpkts.execute(meta.flow_index);
    }
    action get_dpkts() {
        hdr.bnn.dpkts = get_flows_dpkts.execute(meta.flow_index);
    }

    action update_pkts() {
        meta.flow_pkts = update_flows_pkts.execute(meta.flow_index);
    }

    apply {
        update_pkts();
        hdr.bridged_md.flow_pkts = meta.flow_pkts;
        if(FORWARD_DIR_PKT) {
            update_spkts();
            get_dpkts();
        } else {
            update_dpkts();
            get_spkts();
        }
    }
}
