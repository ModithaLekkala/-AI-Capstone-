#include "common/global.p4"

control Bytes(inout headers_t hdr, inout metadata_t meta) {
    Register<bit<16>, _>(FLOWS_NO) flows_bytes;
    RegisterAction<bit<16> , _, bit<16>>(flows_bytes) get_flow_bytes = {
        void apply(inout bit<16> flow_bytes, out bit<16> rv) {
            rv = flow_bytes;
        }
    };

    RegisterAction<bit<16>, bit<16>, void>(flows_bytes) update_flow_bytes = {
        void apply(inout bit<16> flow_bytes) {
            flow_bytes = flow_bytes + hdr.ipv4.total_len;
        }
    };

    apply {
        update_flow_bytes.execute(meta.flow_index);   
    }
}