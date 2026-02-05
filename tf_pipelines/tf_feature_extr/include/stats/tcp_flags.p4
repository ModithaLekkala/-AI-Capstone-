#include "../common/global.p4"

control TcpFlags(inout collector_headers_t hdr, inout metadata_t meta) {
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_fin_cnt;
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_syn_cnt;
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_ack_cnt;
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_psh_cnt;
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_rst_cnt;
    Register<bit<8>, bit<16>>(FLOWS_NO) flows_ece_cnt;

    /* FIN flag counter */
    RegisterAction<_, bit<16>, bit<8>>(flows_fin_cnt) update_fin_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            cnt = cnt + 1;
            rv = cnt;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_fin_cnt) get_fin_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            rv = cnt;
        }
    };

    /* SYN flag counter */
    RegisterAction<_, bit<16>, bit<8>>(flows_syn_cnt) update_syn_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            cnt = cnt + 1;
            rv = cnt;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_syn_cnt) get_syn_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            rv = cnt;
        }
    };

    /* ACK flag counter */
    RegisterAction<_, bit<16>, bit<8>>(flows_ack_cnt) update_ack_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            cnt = cnt + 1;
            rv = cnt;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_ack_cnt) get_ack_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            rv = cnt;
        }
    };

    /* PSH flag counter */
    RegisterAction<_, bit<16>, bit<8>>(flows_psh_cnt) update_psh_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            cnt = cnt + 1;
            rv = cnt;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_psh_cnt) get_psh_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            rv = cnt;
        }
    };

    /* RST flag counter */
    RegisterAction<_, bit<16>, bit<8>>(flows_rst_cnt) update_rst_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            cnt = cnt + 1;
            rv = cnt;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_rst_cnt) get_rst_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            rv = cnt;
        }
    };

    /* ECE flag counter */
    RegisterAction<_, bit<16>, bit<8>>(flows_ece_cnt) update_ece_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            cnt = cnt + 1;
            rv = cnt;
        }
    };
    RegisterAction<_, bit<16>, bit<8>>(flows_ece_cnt) get_ece_cnt = {
        void apply(inout bit<8> cnt, out bit<8> rv) {
            rv = cnt;
        }
    };

    action do_update_fin_cnt() {
        hdr.bnn.fin_cnt = update_fin_cnt.execute(meta.flow_index);
    }
    action do_get_fin_cnt() {
        hdr.bnn.fin_cnt = get_fin_cnt.execute(meta.flow_index);
    }

    action do_update_syn_cnt() {
        hdr.bnn.syn_cnt = update_syn_cnt.execute(meta.flow_index);
    }
    action do_get_syn_cnt() {
        hdr.bnn.syn_cnt = get_syn_cnt.execute(meta.flow_index);
    }

    action do_update_ack_cnt() {
        hdr.bnn.ack_cnt = update_ack_cnt.execute(meta.flow_index);
    }
    action do_get_ack_cnt() {
        hdr.bnn.ack_cnt = get_ack_cnt.execute(meta.flow_index);
    }

    action do_update_psh_cnt() {
        hdr.bnn.psh_cnt = update_psh_cnt.execute(meta.flow_index);
    }
    action do_get_psh_cnt() {
        hdr.bnn.psh_cnt = get_psh_cnt.execute(meta.flow_index);
    }

    action do_update_rst_cnt() {
        hdr.bnn.rst_cnt = update_rst_cnt.execute(meta.flow_index);
    }
    action do_get_rst_cnt() {
        hdr.bnn.rst_cnt = get_rst_cnt.execute(meta.flow_index);
    }

    action do_update_ece_cnt() {
        hdr.bnn.ece_cnt = update_ece_cnt.execute(meta.flow_index);
    }
    action do_get_ece_cnt() {
        hdr.bnn.ece_cnt = get_ece_cnt.execute(meta.flow_index);
    }

    apply {
        if(meta.flow_pkts <= BIDIRECTIONAL_FLOW_MATURE_TIME) {
            /* Update counters based on TCP flags */
            if ((hdr.tcp.flags & TCP_FLAGS_F) != 0) {
                do_update_fin_cnt();
            } else {
                do_get_fin_cnt();
            }

            if ((hdr.tcp.flags & TCP_FLAGS_S) != 0) {
                do_update_syn_cnt();
            } else {
                do_get_syn_cnt();
            }

            if ((hdr.tcp.flags & TCP_FLAGS_A) != 0) {
                do_update_ack_cnt();
            } else {
                do_get_ack_cnt();
            }

            if ((hdr.tcp.flags & TCP_FLAGS_P) != 0) {
                do_update_psh_cnt();
            } else {
                do_get_psh_cnt();
            }

            if ((hdr.tcp.flags & TCP_FLAGS_R) != 0) {
                do_update_rst_cnt();
            } else {
                do_get_rst_cnt();
            }

            if ((hdr.tcp.flags & TCP_FLAGS_E) != 0) {
                do_update_ece_cnt();
            } else {
                do_get_ece_cnt();
            }
        } else {
            /* Just read the counters */
            do_get_fin_cnt();
            do_get_syn_cnt();
            do_get_ack_cnt();
            do_get_psh_cnt();
            do_get_rst_cnt();
            do_get_ece_cnt();
        }
    }
}
