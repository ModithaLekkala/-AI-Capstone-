control Forward(
    inout collector_headers_t hdr,
    inout metadata_t meta,
    inout ingress_intrinsic_metadata_for_tm_t ig_tm_md
) {
    action send_back() {
        /* ether and ipv4 addr swap */
        bit<48> tmp = hdr.ethernet.dst_addr;
        hdr.ethernet.dst_addr = hdr.ethernet.src_addr;
        hdr.ethernet.src_addr = tmp;

        bit<32> tmp2 = hdr.ipv4.dst_addr;
        hdr.ipv4.dst_addr = hdr.ipv4.src_addr;
        hdr.ipv4.src_addr = tmp2;

        ig_tm_md.ucast_egress_port = 1;
    }

    apply {
        send_back();
    }
}