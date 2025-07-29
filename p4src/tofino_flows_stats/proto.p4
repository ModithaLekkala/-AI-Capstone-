#include "common/global.p4"

#define PROTO_TCP 0
#define PROTO_UDP 1
#define PROTO_ICMP 2
#define PROTO_GRE 3
#define PROTO_OSPF 4
#define PROTO_OTHER 5

control Proto(inout headers_t hdr, inout metadata_t meta) {
    // Register to store protocol per flow
    Register<bit<8>, _>(FLOWS_NO) flows_proto;
    RegisterAction<bit<8> , _, bit<8>>(flows_proto) get_flow_proto = {
        void apply(inout bit<8> flow_proto, out bit<8> rv) {
            rv = flow_proto;
        }
    };
    RegisterAction<bit<8> , bit<16>, void>(flows_proto) update_flow_proto = {
        void apply(inout bit<8> flow_proto) {
            flow_proto = meta.proto;
        }
    };

    action set_proto_tcp() {
        meta.proto = PROTO_TCP;
    }
    action set_proto_udp() {
        meta.proto = PROTO_UDP;
    }
    action set_proto_icmp() {
        meta.proto = PROTO_ICMP;
    }
    action set_proto_gre() {
        meta.proto = PROTO_GRE;
    }
    action set_proto_ospf() {
        meta.proto = PROTO_OSPF;
    }
    action set_proto_other() {
        meta.proto = PROTO_OTHER;
    }

    // Table to map packet protocol to encoded value
    table proto_map {
        key = {
            hdr.ipv4.protocol : exact;
        }
        actions = {
            set_proto_tcp;
            set_proto_udp;
            set_proto_icmp;
            set_proto_gre;
            set_proto_ospf;
            set_proto_other;
        }
        size = 6;
        const entries = {
            (1) : set_proto_icmp();
            (6) : set_proto_tcp();
            (17) : set_proto_udp();
            (47) : set_proto_gre();
            (89) : set_proto_ospf();
        }
    }


    apply {
        proto_map.apply();
        update_flow_proto.execute(meta.flow_index);
    }
}
