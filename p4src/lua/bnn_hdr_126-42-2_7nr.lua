-- bnn_eth.lua — Wireshark dissector for "BNN_pkt" over Ethernet (ethertype 0x2323)

-- === Protocol & fields ===
local bnn_proto = Proto("bnn", "BNN Packet")

local f_layer_no     = ProtoField.uint8 ("bnn.layer_no",     "Layer No")

-- l0_out is 42 bits followed by 6-bit padding in a total of 6 bytes
-- We'll decode it and show l0_out as an 11-hex-digit string (42 bits) plus padding (0..63)
local f_l0_out1   = ProtoField.uint8("bnn.l0_out_1",       "L0 Output 1")
local f_l0_out2   = ProtoField.uint8("bnn.l0_out_2",       "L0 Output 2")
local f_l0_out3   = ProtoField.uint8("bnn.l0_out_3",       "L0 Output 3")
local f_l0_out4   = ProtoField.uint8("bnn.l0_out_4",       "L0 Output 4")
local f_l0_out5   = ProtoField.uint8("bnn.l0_out_5",       "L0 Output 5")
local f_l0_out6   = ProtoField.uint8("bnn.l0_out_6",       "L0 Output 6")

local f_l1_out       = ProtoField.uint8 ("bnn.l1_out",       "L1 Output")

local f_input_offset = ProtoField.uint16("bnn.input_offset", "Input Offset", base.DEC)
local f_input_offset_cp = ProtoField.uint16("bnn.input_offset_cp", "Input Offset copy", base.DEC)

local f_pop_recirc   = ProtoField.uint8 ("bnn.pop_recirc",   "Pop Recirc")
local f_nrs_recirc   = ProtoField.uint8 ("bnn.nrs_recirc",   "NRS Recirc")

local f_pop1         = ProtoField.uint8 ("bnn.pop1",         "Pop1")
local f_pop2         = ProtoField.uint8 ("bnn.pop2",         "Pop2")
local f_pop3         = ProtoField.uint8 ("bnn.pop3",         "Pop3")
local f_pop4         = ProtoField.uint8 ("bnn.pop4",         "Pop4")
local f_pop5         = ProtoField.uint8 ("bnn.pop5",         "Pop5")
local f_pop6         = ProtoField.uint8 ("bnn.pop6",         "Pop6")
local f_pop7         = ProtoField.uint8 ("bnn.pop7",         "Pop7")

local f_payload      = ProtoField.bytes ("bnn.payload",      "BNN Payload")

bnn_proto.fields = {
  f_layer_no,
  f_l0_out1,
  f_l0_out2,
  f_l0_out3,
  f_l0_out4,
  f_l0_out5,
  f_l0_out6,
  f_l1_out,
  f_input_offset,
  f_input_offset_cp,
  f_pop_recirc, f_nrs_recirc,
  f_pop1, f_pop2, f_pop3, f_pop4, f_pop5, f_pop6, f_pop7,
  f_payload
}

-- Fixed header layout/length (bytes):
-- 0: layer_no (1)
-- 1..6: l0_out (42 bits) + padding (6 bits)  -> 6 bytes total
-- 7: l1_out (1)
-- 8: pop_recirc (1)
-- 9: nrs_recirc (1)
-- 10..16: pop1..pop7 (7)
-- 17..18: input_offset (2)
local BNN_LEN = 24

function bnn_proto.dissector(tvb, pinfo, tree)
  local len = tvb:len()
  if len < BNN_LEN then return end

  pinfo.cols.protocol = "BNN"

  local t = tree:add(bnn_proto, tvb(0, math.min(len, BNN_LEN)), "BNN Header")

  t:add(f_layer_no,    tvb(0,1))
  t:add(f_l0_out1,     tvb(1,1))
  t:add(f_l0_out2,     tvb(2,1))
  t:add(f_l0_out3,     tvb(3,1))
  t:add(f_l0_out4,     tvb(4,1))
  t:add(f_l0_out5,     tvb(5,1))
  t:add(f_l0_out6,     tvb(6,1))

  t:add(f_l1_out,      tvb(7,1))

  t:add(f_input_offset,        tvb(8,2))
  t:add(f_input_offset_cp,     tvb(10,2))

  t:add(f_pop_recirc, tvb(12,2))
  t:add(f_nrs_recirc, tvb(14,2))

  t:add(f_pop1,       tvb(16,1))
  t:add(f_pop2,       tvb(17,1))
  t:add(f_pop3,       tvb(18,1))
  t:add(f_pop4,       tvb(19,1))
  t:add(f_pop5,       tvb(20,1))
  t:add(f_pop6,       tvb(21,1))
  t:add(f_pop7,       tvb(22,1))

  local remain = len - BNN_LEN
  if remain > 0 then
    tree:add(f_payload, tvb(BNN_LEN, remain))
  end
end

-- === Registration (EtherType 0x2323) ===
DissectorTable.get("ethertype"):add(0x2323, bnn_proto)
