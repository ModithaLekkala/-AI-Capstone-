-- features_hdrv3.lua — Wireshark dissector for BNN Feature Header v3
-- Matches the P4 bnn_input_h header structure:
--
-- header bnn_input_h {
--     bit<16> sbytes;
--     bit<16> dbytes;
--     bit<8> spkts;
--     bit<8> dpkts;
--     bit<16> smeansz;
--     bit<16> dmeansz;
--     bit<16> smaxbytes;
--     bit<16> dmaxbytes;
--     bit<16> sminbytes;
--     bit<16> dminbytes;
--     bit<8> fin_cnt;
--     bit<8> syn_cnt;
--     bit<8> ack_cnt;
--     bit<8> psh_cnt;
--     bit<8> rst_cnt;
--     bit<8> ece_cnt;
-- }
-- Total: 26 bytes

local bnn = Proto("bnn_features", "BNN Features Header v3")

-- Define fields (all standard 8/16 bit widths)
local f_sbytes    = ProtoField.uint16("bnn_features.sbytes",    "sBytes",    base.DEC)
local f_dbytes    = ProtoField.uint16("bnn_features.dbytes",    "dBytes",    base.DEC)
local f_spkts     = ProtoField.uint8 ("bnn_features.spkts",     "sPkts",     base.DEC)
local f_dpkts     = ProtoField.uint8 ("bnn_features.dpkts",     "dPkts",     base.DEC)
local f_smeansz   = ProtoField.uint16("bnn_features.smeansz",   "sMeanSz",   base.DEC)
local f_dmeansz   = ProtoField.uint16("bnn_features.dmeansz",   "dMeanSz",   base.DEC)
local f_smaxbytes = ProtoField.uint16("bnn_features.smaxbytes", "sMaxBytes", base.DEC)
local f_dmaxbytes = ProtoField.uint16("bnn_features.dmaxbytes", "dMaxBytes", base.DEC)
local f_sminbytes = ProtoField.uint16("bnn_features.sminbytes", "sMinBytes", base.DEC)
local f_dminbytes = ProtoField.uint16("bnn_features.dminbytes", "dMinBytes", base.DEC)
local f_fin_cnt   = ProtoField.uint8 ("bnn_features.fin_cnt",   "FIN Count", base.DEC)
local f_syn_cnt   = ProtoField.uint8 ("bnn_features.syn_cnt",   "SYN Count", base.DEC)
local f_ack_cnt   = ProtoField.uint8 ("bnn_features.ack_cnt",   "ACK Count", base.DEC)
local f_psh_cnt   = ProtoField.uint8 ("bnn_features.psh_cnt",   "PSH Count", base.DEC)
local f_rst_cnt   = ProtoField.uint8 ("bnn_features.rst_cnt",   "RST Count", base.DEC)
local f_ece_cnt   = ProtoField.uint8 ("bnn_features.ece_cnt",   "ECE Count", base.DEC)

-- Computed field: total TCP flags
local f_flags_total = ProtoField.uint16("bnn_features.flags_total", "TCP Flags Total", base.DEC)

bnn.fields = {
    f_sbytes, f_dbytes, f_spkts, f_dpkts,
    f_smeansz, f_dmeansz,
    f_smaxbytes, f_dmaxbytes, f_sminbytes, f_dminbytes,
    f_fin_cnt, f_syn_cnt, f_ack_cnt, f_psh_cnt, f_rst_cnt, f_ece_cnt,
    f_flags_total
}

function bnn.dissector(buf, pinfo, tree)
    -- Header size: 10*2 + 6*1 = 26 bytes
    if buf:len() < 26 then return end

    pinfo.cols.protocol = "BNN_FEATURES"
    local t = tree:add(bnn, buf(), "BNN Features Header")

    local o = 0

    -- Byte statistics (16-bit fields)
    t:add(f_sbytes,    buf(o, 2)); o = o + 2
    t:add(f_dbytes,    buf(o, 2)); o = o + 2

    -- Packet counts (8-bit fields)
    t:add(f_spkts,     buf(o, 1)); o = o + 1
    t:add(f_dpkts,     buf(o, 1)); o = o + 1

    -- Mean sizes (16-bit fields, computed by CP)
    t:add(f_smeansz,   buf(o, 2)); o = o + 2
    t:add(f_dmeansz,   buf(o, 2)); o = o + 2

    -- Max/Min bytes (16-bit fields)
    t:add(f_smaxbytes, buf(o, 2)); o = o + 2
    t:add(f_dmaxbytes, buf(o, 2)); o = o + 2
    t:add(f_sminbytes, buf(o, 2)); o = o + 2
    t:add(f_dminbytes, buf(o, 2)); o = o + 2

    -- TCP flag counters (8-bit fields each)
    local flags_sub = t:add(buf(o, 6), "TCP Flag Counters")
    local fin = buf(o, 1):uint();     flags_sub:add(f_fin_cnt, buf(o, 1)); o = o + 1
    local syn = buf(o, 1):uint();     flags_sub:add(f_syn_cnt, buf(o, 1)); o = o + 1
    local ack = buf(o, 1):uint();     flags_sub:add(f_ack_cnt, buf(o, 1)); o = o + 1
    local psh = buf(o, 1):uint();     flags_sub:add(f_psh_cnt, buf(o, 1)); o = o + 1
    local rst = buf(o, 1):uint();     flags_sub:add(f_rst_cnt, buf(o, 1)); o = o + 1
    local ece = buf(o, 1):uint();     flags_sub:add(f_ece_cnt, buf(o, 1)); o = o + 1

    -- Total TCP flags count
    local total = fin + syn + ack + psh + rst + ece
    flags_sub:add(f_flags_total, total):set_generated()
end

-- Register to ethertype 0x2324 (FEATURE_COLLECTOR_PKT_ETYPE)
DissectorTable.get("ethertype"):add(0x2324, bnn)
