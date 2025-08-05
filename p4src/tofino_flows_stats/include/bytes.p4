#include "common/global.p4"

control Bytes(inout headers_t hdr, inout metadata_t meta, in egress_intrinsic_metadata_t eg_intr_md) {
    Register<bit<16>, _>(FLOWS_NO) flows_bytes;
    // RegisterAction<bit<16> , _, bit<16>>(flows_bytes) get_flow_bytes = {
    //     void apply(inout bit<16> flow_bytes, out bit<16> rv) {
    //         rv = flow_bytes;
    //     }
    // };

    RegisterAction<bit<16>, bit<16>, bit<16>>(flows_bytes) update_flow_bytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            flow_bytes = flow_bytes + eg_intr_md.pkt_length;
            rv = flow_bytes;
        }
    };

    apply {
        meta.curr_flow.bytes = update_flow_bytes.execute(meta.flow_index);
        if(meta.curr_flow.pkts == 8) {
            meta.curr_flow.bytes_mean = meta.curr_flow.pkts >> 3;
        }
    }  
}