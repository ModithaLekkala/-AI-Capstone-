/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
#include "include/common/headers.p4"
#include "include/common/util.p4"
#include "include/hash_flows.p4"
#include "include/ttl.p4"
#include "include/proto.p4"
#include "include/bytes.p4"
#include "include/pkt_count.p4"
#include "include/forward.p4"
#include "include/parsers.p4"
#include "include/deparsers.p4"

control Ingress(
    inout headers_t hdr,
    inout metadata_t meta,
    in    ingress_intrinsic_metadata_t ig_intr_md,
    in    ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t ig_tm_md 
){
    Forward() fw;
    FlowHashing() fh;
    PacketsCounter() pc;

    apply {
        /* compute index for flow and reversed flow */
        fh.apply(hdr, meta); 

        /* keeps track of analyzed pkts per flow */
        pc.apply(hdr, meta); 
        
        /* normal forwarding */
        fw.apply(hdr, meta, ig_tm_md,ig_intr_md);
    }
}

control Egress(
        inout headers_t hdr,
        inout metadata_t meta,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {
    
    Bytes() bytes;
    
    apply {
        /* sbytes, dbytes */
        bytes.apply(hdr, meta, eg_intr_md);
    }
}



Pipeline(
    IngressParser(),
    Ingress(),
    IngressDeparser(),
    EgressParser(),
    Egress(),
    EgressDeparser()
) inethynn;
Switch(inethynn) main;
