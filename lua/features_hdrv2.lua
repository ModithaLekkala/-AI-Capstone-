-- bnn_input.lua — dissector aligned to Scapy BNNFeaturesHeader
-- class BNNFeaturesHeader(Packet):
--     name = "bnn_input_h"
--     fields_desc = [
--         ShortField("sbytes", 0),
--         ShortField("dbytes", 0),
--         ByteField("spkts",  0),
--         ByteField("dpkts",  0),
--         ShortField("smean",  0),
--         ShortField("dmean",  0),
--         ShortField("smaxbytes",  0),
--         ShortField("dmaxbytes",  0),
--         ShortField("sminbytes",  0),
--         ShortField("dminbytes",  0),
--         BitField("fin_cnt",  0, 4),
--         BitField("syn_cnt",  0, 4),
--         BitField("ack_cnt",  0, 4),
--         BitField("psh_cnt",  0, 4),
--         BitField("rst_cnt",  0, 4),
--         BitField("ece_cnt",  0, 4)
--     ]

local bnn = Proto("bnn_input", "BNN Input Header")

-- 16-bit & 8-bit fields (big-endian network order)
local f_sbytes    = ProtoField.uint16("bnn_input.sbytes",    "sBytes")
local f_dbytes    = ProtoField.uint16("bnn_input.dbytes",    "dBytes")
local f_spkts     = ProtoField.uint8 ("bnn_input.spkts",     "sPkts")
local f_dpkts     = ProtoField.uint8 ("bnn_input.dpkts",     "dPkts")
local f_smean     = ProtoField.uint16("bnn_input.smean",     "sMean")
local f_dmean     = ProtoField.uint16("bnn_input.dmean",     "dMean")
local f_smaxbytes = ProtoField.uint16("bnn_input.smaxbytes", "sMaxBytes")
local f_dmaxbytes = ProtoField.uint16("bnn_input.dmaxbytes", "dMaxBytes")
local f_sminbytes = ProtoField.uint16("bnn_input.sminbytes", "sMinBytes")
local f_dminbytes = ProtoField.uint16("bnn_input.dminbytes", "dMinBytes")

-- 4-bit counters packed in 3 bytes (Scapy order):
-- Byte A: fin (hi nibble), syn (lo nibble)
-- Byte B: ack (hi), psh (lo)
-- Byte C: rst (hi), ece (lo)
local f_fin_cnt = ProtoField.uint8("bnn_input.fin_cnt", "FIN Count", base.DEC, nil, 0xF0)
local f_syn_cnt = ProtoField.uint8("bnn_input.syn_cnt", "SYN Count", base.DEC, nil, 0x0F)
local f_ack_cnt = ProtoField.uint8("bnn_input.ack_cnt", "ACK Count", base.DEC, nil, 0xF0)
local f_psh_cnt = ProtoField.uint8("bnn_input.psh_cnt", "PSH Count", base.DEC, nil, 0x0F)
local f_rst_cnt = ProtoField.uint8("bnn_input.rst_cnt", "RST Count", base.DEC, nil, 0xF0)
local f_ece_cnt = ProtoField.uint8("bnn_input.ece_cnt", "ECE Count", base.DEC, nil, 0x0F)

-- Aggregate: sum of all six counters (fits in 16 bits)
local f_flags_total = ProtoField.uint16("bnn_input.flags_total", "TCP Flags Count (sum)", base.DEC)

bnn.fields = {
  f_sbytes, f_dbytes, f_spkts, f_dpkts, f_smean, f_dmean,
  f_smaxbytes, f_dmaxbytes, f_sminbytes, f_dminbytes,
  f_fin_cnt, f_syn_cnt, f_ack_cnt, f_psh_cnt, f_rst_cnt, f_ece_cnt,
  f_flags_total
}

function bnn.dissector(buf, pinfo, tree)
  -- size check:
  -- 2+2 +1+1 +2+2 +2+2+2+2 +3 = 21 bytes minimum
  if buf:len() < 21 then return end

  pinfo.cols.protocol = "BNN_INPUT"
  local t  = tree:add(bnn, buf(), "BNN Input Header")

  local o = 0
  t:add(f_sbytes,    buf(o,2)); o=o+2
  t:add(f_dbytes,    buf(o,2)); o=o+2
  t:add(f_spkts,     buf(o,1)); o=o+1
  t:add(f_dpkts,     buf(o,1)); o=o+1
  t:add(f_smean,     buf(o,2)); o=o+2
  t:add(f_dmean,     buf(o,2)); o=o+2
  t:add(f_smaxbytes, buf(o,2)); o=o+2
  t:add(f_dmaxbytes, buf(o,2)); o=o+2
  t:add(f_sminbytes, buf(o,2)); o=o+2
  t:add(f_dminbytes, buf(o,2)); o=o+2

  -- 3 bytes of counters
  local A = buf(o,1):uint();   -- fin/syn
  local B = buf(o+1,1):uint(); -- ack/psh
  local C = buf(o+2,1):uint(); -- rst/ece

  -- Show individual counters (aligned with Scapy packing)
  local flags_sub = t:add(buf(o,3), "TCP Flag Counters (packed)")
  flags_sub:add(f_fin_cnt, buf(o,1))
  flags_sub:add(f_syn_cnt, buf(o,1))
  flags_sub:add(f_ack_cnt, buf(o+1,1))
  flags_sub:add(f_psh_cnt, buf(o+1,1))
  flags_sub:add(f_rst_cnt, buf(o+2,1))
  flags_sub:add(f_ece_cnt, buf(o+2,1))

  -- Extract nibbles
  local fin = bit.rshift(bit.band(A, 0xF0), 4)
  local syn = bit.band(A, 0x0F)
  local ack = bit.rshift(bit.band(B, 0xF0), 4)
  local psh = bit.band(B, 0x0F)
  local rst = bit.rshift(bit.band(C, 0xF0), 4)
  local ece = bit.band(C, 0x0F)

  -- Aggregate (sum) into a 16-bit field
  local total = fin + syn + ack + psh + rst + ece
  flags_sub:add(f_flags_total, total)

  o = o + 3
end

-- Register to your Ethertype (and SLL if you capture on cooked interfaces)
DissectorTable.get("ethertype"):add(0x2324, bnn)
-- DissectorTable.get("sll.ltype"):add(0x2324, bnn)
