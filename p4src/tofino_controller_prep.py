def generate_16bit_hex():
    """
    Yields tuples of (16-bit binary string, 4-digit hex string) for all values 0–65535.
    """
    for i in range(1, (1 << 16)-1):  # 0 through 65535
        bin_str = format(i, '016b')   # 16-bit binary, zero-padded
        hex_str = format(i, '04X')    # 4-digit uppercase hex, zero-padded
        popcount = format(bin(i).count('1'), '01X')
        yield bin_str, hex_str, popcount

p4 = bfrt.tofino_mlp_prep.pipe
pop1 = p4.Ingress.pop1
pop2 = p4.Ingress.pop2
pop3 = p4.Ingress.pop3
pop4 = p4.Ingress.pop4
pop5 = p4.Ingress.pop5
pop6 = p4.Ingress.pop6
pop7 = p4.Ingress.pop7
pop8 = p4.Ingress.pop8

bnn_input_reg = p4.Ingress.bnn_input_reg

# for ix, (bstr, hstr, popcount) in enumerate(generate_16bit_hex()):
#     print(f"added: 0x{hstr}, 0x{popcount}")
#     pop1.add_with_pop_act1(f'0x{hstr}', f'0x{popcount}')
#     pop2.add_with_pop_act2(f'0x{hstr}', f'0x{popcount}')
#     pop3.add_with_pop_act3(f'0x{hstr}', f'0x{popcount}')
#     pop4.add_with_pop_act4(f'0x{hstr}', f'0x{popcount}')
#     pop5.add_with_pop_act5(f'0x{hstr}', f'0x{popcount}')
#     pop6.add_with_pop_act6(f'0x{hstr}', f'0x{popcount}')
#     pop7.add_with_pop_act7(f'0x{hstr}', f'0x{popcount}')
#     pop8.add_with_pop_act8(f'0x{hstr}', f'0x{popcount}')

for ix in range(0, 8):
    print(f"added entry: [recirc_no: {ix} | l1_weights: ['0x1345', '0x5678', '0x9ABC', '0xDEF1', '0x1245', '0x5678', '0x9ABC', '0xDEF1']")
    p4.Ingress.l1_weights.add_with_get_l1_weights(f'{ix}', '0x1345', '0x5678', '0x9ABC', '0xDEF1', '0x1245', '0x5678', '0x9ABC', '0xDEF1')
    bnn_input_reg.add(ix, f'{ix}{ix}{ix}{ix}')



    