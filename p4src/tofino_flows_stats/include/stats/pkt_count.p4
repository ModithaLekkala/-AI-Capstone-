#include "../common/global.p4"

control PacketsCounter(inout headers_t hdr, inout metadata_t meta, in ingress_intrinsic_metadata_t ig_intr_md) {
    Register<bit<16>, _>(FLOWS_NO) flows_pkt_count;
    RegisterAction<bit<16> , bit<16>, bit<16>>(flows_pkt_count) update_and_get_flow_pkt_count = {
        void apply(inout bit<16> flow_pkt_count, out bit<16> rv) {
            flow_pkt_count = flow_pkt_count + 1;
            rv = flow_pkt_count;
        }
    };

    RegisterAction<bit<16> , bit<16>, bit<16>>(flows_pkt_count) get_flow_pkt_count = {
        void apply(inout bit<16> flow_pkt_count, out bit<16> rv) {
            rv = flow_pkt_count;
        }
    };

    apply {
        if(NOT_RESUB_PKT) {
            hdr.partial_bnn.spkts = update_and_get_flow_pkt_count.execute(meta.flow_index);
        } else {
            hdr.bnn.dpkts = get_flow_pkt_count.execute(meta.reverse_flow_index);
        }
    }
}