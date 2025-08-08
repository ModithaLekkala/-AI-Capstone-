#include "../common/global.p4"

control PacketsCounter(inout headers_t hdr, inout metadata_t meta) {
    Register<bit<16>, _>(FLOWS_NO) flows_pkt_count;
    RegisterAction<bit<16> , bit<16>, bit<16>>(flows_pkt_count) update_and_get_flow_pkt_count = {
        void apply(inout bit<16> flow_pkt_count, out bit<16> rv) {
            flow_pkt_count = flow_pkt_count + 1;
            rv = flow_pkt_count;
        }
    };

    apply {
        meta.curr_flow.pkts = update_and_get_flow_pkt_count.execute(meta.flow_index);
    }
}