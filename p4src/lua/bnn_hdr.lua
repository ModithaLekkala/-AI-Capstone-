-- bnn_eth.lua — Wireshark dissector for "BNN_pkt" carried directly over Ethernet (ethertype 0x2323)

-- === Protocol & fields ===
local bnn_proto = Proto("bnn", "BNN Packet")

local f_layer_no   = ProtoField.uint8 ("bnn.layer_no",   "Layer No")
local f_l0_out     = ProtoField.uint32("bnn.l0_out",     "L0 Output")
local f_l1_out     = ProtoField.uint8 ("bnn.l1_out",     "L1 Output")
local f_l2_out     = ProtoField.uint8 ("bnn.l2_out",     "L2 Output")

local f_pop_recirc = ProtoField.uint8 ("bnn.pop_recirc", "Pop Recirc")
local f_nrs_recirc = ProtoField.uint8 ("bnn.nrs_recirc", "NRS Recirc")

local f_pop1       = ProtoField.uint8 ("bnn.pop1",       "Pop1")
local f_pop2       = ProtoField.uint8 ("bnn.pop2",       "Pop2")
local f_pop3       = ProtoField.uint8 ("bnn.pop3",       "Pop3")
local f_pop4       = ProtoField.uint8 ("bnn.pop4",       "Pop4")

local f_payload    = ProtoField.bytes ("bnn.payload",    "BNN Payload")

bnn_proto.fields = {
  f_layer_no, f_l0_out, f_l1_out, f_l2_out,
  f_pop_recirc, f_nrs_recirc,
  f_pop1, f_pop2, f_pop3, f_pop4,
  f_payload
}

local BNN_LEN = 13 -- fixed header size in bytes

-- === Dissector ===
function bnn_proto.dissector(tvb, pinfo, tree)
  local len = tvb:len()
  if len < BNN_LEN then return end

  pinfo.cols.protocol = "BNN"

  local t = tree:add(bnn_proto, tvb(0, math.min(len, BNN_LEN)), "BNN Header")

  t:add(f_layer_no,   tvb(0,1))
  t:add(f_l0_out,     tvb(1,4))
  t:add(f_l1_out,     tvb(5,1))
  t:add(f_l2_out,     tvb(6,1))

  t:add(f_pop_recirc, tvb(7,1))
  t:add(f_nrs_recirc, tvb(8,1))

  t:add(f_pop1,       tvb(9,1))
  t:add(f_pop2,       tvb(10,1))
  t:add(f_pop3,       tvb(11,1))
  t:add(f_pop4,       tvb(12,1))

  local remain = len - BNN_LEN
  if remain > 0 then
    tree:add(f_payload, tvb(BNN_LEN, remain))
  end
end

-- === Registration (EtherType 0x2323) ===
DissectorTable.get("ethertype"):add(0x2323, bnn_proto)
