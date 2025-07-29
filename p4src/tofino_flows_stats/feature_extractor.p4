/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
#include "common/headers.p4"
#include "common/util.p4"
#include "ingress_parser.p4"
#include "hash_flows.p4"
#include "ttl.p4"
#include "proto.p4"
#include "bytes.p4"
#include "pkt_count.p4"
#include "forward.p4"



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
    Bytes() bytes;

    apply {
        /* compute index for flow and reversed flow */
        // fh.apply(hdr, meta); 
        // /* sbytes, dbytes */
        // bytes.apply(hdr, meta);
        
        /* normal forwarding */
        fw.apply(hdr, meta, ig_tm_md,ig_intr_md);
        ig_tm_md.bypass_egress = 1w1;
    }
}


control IngressDeparser(
    packet_out      pkt,
    inout headers_t hdr,
    in   metadata_t meta,
    in   ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md)
{
    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.tcp);
        pkt.emit(hdr.udp);
    }
}



Pipeline(
    IngressParser(),
    Ingress(),
    IngressDeparser(),
    EmptyEgressParser(),
    EmptyEgress(),
    EmptyEgressDeparser()
) inethynn;
Switch(inethynn) main;
