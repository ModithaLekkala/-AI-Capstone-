import numpy as np 
from pycommon import hex_input, hex_w, nn

def generate_16bit_hex():
    """
    Yields (binary16, hex4, popcount_hex1) for all values 1..(2^16−2).
    """
    for i in range(1, (1 << 16) - 1):
        bin_str = format(i, '016b')    # 16-bit binary
        hex_str = format(i, '04X')     # 4-digit uppercase hex
        popcnt  = format(bin(i).count('1'), '01X')
        yield bin_str, hex_str, popcnt


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

l1_weights    = p4.Ingress.l1_weights   # SINGLE table, two-key: (weight_batch, neuron_batch)
bnn_input_reg = p4.Ingress.bnn_input_reg


# -------------------------------------------------
#  2) Populate the sixteen “popcount” tables (pop1..pop16)
#     We insert all 65 534 possible 16-bit keys → 1-hex-digit popcount
# -------------------------------------------------
for _, hex4, popcnt in generate_16bit_hex():
    pop1.add_with_pop_act1(f'0x{hex4}', f'0x{popcnt}')
    pop2.add_with_pop_act2(f'0x{hex4}', f'0x{popcnt}')
    pop3.add_with_pop_act3(f'0x{hex4}', f'0x{popcnt}')
    pop4.add_with_pop_act4(f'0x{hex4}', f'0x{popcnt}')
    pop5.add_with_pop_act5(f'0x{hex4}', f'0x{popcnt}')
    pop6.add_with_pop_act6(f'0x{hex4}', f'0x{popcnt}')
    pop7.add_with_pop_act7(f'0x{hex4}', f'0x{popcnt}')
    pop8.add_with_pop_act8(f'0x{hex4}', f'0x{popcnt}')

print("→ Done loading pop1..pop16 (all 16-bit keys → 1-hex-digit popcount).")


# -------------------------------------------------
#  3) Define your 256-bit weights as 32-hex-digit strings.
#     We must have len(hex_w) = num_weight_batches × num_neuron_batches.
#     Here, let num_neuron_batches = 2 (two “neuron batches”), so
#     each “weight batch” is a 256-bit (=32 hex chars) string.
# -------------------------------------------------
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


# -------------------------------------------------
#  4) For each “weight_batch = ix” (0..num_weight_batches−1) and
#     “neuron_batch = j” (0..1), split the 32-hex-digit string
#     into sixteen 4-hex-digit chunks and call add_with_get_l1_weights(...).
# -------------------------------------------------
for j in range(num_neuron_batches):
    for ix in range(weight_batches_no):
        base = parallel_neurons_cap * j

        w1 = w_mx[ix]

        (w0,  w1,  w2,  w3,
         w4,  w5,  w6,  w7) = w1[base: base+parallel_neurons_cap]

        print(
            f"l1_weights.add_with_get_l1_weights("
            f"weight_batch={ix}, neuron_batch={j}, "
            f"w0=0x{w0},w1=0x{w1},w2=0x{w2},w3=0x{w3},"
            f"w4=0x{w4},w5=0x{w5},w6=0x{w6},w7=0x{w7},"
            f")"
        )

        l1_weights.add_with_get_l1_weights(
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

print("→ Done loading all 128-bit weights into l1_weights (two-key table).")


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
