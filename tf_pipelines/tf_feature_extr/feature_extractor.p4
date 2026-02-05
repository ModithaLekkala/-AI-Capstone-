/* -*- P4_16 -*- */
#include <core.p4>
#include <tna.p4>
#include "../common/headers.p4"
#include "include/common/headers.p4"
#include "include/hash_flows.p4"
#include "include/stats/bytes.p4"
#include "include/stats/pkt_count.p4"
#include "include/stats/tcp_flags.p4"
#include "include/forward.p4"
#include "include/parsers.p4"
#include "include/deparsers.p4"

control CollectorIngress(
    inout collector_headers_t hdr,
    inout metadata_t meta,
    in    ingress_intrinsic_metadata_t ig_intr_md,
    in    ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t ig_tm_md
){
    Forward() fw;
    FlowHashing() fh;
    PacketsCounter() pc;
    TcpFlags() tcp_flags;
    Bytes() bytes;

    action set_normal_pkt() {
        hdr.bridged_md.setValid();
        hdr.bridged_md.pkt_type = PKT_TYPE_NORMAL;
    }

    apply {
        /* compute flow index */
        fh.apply(hdr, meta);

        /* spkts, dpkts */
        pc.apply(hdr, meta, ig_intr_md);

        if(TCP_PKT) {
            /* fin_cnt, syn_cnt, ack_cnt, psh_cnt, rst_cnt, ece_cnt */
            tcp_flags.apply(hdr, meta);
        }

        /* port forwarding */
        fw.apply(hdr, meta, ig_tm_md);

        /* sbytes, dbytes, smeansz, dmeansz, smaxbytes, dmaxbytes, sminbytes, dminbytes */
        bytes.apply(hdr, meta);

        /* set bnn output if flow is mature */
        if(meta.flow_pkts == BIDIRECTIONAL_FLOW_MATURE_TIME) {
            hdr.bnn.setValid();

            /* mirror logic */
            set_normal_pkt();
            ig_tm_md.ucast_egress_port=2;
            hdr.bridged_md.do_egr_mirroring = 1;
            hdr.bridged_md.egr_mir_ses = 1;
        }
    }
}

control CollectorEgress(
        inout collector_headers_t hdr,
        inout metadata_t meta,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t eg_dprsr_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {

    action set_mirror() {
        meta.egr_mir_ses = hdr.bridged_md.egr_mir_ses;
        meta.pkt_type = PKT_TYPE_MIRROR;
        eg_dprsr_md.mirror_type = MIRROR_TYPE_E2E;
    }

    action set_bnn_hdr() {
        hdr.bnn.setValid();
        hdr.ipv4.setInvalid();
        hdr.tcp.setInvalid();
        hdr.udp.setInvalid();
        hdr.mirrored_md.setInvalid();
        hdr.ethernet.setValid();
        hdr.ethernet.ether_type = FEATURE_COLLECTOR_PKT_ETYPE;
    }

    apply {
        if(hdr.bridged_md.do_egr_mirroring == 1) {
            set_mirror();
        } else if(hdr.mirrored_md.isValid()) {
            set_bnn_hdr();
        }
    }
}

Pipeline(
    CollectorIngressParser(),
    CollectorIngress(),
    CollectorIngressDeparser(),
    CollectorEgressParser(),
    CollectorEgress(),
    CollectorEgressDeparser()
) features_collector;
Switch(features_collector) main;
