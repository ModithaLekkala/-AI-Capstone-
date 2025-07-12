import numpy as np 
from pycommon import hex_input, hex_w, nn, hex_w2, hex_w3

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
p4            = bfrt.tofino_mlp_prep.inethynn
pop1          = p4.Ingress.pop1
pop2          = p4.Ingress.pop2
pop3          = p4.Ingress.pop3
pop4          = p4.Ingress.pop4

l0_weights    = p4.Ingress.l0_weights   # SINGLE table, two-key: (weight_batch, neuron_batch)
l1_weights    = p4.Ingress.l1_weights   

bnn_input_reg = p4.Ingress.bnn_input_reg

eb            = p4.Ingress.egress_behaviour


# -------------------------------------------------
#  2) Populate the sixteen “popcount” tables (pop1..pop16)
#     We insert all 65 534 possible 16-bit keys → 1-hex-digit popcount
# -------------------------------------------------
for _, hex4, popcnt in generate_16bit_hex():
    pop1.add_with_pop_act1(f'0x{hex4}', f'0x{popcnt}')
    pop2.add_with_pop_act2(f'0x{hex4}', f'0x{popcnt}')
    pop3.add_with_pop_act3(f'0x{hex4}', f'0x{popcnt}')
    pop4.add_with_pop_act4(f'0x{hex4}', f'0x{popcnt}')

print("→ Done loading pop1..pop16 (all 16-bit keys → 1-hex-digit popcount).")


# -------------------------------------------------
#  L0 WEIGHTS TABLE LOGIC 
# -------------------------------------------------
print('POPULATE L0 WEIGHTS TABLE')
parallel_bit_cap = (16//4)
parallel_neurons_cap = 4

assert len(hex_w) == nn[1], \
    'weight no. different from neurons no. they must match'

num_neuron_batches  = nn[1] // parallel_neurons_cap
weight_batches_no = len(hex_w[0]) // parallel_bit_cap

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

        (w0,  w1,  w2,  w3) = w1[base: base+parallel_neurons_cap]

        print(
            f"l0_weights.add_with_get_weights("
            f"weight_batch={ix}, neuron_batch={j}, "
            f"w0=0x{w0},w1=0x{w1},w2=0x{w2},w3=0x{w3},"
            f")"
        )

        l0_weights.add_with_get_weights(
            f"{ix}",           # key “weight_batch”
            f"{j}",            # key “neuron_batch”
            f"0x{w0}",         # bit<16> nr1_w
            f"0x{w1}",         # bit<16> nr2_w
            f"0x{w2}",         # bit<16> nr3_w
            f"0x{w3}",         # bit<16> nr4_w
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

        (w0,  w1,  w2,  w3) = w1[base: base+parallel_neurons_cap]

        print(
            f"l1_weights.add_with_get_weights("
            f"weight_batch={ix}, neuron_batch={j}, "
            f"w0=0x{w0},w1=0x{w1},w2=0x{w2},w3=0x{w3},"
            f")"
        )

        l1_weights.add_with_get_weights(
            f"{ix}",           
            f"{j}",            
            f"0x{w0}",         
            f"0x{w1}",         
            f"0x{w2}",         
            f"0x{w3}",         
        )

print("→ Done loading all 32-bit weights into l1_weights (two-key table).\n")

# -------------------------------------------------
#  L2 (FINAL) WEIGHTS TABLE LOGIC 
# -------------------------------------------------
print('POPULATE L2 WEIGHTS TABLE')
# this layer has 2 neurons → we batch 2 at a time
parallel_neurons_cap3 = 2      # two output neurons
parallel_bit_cap3     = 2      # each weight is 2 hex digits (8 bits)

# must match nn[3] == len(hex_w3)
assert len(hex_w3) == nn[3], 'hex_w3 length must equal number of final neurons'

num_neuron_batches3 = nn[3] // parallel_neurons_cap3  # 2//2 == 1
weight_batches_no3  = len(hex_w3[0]) // parallel_bit_cap3
assert len(hex_w3[0]) % parallel_bit_cap3 == 0

# build a matrix so w_mx3[batch][neuron] == that 2-digit chunk
w_mx3 = np.zeros((weight_batches_no3, len(hex_w3)), dtype=object).tolist()
for ix, w in enumerate(hex_w3):
    # split into 2-char chunks: here just one chunk per string
    chunks = [ w[i:i+parallel_bit_cap3] for i in range(0, len(w), parallel_bit_cap3) ]
    for jx, chunk in enumerate(chunks):
        w_mx3[jx][ix] = chunk

# get BFRT handle for the new table
l2_weights = p4.Ingress.l2_weights  # <-- make sure your P4 defines this!

for j in range(num_neuron_batches3):
    for ix in range(weight_batches_no3):
        base = parallel_neurons_cap3 * j

        row = w_mx3[ix]
        # grab exactly two 2-digit hex strings:
        w0, w1 = row[base: base + parallel_neurons_cap3]

        print(
            f"l2_weights.add_with_get_weights("
            f"weight_batch={ix}, neuron_batch={j}, "
            f"w0=0x{w0},w1=0x{w1},w2=0x0,w3=0x0"
            f")"
        )
        l2_weights.add_with_get_weights(
            f"{ix}",           # key “weight_batch”
            f"{j}",            # key “neuron_batch”
            f"0x{w0}",         # bit<8>  nr1_w
            f"0x{w1}",         # bit<8>  nr2_w
            f"0x0",
            f"0x0"
        )

print("→ Done loading all 8-bit weights into l2_weights (two-key table).\n")

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
