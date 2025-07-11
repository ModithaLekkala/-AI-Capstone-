import numpy as np 
from pycommon import hex_input, hex_w, nn, hex_w2

def generate_16bit_hex():
    """
    Yields (binary16, hex4, popcount_hex1) for all values 1..(2^16−2).
    """
    for i in range(1, (1 << 16) - 1):
        bin_str = format(i, '016b')    # 16-bit binary
        hex_str = format(i, '04X')     # 4-digit uppercase hex
        popcnt  = format(bin(i).count('1'), '01X')
        yield bin_str, hex_str, popcnt

def cover_range_with_prefixes(start, end, width):
    """
    Return list of (value, mask) pairs whose ternary masks cover [start..end].
    """
    prefixes = []
    cur = start
    while cur <= end:
        blk = 1
        # grow block while aligned and within end
        while (cur & blk) == 0 and cur + (blk << 1) - 1 <= end:
            blk <<= 1
        mask = (~(blk - 1)) & ((1 << width) - 1)
        prefixes.append((cur, mask))
        cur += blk
    return prefixes


# -------------------------------------------------
#  1) Grab references to P4-generated table + register objects
# -------------------------------------------------
p4            = bfrt.tofino_mlp_prep.pipe
pop1          = p4.Ingress.pop1
pop2          = p4.Ingress.pop2
pop3          = p4.Ingress.pop3
pop4          = p4.Ingress.pop4
pop5          = p4.Ingress.pop5
pop6          = p4.Ingress.pop6
pop7          = p4.Ingress.pop7
pop8          = p4.Ingress.pop8

l0_weights    = p4.Ingress.l0_weights   # SINGLE table, two-key: (weight_batch, neuron_batch)
l1_weights    = p4.Ingress.l1_weights   

bnn_input_reg = p4.Ingress.bnn_input_reg

eb            = p4.Ingress.egress_behaviour


# -------------------------------------------------
#  2) Populate the sixteen “popcount” tables (pop1..pop16)
#     We insert all 65 534 possible 16-bit keys → 1-hex-digit popcount
# -------------------------------------------------
# for _, hex4, popcnt in generate_16bit_hex():
#     pop1.add_with_pop_act1(f'0x{hex4}', f'0x{popcnt}')
#     pop2.add_with_pop_act2(f'0x{hex4}', f'0x{popcnt}')
#     pop3.add_with_pop_act3(f'0x{hex4}', f'0x{popcnt}')
#     pop4.add_with_pop_act4(f'0x{hex4}', f'0x{popcnt}')
#     pop5.add_with_pop_act5(f'0x{hex4}', f'0x{popcnt}')
#     pop6.add_with_pop_act6(f'0x{hex4}', f'0x{popcnt}')
#     pop7.add_with_pop_act7(f'0x{hex4}', f'0x{popcnt}')
#     pop8.add_with_pop_act8(f'0x{hex4}', f'0x{popcnt}')

print("→ Done loading pop1..pop16 (all 16-bit keys → 1-hex-digit popcount).")


