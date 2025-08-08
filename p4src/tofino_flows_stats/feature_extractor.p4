/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
#include "include/common/headers.p4"
#include "include/hash_flows.p4"
#include "include/stats/ttl.p4"
#include "include/stats/proto.p4"
#include "include/stats/bytes.p4"
#include "include/stats/pkt_count.p4"
#include "include/forward.p4"
#include "include/parsers.p4"
#include "include/deparsers.p4"
#include "include/stats/packet_type.p4"
#include "include/stats/iat.p4"

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
    TTL() ttl;
    PacketType() get_tcp_pkt_type;
    IAT() iat;
    Bytes() bytes;

    /* remaining features are already set in resubmit section of all stats modules */
    action compose_full_imput() {
        hdr.bnn.sttl = hdr.partial_bnn.sttl;
        hdr.bnn.sbytes = hdr.partial_bnn.sbytes;
        hdr.bnn.smean = hdr.partial_bnn.smean;
        hdr.bnn.spkts = hdr.partial_bnn.spkts;
    }

    apply {

        /* compute index for flow and reversed flow */
        fh.apply(hdr, meta);

        /* get current pkt number in the flow */
        pc.apply(hdr, meta, ig_intr_md);

        if(TCP_PKT) {
            /* get tcp pkt type */
            get_tcp_pkt_type.apply(hdr, meta);

            /* synack, ackdat */
            iat.apply(hdr, meta, ig_prsr_md);
        }

        /* sttl, dttl */
        ttl.apply(hdr, meta,ig_intr_md);


        /* sbytes, dbytes */
        bytes.apply(hdr, meta, ig_intr_md);


        /* resubmit to compute other way statistics */
        if((hdr.partial_bnn.spkts == FLOW_MATURE_TIME) && NOT_RESUB_PKT) {
            ig_dprsr_md.resubmit_type = 8;
        }

        /* port forwarding */
        if(RESUB_PKT) {
            hdr.bnn.setValid();
            compose_full_imput();
            fw.apply(hdr, meta, ig_tm_md);
        }

        /* skip egress */
        ig_tm_md.bypass_egress = 1w1;
    }
}

control Egress(
        inout headers_t hdr,
        inout metadata_t meta,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {
    
    apply {
        
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
