-- bnn_eth.lua — Wireshark dissector for "BNN_pkt" over Ethernet (ethertype 0x2323)

-- === Protocol & fields ===
local bnn_proto = Proto("bnn", "BNN Packet")

local f_layer_no     = ProtoField.uint8 ("bnn.layer_no",     "Layer No")

-- l0_out is 42 bits followed by 6-bit padding in a total of 6 bytes
-- We'll decode it and show l0_out as an 11-hex-digit string (42 bits) plus padding (0..63)
local f_l0_out_hex   = ProtoField.string("bnn.l0_out",       "L0 Output (42b, hex)")
local f_padding6     = ProtoField.uint8 ("bnn.padding6",     "Padding (6b)", base.DEC)

local f_l1_out       = ProtoField.uint8 ("bnn.l1_out",       "L1 Output")

local f_pop_recirc   = ProtoField.uint8 ("bnn.pop_recirc",   "Pop Recirc")
local f_nrs_recirc   = ProtoField.uint8 ("bnn.nrs_recirc",   "NRS Recirc")

local f_pop1         = ProtoField.uint8 ("bnn.pop1",         "Pop1")
local f_pop2         = ProtoField.uint8 ("bnn.pop2",         "Pop2")
local f_pop3         = ProtoField.uint8 ("bnn.pop3",         "Pop3")
local f_pop4         = ProtoField.uint8 ("bnn.pop4",         "Pop4")
local f_pop5         = ProtoField.uint8 ("bnn.pop5",         "Pop5")
local f_pop6         = ProtoField.uint8 ("bnn.pop6",         "Pop6")
local f_pop7         = ProtoField.uint8 ("bnn.pop7",         "Pop7")

local f_input_offset = ProtoField.uint16("bnn.input_offset", "Input Offset", base.HEX)

local f_payload      = ProtoField.bytes ("bnn.payload",      "BNN Payload")

bnn_proto.fields = {
  f_layer_no,
  f_l0_out_hex, f_padding6,
  f_l1_out,
  f_pop_recirc, f_nrs_recirc,
  f_pop1, f_pop2, f_pop3, f_pop4, f_pop5, f_pop6, f_pop7,
  f_input_offset,
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
local BNN_LEN = 19

-- helper: 16-bit masks/shifts (use bit32; Wireshark Lua uses Lua 5.2)
local band  = bit32.band
local bor   = bit32.bor
local lsh   = bit32.lshift
local rsh   = bit32.rshift

-- === Dissector ===
function bnn_proto.dissector(tvb, pinfo, tree)
  local len = tvb:len()
  if len < BNN_LEN then return end

  pinfo.cols.protocol = "BNN"

  local hdr = tree:add(bnn_proto, tvb(0, BNN_LEN), "BNN Header")

  -- Byte 0
  hdr:add(f_layer_no, tvb(0,1))

  -- Bytes 1..6: 48 bits total = l0_out (42) + padding (6)
  local H = tvb(1,2):uint()   -- bytes 1-2
  local M = tvb(3,2):uint()   -- bytes 3-4
  local L = tvb(5,2):uint()   -- bytes 5-6

  -- Right-shift the 48-bit value by 6 to drop the padding (LSB side)
  -- Represent the 42-bit value as three chunks: 10b | 16b | 16b
  local hi10   = rsh(H, 6)                                      -- top 10 bits
  local mid16  = bor(lsh(band(H, 0x003F), 10), rsh(M, 6))       -- next 16
  local low16  = bor(lsh(band(M, 0x003F), 10), rsh(L, 6))       -- last 16
  local padding6 = band(L, 0x003F)                              -- low 6 bits

  -- Render the 42-bit value as 11 hex digits: 10+16+16 bits → 3+4+4 hex digits
  local l0_hex = string.format("%03x%04x%04x", hi10, mid16, low16):gsub("^0+(%x)","%1")
  if l0_hex == "" then l0_hex = "0" end
  hdr:add(f_l0_out_hex, tvb(1,6)):set_text("L0 Output (42b): 0x" .. l0_hex)
  hdr:add(f_padding6, tvb(5,2)):set_text(string.format("Padding (6b): %d", padding6))

  -- Byte 7
  hdr:add(f_l1_out, tvb(7,1))

  -- Bytes 8..9
  hdr:add(f_pop_recirc, tvb(8,1))
  hdr:add(f_nrs_recirc, tvb(9,1))

  -- Bytes 10..16
  hdr:add(f_pop1, tvb(10,1))
  hdr:add(f_pop2, tvb(11,1))
  hdr:add(f_pop3, tvb(12,1))
  hdr:add(f_pop4, tvb(13,1))
  hdr:add(f_pop5, tvb(14,1))
  hdr:add(f_pop6, tvb(15,1))
  hdr:add(f_pop7, tvb(16,1))

  -- Bytes 17..18
  hdr:add(f_input_offset, tvb(17,2))

  -- Any remaining payload after the fixed header
  local remain = len - BNN_LEN
  if remain > 0 then
    tree:add(f_payload, tvb(BNN_LEN, remain))
  end
end

-- === Registration (EtherType 0x2323) ===
DissectorTable.get("ethertype"):add(0x2323, bnn_proto)
