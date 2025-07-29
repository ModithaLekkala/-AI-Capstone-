control Forward(
    inout headers_t hdr,
    inout metadata_t meta,
    inout ingress_intrinsic_metadata_for_tm_t ig_tm_md,
    in    ingress_intrinsic_metadata_t ig_intr_md
) {
    action send_back() {
        /* ether and ipv4 addr swap */
        bit<48> tmp = hdr.ethernet.dst_addr;
        hdr.ethernet.dst_addr = hdr.ethernet.src_addr;
        hdr.ethernet.src_addr = tmp;

        bit<32> tmp2 = hdr.ipv4.dst_addr;
        hdr.ipv4.dst_addr = hdr.ipv4.src_addr;
        hdr.ipv4.src_addr = tmp2;

        ig_tm_md.ucast_egress_port = ig_intr_md.ingress_port;
    }

    apply {
        send_back();
    }
}