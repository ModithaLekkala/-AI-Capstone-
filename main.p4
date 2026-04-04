// main.p4 
#include <core.p4>
#include <v1model.p4>

// --- CONSTANTS ---
#define HASH_BASE 10w0       // Base for hash calculation.
#define HASH_MAX 10w1023     // Max hash value, for 1024 register entries.
#define ETH_TYPE_IPV4 0x0800 // EtherType for IPv4.
#define IP_PROTO_TCP 8w6     // IP protocol for TCP.

// --- HEADER DEFINITIONS ---
// Defines Ethernet header structure.
header ethernet_t {
    bit<48> dst_addr;
    bit<48> src_addr;
    bit<16> ether_type;
}

// Defines IPv4 header structure.
header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<6>  dscp;
    bit<2>  ecn;
    bit<16> len;
    bit<16> identification;
    bit<3>  flags;
    bit<13> frag_offset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdr_checksum;
    bit<32> src_addr;
    bit<32> dst_addr;
}

// Defines TCP header structure.
header tcp_t {
    bit<16> src_port;
    bit<16> dst_port;
    bit<32> seq_no;
    bit<32> ack_no;
    bit<4>  data_offset;
    bit<3>  res;
    bit<3>  ecn;
    bit<6>  ctrl; // TCP flags (PSH, etc.)
    bit<16> window;
    bit<16> checksum;
    bit<16> urgent_ptr;
}

// Struct to hold all parsed headers.
struct headers_t {
    ethernet_t ethernet;
    ipv4_t     ipv4;
    tcp_t      tcp;
}

// --- USER METADATA ---
// Per-packet data used during processing.
struct local_metadata_t {
    bit<32> hashed_address; // Index for registers.
    // Window stats used as keys in the decision table.
    bit<32> win_pkglength;
    bit<32> win_pkgcount;
    bit<32> win_maxlength;
    bit<32> win_minlength;
    bit<8>  win_psh;
    bit<1>  should_forward; // Forwarding decision flag.
}

// --- PARSER ---
// Extracts Ethernet -> IPv4 -> TCP headers.
parser parser_impl(packet_in packet,
                   out headers_t hdr,
                   inout local_metadata_t user_md,
                   inout standard_metadata_t st_md) {
    state start { transition parse_ethernet; }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.ether_type) {
            ETH_TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            IP_PROTO_TCP: parse_tcp;
            default: accept;
        }
    }
    state parse_tcp {
        packet.extract(hdr.tcp);
        transition accept;
    }
}

