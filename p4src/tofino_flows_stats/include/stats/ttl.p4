#include "../common/global.p4"

control TTL(inout headers_t hdr, inout metadata_t meta, in ingress_intrinsic_metadata_t ig_intr_md) {
    Register<bit<8> ,bit<16>>(FLOWS_NO) flows_ttl;
    RegisterAction<_, bit<16>, bit<8>>(flows_ttl) update_and_get_flow_ttl = {
        void apply(inout bit<8> ttl, out bit<8> rv) {
            ttl =  hdr.ipv4.ttl;
            rv = ttl;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_ttl) get_flow_ttl = {
        void apply(inout bit<8> ttl, out bit<8> rv) {
            rv = ttl;
        }
    };

    apply {
        if(NOT_RESUB_PKT) {
            hdr.partial_bnn.sttl = update_and_get_flow_ttl.execute(meta.flow_index);
        } else {
            hdr.bnn.dttl = get_flow_ttl.execute(meta.reverse_flow_index);
        }
    }
}