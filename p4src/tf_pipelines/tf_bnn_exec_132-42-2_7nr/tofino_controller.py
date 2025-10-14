import numpy as np 
from pycommon import hex_inputs, hex_w, nn, hex_w2

def generate_14bit():
    """
    Yields (binary14, hex4, popcount_int) for all 14-bit values 0..(2^14-1).
    """
    for i in range(1 << 14):                            # 0..16383
        bin_str = format(i, '014b')                     # 14-bit binary with leading zeros
        hex_str = format(i, '04X')                      # 4-digit uppercase hex (up to 3FFF)
        popcnt  = format(bin(i).count('1'), '01X')      # integer popcount
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
p4 = bfrt.multipipe_inetml.bnn_executor
pop1          = p4.BnnIngress.pop1
pop2          = p4.BnnIngress.pop2
pop3          = p4.BnnIngress.pop3
pop4          = p4.BnnIngress.pop4
pop5          = p4.BnnIngress.pop5
pop6          = p4.BnnIngress.pop6
pop7          = p4.BnnIngress.pop7

l0_weights    = p4.BnnIngress.l0_weights   # SINGLE table, two-key: (weight_batch, neuron_batch)
l1_weights    = p4.BnnIngress.l1_weights   

bnn_input_reg = p4.BnnIngress.bnn_input_reg

eb            = p4.BnnIngress.egress_behaviour



# -------------------------------------------------
#  2) Populate the sixteen “popcount” tables (pop1..pop16)
#     We insert all 65 534 possible 16-bit keys → 1-hex-digit popcount
# -------------------------------------------------
print('POPULATE POPS TABLES')
for i, (_, hex_combination, popcnt) in enumerate(generate_14bit()):
    pop1.add_with_pop_act1(f'0x{hex_combination}', f'0x{popcnt}')
    pop2.add_with_pop_act2(f'0x{hex_combination}', f'0x{popcnt}')
    pop3.add_with_pop_act3(f'0x{hex_combination}', f'0x{popcnt}')
    pop4.add_with_pop_act4(f'0x{hex_combination}', f'0x{popcnt}')
    pop5.add_with_pop_act5(f'0x{hex_combination}', f'0x{popcnt}')
    pop6.add_with_pop_act6(f'0x{hex_combination}', f'0x{popcnt}')
    pop7.add_with_pop_act7(f'0x{hex_combination}', f'0x{popcnt}')
    print(f'{i} loaded 14-bit combination', sep=' ', end='\r', flush=True)

print("→ Done loading pop1..pop7 (all 14-bit keys → 1-hex-digit popcount).\n")

# -------------------------------------------------
#  2) binarized weights and input
# -------------------------------------------------
hex_w = ['{:0126b}'.format(int(hex_w[i], 16)) for i in range(0, len(hex_w))]
hex_w2 = ['{:042b}'.format(int(hex_w2[i], 16)) for i in range(0, len(hex_w2))]
hex_input = '{:0126b}'.format(int(hex_input, 16))

# -------------------------------------------------
#  L0 WEIGHTS TABLE LOGIC 
# -------------------------------------------------
print('POPULATE L0 WEIGHTS TABLE')
parallel_bit_cap = 14
parallel_neurons_cap = 7

assert len(hex_w) == nn[1], 'weight no. different from neurons no. they must match'

num_neuron_batches  = nn[1] // parallel_neurons_cap
weight_batches_no = len(hex_w[0]) // parallel_bit_cap

assert len(hex_w) == parallel_neurons_cap * num_neuron_batches, "hex_w length must equal num_weight_batches * num_neuron_batches"

w_mx = np.zeros((weight_batches_no, len(hex_w))).tolist()
print(f'mx shape {len(w_mx)}' )
for ix, w in enumerate(hex_w):
    chunks = [w[i:i+parallel_bit_cap] for i in range(0, len(w), 14)]
    for jx, chunk in enumerate(chunks):
        w_mx[jx][ix] = chunk

