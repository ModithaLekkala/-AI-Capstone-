#include "common/global.p4"

struct paired_addr {
    ipv4_addr_t src;
    ipv4_addr_t dst;
}

control FlowHashing(inout headers_t hdr, inout metadata_t meta) {
    @symmetric("hdr.ipv4.src_addr", "hdr.ipv4.dst_addr")
    @symmetric("hdr.tcp.src_port", "hdr.tcp.dst_port")
    Hash<bit<16>>(HashAlgorithm_t.CRC16) hash_tcp;
    action apply_hash_tcp() { 
        meta.flow_index = hash_tcp.get({ 
            hdr.ipv4.src_addr, 
            hdr.ipv4.dst_addr, 
            hdr.ipv4.protocol, 
            hdr.tcp.src_port, 
            hdr.tcp.dst_port 
        }); 
    }

    action apply_hash_reverse_tcp() { 
        meta.reverse_flow_index = hash_tcp.get({ 
            hdr.ipv4.dst_addr, 
            hdr.ipv4.src_addr, 
            hdr.ipv4.protocol, 
            hdr.tcp.dst_port, 
            hdr.tcp.src_port 
        }); 
    }

    @symmetric("hdr.ipv4.src_addr", "hdr.ipv4.dst_addr")
    @symmetric("hdr.udp.src_port", "hdr.udp.dst_port")
    Hash<bit<16>>(HashAlgorithm_t.CRC16) hash_udp; 
    action apply_hash_udp() { 
        meta.flow_index = hash_udp.get({ 
            hdr.ipv4.src_addr, 
            hdr.ipv4.dst_addr, 
            hdr.ipv4.protocol, 
            hdr.udp.src_port, 
            hdr.udp.dst_port 
        }); 
    }
    action apply_hash_reverse_udp() { 
        meta.reverse_flow_index = hash_udp.get({ 
            hdr.ipv4.dst_addr, 
            hdr.ipv4.src_addr, 
            hdr.ipv4.protocol, 
            hdr.udp.dst_port, 
            hdr.udp.src_port 
        }); 
    }

    Register<paired_addr, _>(FLOWS_NO) flows_src_dst;
    RegisterAction<_, bit<16>, ipv4_addr_t>(flows_src_dst) updare_set_flows_src_dst = {
        void apply(inout paired_addr flow_src_dst, out ipv4_addr_t rv) {
            if(flow_src_dst.src == 0 && flow_src_dst.dst == 0) {
                flow_src_dst.src = hdr.ipv4.src_addr;
                flow_src_dst.dst = hdr.ipv4.dst_addr;
            }
            rv = flow_src_dst.src;
        }
    };

    apply {
        if(hdr.tcp.isValid()) {
            apply_hash_tcp();
        } else if (hdr.udp.isValid()) {
            apply_hash_udp();
        }

        meta.dummy = updare_set_flows_src_dst.execute(meta.flow_index);
        if(meta.dummy == hdr.ipv4.src_addr) {
            meta.flow_dir = 1;
        } else {
            meta.flow_dir = 0;
        }
    }
}
