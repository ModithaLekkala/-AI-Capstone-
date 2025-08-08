#include "../common/global.p4"

control TTL(inout headers_t hdr, inout metadata_t meta) {
    Register<bit<8> ,bit<16>>(FLOWS_NO) flows_ttl;
    RegisterAction<_, bit<16>, bit<8>>(flows_ttl) update_and_get_flow_ttl = {
        void apply(inout bit<8> ttl, out bit<8> rv) {
            ttl =  hdr.ipv4.ttl;
            rv = ttl;
        }
    };

    apply {
        meta.curr_flow.ttl = update_and_get_flow_ttl.execute(meta.flow_index);
    }
}