control FlowHashing(inout headers_t hdr, inout metadata_t meta) {

    Hash<bit<16>>(HashAlgorithm_t.CRC32) hash; 
    action apply_hash() { 
        meta.flow_index = hash.get({ 
            hdr.ipv4.src_addr, 
            hdr.ipv4.dst_addr, 
            hdr.ipv4.protocol, 
            hdr.tcp.src_port, 
            hdr.tcp.dst_port 
        }); 
    }

    Hash<bit<16>>(HashAlgorithm_t.CRC32) hash_rev; 
    action apply_hash_reverse() { 
        meta.reverse_flow_index = hash_rev.get({ 
            hdr.ipv4.dst_addr, 
            hdr.ipv4.src_addr, 
            hdr.ipv4.protocol, 
            hdr.tcp.dst_port, 
            hdr.tcp.src_port 
        }); 
    }

    apply {
        apply_hash();
        apply_hash_reverse();
    }
}
