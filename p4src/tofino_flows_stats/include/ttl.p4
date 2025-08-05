#include "common/global.p4"

control TTL(inout headers_t hdr, inout metadata_t meta) {
    Register<bit<8>, _>(FLOWS_NO) flows_ttl;
    RegisterAction<bit<8> , _, bit<8>>(flows_ttl) get_flow_ttl = {
        void apply(inout bit<8> flow_ttl, out bit<8> rv) {
            rv = flow_ttl;
        }
    };

    RegisterAction<bit<8> , bit<16>, void>(flows_ttl) update_flow_ttl = {
        void apply(inout bit<8> flow_ttl) {
            flow_ttl = hdr.ipv4.ttl;
        }
    };
    apply {
        update_flow_ttl.execute(meta.flow_index);
    }
}