// --- INGRESS PIPELINE ---
// Main packet processing logic.
control ingress(inout headers_t hdr,
                inout local_metadata_t user_md,
                inout standard_metadata_t st_md) {

    // Registers for stateful flow tracking.
    register<bit<48>>(1024) last_time_reg;
    register<bit<48>>(1024) win_interval_reg;
    register<bit<32>>(1024) win_pkgcount_reg;
    register<bit<32>>(1024) win_pkglength_reg;
    register<bit<32>>(1024) win_maxlength_reg;
    register<bit<32>>(1024) win_minlength_reg;
    register<bit<8>>(1024)  win_psh_reg;

    // Actions to be applied by the decision table.
	action drop()    { user_md.should_forward = 0; mark_to_drop(st_md); }
	action forward() { user_md.should_forward = 1; }

    // Action to clear a flow's statistics to start a new window.
    action reset_window_stats() {
        win_interval_reg.write(user_md.hashed_address, 0);
        win_pkgcount_reg.write(user_md.hashed_address, 0);
        win_pkglength_reg.write(user_md.hashed_address, 0);
        win_maxlength_reg.write(user_md.hashed_address, 0);
        win_minlength_reg.write(user_md.hashed_address, 0);
        win_psh_reg.write(user_md.hashed_address, 0);
	}

    // Decision table matches on flow stats to select an action (drop/forward).
    table decision_table {
        key = {
            user_md.win_maxlength : ternary;
            user_md.win_minlength : ternary;
            user_md.win_psh       : ternary;
            user_md.win_pkglength : ternary;
            user_md.win_pkgcount  : ternary;
        }
        actions = { drop; forward; }
        size = 1024;
        default_action = forward();
    }

    // Actions to compute a symmetric flow hash for the register index.
    action compute_server_flow () { hash(user_md.hashed_address, HashAlgorithm.crc16, HASH_BASE, {hdr.ipv4.dst_addr, hdr.tcp.dst_port, hdr.ipv4.src_addr, hdr.tcp.src_port}, HASH_MAX); }
    action compute_client_flow () { hash(user_md.hashed_address, HashAlgorithm.crc16, HASH_BASE, {hdr.ipv4.src_addr, hdr.tcp.src_port, hdr.ipv4.dst_addr, hdr.tcp.dst_port}, HASH_MAX); }

    // Main ingress logic block.
    apply {
        user_md.should_forward = 0; // Default to not forwarding.
        // Calculate a flow hash if the packet is valid IPv4.
        if(hdr.ipv4.isValid()) {
            if(st_md.ingress_port == 1) { compute_server_flow(); } else { compute_client_flow(); }
        }

        // --- Accumulate statistics for the flow ---
        bit<8> psh_value = 0;
        if(hdr.tcp.isValid() && (hdr.tcp.ctrl & 0b001000) > 0) { psh_value = 1; }
        
        // Read current statistics from registers.
        bit<32> win_pkgcount_val; bit<32> win_pkglength_val; bit<32> win_maxlength_val; bit<32> win_minlength_val; bit<8> win_psh_val;
        win_pkgcount_reg.read(win_pkgcount_val, user_md.hashed_address);
        win_pkglength_reg.read(win_pkglength_val, user_md.hashed_address);
        win_maxlength_reg.read(win_maxlength_val, user_md.hashed_address);
        win_minlength_reg.read(win_minlength_val, user_md.hashed_address);
        win_psh_reg.read(win_psh_val, user_md.hashed_address);

        // --- Time window logic and decision making ---
        // Calculate total elapsed time for the current window.
        bit<48> last_time; bit<48> win_interval; bit<48> curr_interval = 0;
        last_time_reg.read(last_time, user_md.hashed_address);
        win_interval_reg.read(win_interval, user_md.hashed_address);
        if (last_time != 0) { curr_interval = st_md.ingress_global_timestamp - last_time; }
        win_interval = win_interval + curr_interval;
        last_time_reg.write(user_md.hashed_address, st_md.ingress_global_timestamp);
        win_interval_reg.write(user_md.hashed_address, win_interval);

        // If time window (2s) has not expired, forward the packet.
        if (win_interval < 2000000) {
            user_md.should_forward = 1;
        } else {
            // If window expired, copy stats to metadata for the table.
            user_md.win_pkglength = win_pkglength_val;
            user_md.win_pkgcount = win_pkgcount_val;
            user_md.win_maxlength = win_maxlength_val;
            user_md.win_minlength = win_minlength_val;
            user_md.win_psh = win_psh_val;
            // Apply the decision table and then reset the flow's stats.
            decision_table.apply();
            reset_window_stats();
        }

        // Update stats with data from the current packet.
        win_pkgcount_val = win_pkgcount_val + 1;
        win_pkglength_val = win_pkglength_val + st_md.packet_length;
        win_psh_val = win_psh_val + psh_value;
        if(win_pkgcount_val == 0) { // Initialize min/max length on first packet.
            win_maxlength_val = st_md.packet_length;
            win_minlength_val = st_md.packet_length;
        } else { // Otherwise, update min/max if needed.
            if(st_md.packet_length > win_maxlength_val) { win_maxlength_val = st_md.packet_length; }
            if(st_md.packet_length < win_minlength_val) { win_minlength_val = st_md.packet_length; }
        }
        // Write updated statistics back to registers.
        win_pkgcount_reg.write(user_md.hashed_address, win_pkgcount_val);
        win_pkglength_reg.write(user_md.hashed_address, win_pkglength_val);
        win_maxlength_reg.write(user_md.hashed_address, win_maxlength_val);
        win_minlength_reg.write(user_md.hashed_address, win_minlength_val);
        win_psh_reg.write(user_md.hashed_address, win_psh_val);

        // Forward the packet if the final decision was to forward.
        if (user_md.should_forward == 1) {
            st_md.egress_spec = 1;
        }
    }
}

// --- EGRESS AND DEPARSER ---
// Egress pipeline is empty.
control egress(inout headers_t hdr, inout local_metadata_t user_md, inout standard_metadata_t st_md) { apply { } }
// Checksum controls are empty; no checksum validation or calculation.
control no_verify_checksum(inout headers_t hdr, inout local_metadata_t user_md) { apply { } }
control no_compute_checksum(inout headers_t hdr, inout local_metadata_t user_md) { apply { } }

// Reconstruct the outgoing packet from headers.
control deparser(packet_out pkt, in headers_t hdr) {
    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.tcp);
    }
}

// Instantiate the V1Switch model with all the defined blocks.
V1Switch(parser_impl(), no_verify_checksum(), ingress(), egress(), no_compute_checksum(), deparser()) main;
