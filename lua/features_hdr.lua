-- Define protocol
bnn_proto = Proto("features", "BNN Feature Header")

-- Define fields
local f_sttl   = ProtoField.uint8("features.sttl",   "sTTL")
local f_dttl   = ProtoField.uint8("features.dttl",   "dTTL")
local f_sbytes = ProtoField.uint16("features.sbytes","sBytes")
local f_dbytes = ProtoField.uint16("features.dbytes","dBytes")
local f_smean  = ProtoField.uint16("features.smean", "sMean")
local f_dmean  = ProtoField.uint16("features.dmean", "dMean")
local f_spkts  = ProtoField.uint16("features.spkts", "sPkts")
local f_dpkts  = ProtoField.uint16("features.dpkts", "dPkts")
local f_synack = ProtoField.uint8("features.synack", "SynAck")
local f_ackdat = ProtoField.uint8("features.ackdat", "AckDat")

bnn_proto.fields = {
    f_sttl, f_dttl, f_sbytes, f_dbytes,
    f_smean, f_dmean, f_spkts, f_dpkts,
    f_synack, f_ackdat
}

-- Dissector function
function bnn_proto.dissector(buffer, pinfo, tree)
    if buffer:len() < 16 then return end

    pinfo.cols.protocol = "BNNFeature"
    local subtree = tree:add(bnn_proto, buffer(), "BNN Feature Header")

    subtree:add(f_sttl,   buffer(0,1))
    subtree:add(f_dttl,   buffer(1,1))
    subtree:add(f_sbytes, buffer(2,2))
    subtree:add(f_dbytes, buffer(4,2))
    subtree:add(f_smean,  buffer(6,2))
    subtree:add(f_dmean,  buffer(8,2))
    subtree:add(f_spkts,  buffer(10,2))
    subtree:add(f_dpkts,  buffer(12,2))
    subtree:add(f_synack, buffer(14,1))
    subtree:add(f_ackdat, buffer(15,1))
end

DissectorTable.get("ethertype"):add(0x2324, bnn_proto)