# -------------------------------------------------
#  L0 WEIGHTS TABLE LOGIC 
# -------------------------------------------------
print('POPULATE L0 WEIGHTS TABLE')
parallel_bit_cap = (16//4)
parallel_neurons_cap = 8

assert len(hex_w) == nn[1], \
    'weight no. different from neurons no. they must match'

num_neuron_batches  = nn[1] // parallel_neurons_cap #2
weight_batches_no = len(hex_w[0]) // parallel_bit_cap #8

assert len(hex_w) == parallel_neurons_cap * num_neuron_batches, \
       "hex_w length must equal num_weight_batches * num_neuron_batches"

w_mx = np.zeros((weight_batches_no, len(hex_w))).tolist()
for ix, w in enumerate(hex_w):
    chunks = [w[i:i+4] for i in range(0, len(w), 4)]
    for jx, chunk in enumerate(chunks):
        w_mx[jx][ix] = chunk

# push weight into weight table l0
for j in range(num_neuron_batches):
    for ix in range(weight_batches_no):
        base = parallel_neurons_cap * j

        w1 = w_mx[ix]

        (w0,  w1,  w2,  w3,
         w4,  w5,  w6,  w7) = w1[base: base+parallel_neurons_cap]

        print(
            f"l0_weights.add_with_get_weights("
            f"weight_batch={ix}, neuron_batch={j}, "
            f"w0=0x{w0},w1=0x{w1},w2=0x{w2},w3=0x{w3},"
            f"w4=0x{w4},w5=0x{w5},w6=0x{w6},w7=0x{w7},"
            f")"
        )

        l0_weights.add_with_get_weights(
            f"{ix}",           # key “weight_batch”
            f"{j}",            # key “neuron_batch”
            f"0x{w0}",         # bit<16> nr1_w
            f"0x{w1}",         # bit<16> nr2_w
            f"0x{w2}",         # bit<16> nr3_w
            f"0x{w3}",         # bit<16> nr4_w
            f"0x{w4}",         # bit<16> nr5_w
            f"0x{w5}",         # bit<16> nr6_w
            f"0x{w6}",         # bit<16> nr7_w
            f"0x{w7}",         # bit<16> nr8_w
        )

print("→ Done loading all 128-bit weights into l0_weights (two-key table).\n")

# -------------------------------------------------
#  L1 WEIGHTS TABLE LOGIC 
# -------------------------------------------------
print('POPULATE L1 WEIGHTS TABLE')
assert len(hex_w2) == nn[2], \
    'l1 weight no. different from neurons no. they must match'

num_neuron_batches  = nn[2] // parallel_neurons_cap #2
weight_batches_no = len(hex_w2[0]) // parallel_bit_cap #8

assert len(hex_w2) == parallel_neurons_cap * num_neuron_batches, \
       "hex_w2 length must equal num_weight_batches * num_neuron_batches"

w_mx = np.zeros((weight_batches_no, len(hex_w2))).tolist()
for ix, w in enumerate(hex_w2):
    chunks = [w[i:i+4] for i in range(0, len(w), 4)]
    for jx, chunk in enumerate(chunks):
        w_mx[jx][ix] = chunk

# push weight into weight table l0
for j in range(num_neuron_batches):
    for ix in range(weight_batches_no):
        base = parallel_neurons_cap * j

        w1 = w_mx[ix]

        (w0,  w1,  w2,  w3,
         w4,  w5,  w6,  w7) = w1[base: base+parallel_neurons_cap]

        print(
            f"l1_weights.add_with_get_weights("
            f"weight_batch={ix}, neuron_batch={j}, "
            f"w0=0x{w0},w1=0x{w1},w2=0x{w2},w3=0x{w3},"
            f"w4=0x{w4},w5=0x{w5},w6=0x{w6},w7=0x{w7},"
            f")"
        )

        l1_weights.add_with_get_weights(
            f"{ix}",           
            f"{j}",            
            f"0x{w0}",         
            f"0x{w1}",         
            f"0x{w2}",         
            f"0x{w3}",         
            f"0x{w4}",         
            f"0x{w5}",         
            f"0x{w6}",         
            f"0x{w7}",         
        )

print("→ Done loading all 32-bit weights into l1_weights (two-key table).\n")



# -------------------------------------------------
#  5) Finally, split a single 256-bit “hex_input” into sixteen 16-bit chunks
#     and write them into bnn_input_reg[0..15].
# -------------------------------------------------
# hex_input = "e51411243381365b9ea36fbeedd94689"
assert len(hex_input) == 32, "hex_input must be exactly 32 hex digits"

# Make sixteen 4-digit substrings:
input_chunks = [ hex_input[i : i + 4] for i in range(0, 32, 4) ]

for idx, piece in enumerate(input_chunks):
    print(f"bnn_input_reg.add({idx}, 0x{piece})")
    bnn_input_reg.add(idx, f"0x{piece}")

print("→ Done loading the 128-bit input into register slots 0..7.")

# your constants:
WIDTH = {0: 8, 1: 2}
HEIGHT= {0: 4,1: 1}
BW_POP = 8    # e.g. 3
BW_NRS = 8    # e.g. 2 or 3

for layer in (0,1):
    # 1) pop_recirc < WIDTH[layer]
    for val, m in cover_range_with_prefixes(0, WIDTH[layer]-1, BW_POP):
        eb.add_with_pop_recirc(
            layer_no           = layer,
            pop_recirc         = val,
            pop_recirc_mask    = m,
            nrs_recirc         = 0,
            nrs_recirc_mask    = (1<<BW_NRS)-1
        )

        print(
            f'eb.add_with_pop_recirc( '
            f'layer_no           = {layer}, '
            f'pop_recirc         = {val}, '
            f'pop_recirc_mask    = {m},'
            f'nrs_recirc         = {0}, '
            f'nrs_recirc_mask    = {(1<<BW_NRS)-1} )'
        )

    # 2) WIDTH[layer] <= pop_recirc AND nrs_recirc < HEIGHT[layer]
    for val_n, m_n in cover_range_with_prefixes(0, HEIGHT[layer]-1, BW_NRS):
        eb.add_with_nrs_recirc(
            layer_no           = layer,
            pop_recirc         = WIDTH[layer],
            pop_recirc_mask    = (1<<BW_POP)-1,
            nrs_recirc         = val_n,
            nrs_recirc_mask    = m_n
        )
        print(
            f'eb.add_with_nrs_recirc('
            f'layer_no           = {layer},'
            f'pop_recirc         = {WIDTH[layer]},'
            f'pop_recirc_mask    = {(1<<BW_POP)-1},'
            f'nrs_recirc         = {val_n},'
            f'nrs_recirc_mask    = {m_n} )'
        )

    # 3) final else: pop_recirc == WIDTH AND nrs_recirc == HEIGHT
    act = eb.add_with_to_next_layer if layer == 0 else eb.add_with_send_back
    act(
        layer_no           = layer,
        pop_recirc         = WIDTH[layer],
        pop_recirc_mask    = (1<<BW_POP)-1,
        nrs_recirc         = HEIGHT[layer],
        nrs_recirc_mask    = (1<<BW_NRS)-1
    )

    print(
        f'act(layer_no           = {layer}, '
        f'pop_recirc         = {WIDTH[layer]},'
        f'pop_recirc_mask    = {(1<<BW_POP)-1},'
        f'nrs_recirc         = {HEIGHT[layer]},'
        f'nrs_recirc_mask    = {(1<<BW_NRS)-1})'
    )

    print("→ Done loading the egress behaviour table.")