# push weight into weight table l0
for j in range(num_neuron_batches):
    for ix in range(weight_batches_no):
        base = parallel_neurons_cap * j

        w1 = w_mx[ix]

        (w0,  w1,  w2,  w3, w4, w5, w6) = w1[base: base+parallel_neurons_cap]

        print(
            f"l0_weights.add_with_get_weights("
            f"weight_batch={ix}, neuron_batch={j}, "
            f"w0=0b{w0},w1=0b{w1},w2=0b{w2},w3=0b{w3},"
            f"w4=0b{w4},w5=0b{w5},w6=0b{w6}"
            f")"
        )

        l0_weights.add_with_get_weights(
            f"{ix}",           # key “weight_batch”
            f"{j}",            # key “neuron_batch”
            f"0b{w0}",         # bit<16> nr1_w
            f"0b{w1}",         # bit<16> nr2_w
            f"0b{w2}",         # bit<16> nr3_w
            f"0b{w3}",         # bit<16> nr4_w
            f"0b{w4}",         # bit<16> nr5_w
            f"0b{w5}",         # bit<16> nr6_w
            f"0b{w6}"         # bit<16> nr7_w
        )

print("→ Done loading all 126-bit weights into l0_weights (two-key table).\n")

# -------------------------------------------------
#  L1 (FINAL) WEIGHTS TABLE LOGIC 
# -------------------------------------------------
print('POPULATE L1 WEIGHTS TABLE')
# this layer has 2 neurons → we batch 2 at a time
parallel_neurons_cap3 = 2      # two output neurons
parallel_bit_cap3     = 14      # each weight is 2 hex digits (8 bits)

assert len(hex_w2) == nn[2], 'hex_w2 length must equal number of final neurons'

num_neuron_batches3 = nn[2] // parallel_neurons_cap3  # 2//2 == 1
weight_batches_no3  = len(hex_w2[0]) // parallel_bit_cap3
assert len(hex_w2[0]) % parallel_bit_cap3 == 0

# build a matrix so w_mx2[batch][neuron] == that 2-digit chunk
w_mx2 = np.zeros((weight_batches_no3, len(hex_w2)), dtype=object).tolist()
for ix, w in enumerate(hex_w2):
    # split into 2-char chunks: here just one chunk per string
    chunks = [ w[i:i+parallel_bit_cap3] for i in range(0, len(w), parallel_bit_cap3) ]
    for jx, chunk in enumerate(chunks):
        w_mx2[jx][ix] = chunk


for j in range(num_neuron_batches3):
    for ix in range(weight_batches_no3):
        base = parallel_neurons_cap3 * j

        row = w_mx2[ix]
        w0, w1 = row[base: base + parallel_neurons_cap3]

        print(
            f"l1_weights.add_with_get_bin_weights("
            f"weight_batch={ix}, neuron_batch={j}, "
            f"w0=0b{w0},w1=0b{w1}"
            f")"
        )
        l1_weights.add_with_get_bin_weights(
            f"{ix}",           # key “weight_batch”
            f"{j}",            # key “neuron_batch”
            f"0b{w0}",         # bit<8>  nr1_w
            f"0b{w1}",         # bit<8>  nr2_w
        )

print("→ Done loading all 42-bit weights into l1_weights (two-key table).\n")

# -------------------------------------------------
#  5) Finally, split a single 256-bit “hex_input” into sixteen 16-bit chunks
#     and write them into bnn_input_reg[0..15].
# -------------------------------------------------
assert len(hex_input) == 133, "hex_input must be exactly 126 bin digits"
ix=0
for hex_input in hex_inputs:
    # Make sixteen 4-digit substrings:
    input_chunks = [ f'00{hex_input[i : i + 14]}' for i in range(0, 126, 14) ]

    for piece in input_chunks:
        print(f"bnn_input_reg.add({idx}, 0b{piece})")
        bnn_input_reg.add(ix, f"0b{piece}")
        ix+1
        
    idx+=7

print("→ Done loading the 126-bit inputs into registers.")
