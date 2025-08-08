control IngressDeparser(
    packet_out      pkt,
    inout headers_t hdr,
    in   metadata_t meta,
    in   ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md)
{
    /* resubmission for other way statistics - dst->src */
    Resubmit() resubmit;
    apply {
        if (ig_dprsr_md.resubmit_type == 8) {
            resubmit.emit(hdr.partial_bnn);
        }

        pkt.emit(hdr.bnn);
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.tcp);
        pkt.emit(hdr.udp);
    }
}

control EgressDeparser(
        packet_out pkt,
        inout headers_t hdr,
        in metadata_t eg_md,
        in egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md) {
    
    apply {
        pkt.emit(hdr.bnn);
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.tcp);
        pkt.emit(hdr.udp);
    }
}