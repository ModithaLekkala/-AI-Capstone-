import numpy as np 
from .utils import generate_14bit, generate_16bit_hex
from .pycommon import nn

class BNNPipeline():
    def __init__(self, bnn_model, bfrt):
        self.bnn_model = bnn_model
        self.p4_bnn_exec = bfrt.multipipe_inetml.bnn_executor
        self.bfrt_pop1 = self.p4_bnn_exec.BnnIngress.pop1
        self.bfrt_pop2 = self.p4_bnn_exec.BnnIngress.pop2
        self.bfrt_pop3 = self.p4_bnn_exec.BnnIngress.pop3
        self.bfrt_pop4 = self.p4_bnn_exec.BnnIngress.pop4
        if(not self.bnn_model == 'wide'):
            self.bfrt_pop5 = self.p4_bnn_exec.BnnIngress.pop5
            self.bfrt_pop6 = self.p4_bnn_exec.BnnIngress.pop6
            self.bfrt_pop7 = self.p4_bnn_exec.BnnIngress.pop7

        self.bfrt_l0_weights = self.p4_bnn_exec.BnnIngress.l0_weights
        self.bfrt_l1_weights = self.p4_bnn_exec.BnnIngress.l1_weights
        if(self.bnn_model == 'wide'):
            self.bfrt_l2_weights = self.p4_bnn_exec.BnnIngress.l2_weights 

        self.bnn_input_reg = self.p4_bnn_exec.BnnIngress.bnn_input_reg

        self.w1 = None
        self.w2 = None
        if(self.bnn_model == 'wide'):
            self.w3 = None
        
        if(self.bnn_model == 'dense' or self.bnn_model == 'tiny'):
            self.load_pop_tb = self.load_pop_tb_7
            self.load_weights_tb = self.load_weights_tb_7
            self.load_bnn_input_reg = self.load_bnn_input_reg_7
        else:
            self.load_pop_tb = self.load_pop_tb_4
            self.load_weights_tb = self.loead_weights_tb_4
            self.load_bnn_input_reg = self.load_bnn_input_reg_4

        self.bnn_input_offset = 0
        self.inference_output={}

    def track_inference_input(self, input):    
        self.inference_output[f'{self.bnn_input_offset}'] = {
            'input': input,
            'last_layer': None,
            'result': None
        }



    def load_pop_tb_7(self):
        print('POPULATE POPS TABLES')
        for i, (_, hex_combination, popcnt) in enumerate(generate_14bit()):
            self.bfrt_pop1.add_with_pop_act1(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop2.add_with_pop_act2(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop3.add_with_pop_act3(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop4.add_with_pop_act4(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop5.add_with_pop_act5(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop6.add_with_pop_act6(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop7.add_with_pop_act7(f'0x{hex_combination}', f'0x{popcnt}')
            print(f'{i} loaded 14-bit combination', sep=' ', end='\r', flush=True)

        print("→ Done loading pop1..pop7 (all 14-bit keys → 1-hex-digit popcount).\n")
    
    def load_pop_tb_4(self):
        print('POPULATE POPS TABLES')
        for i, (_, hex_combination, popcnt) in enumerate(generate_16bit_hex()):
            self.bfrt_pop1.add_with_pop_act1(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop2.add_with_pop_act2(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop3.add_with_pop_act3(f'0x{hex_combination}', f'0x{popcnt}')
            self.bfrt_pop4.add_with_pop_act4(f'0x{hex_combination}', f'0x{popcnt}')
            print(f'{i} loaded 14-bit combination', sep=' ', end='\r', flush=True)

        print("→ Done loading pop1..pop4 (all 16-bit keys → 1-hex-digit popcount).\n")

    def load_weights_tb_7(self, l1_w, l2_w):
        l1_w = ['{:0126b}'.format(int(l1_w[i], 16)) for i in range(0, len(l1_w))]
        l2_w = ['{:042b}'.format(int(l2_w[i], 16)) for i in range(0, len(l2_w))]

        assert len(l1_w[0]) == 126
        assert len(l2_w[1]) == 42
        assert len(l1_w) == 42, 'weight l1 no. different from neurons no. they must match'
        assert len(l2_w) == 2, 'weight l2 no. different from neurons no. they must match'

        # -------------------------------------------------
        #  L0 WEIGHTS TABLE LOGIC 
        # -------------------------------------------------
        print('POPULATE L0 WEIGHTS TABLE')
        parallel_bit_cap = 14
        parallel_neurons_cap = 7

        num_neuron_batches  = nn[1] // parallel_neurons_cap
        weight_batches_no = len(l1_w[0]) // parallel_bit_cap

        assert len(l1_w) == parallel_neurons_cap * num_neuron_batches, "hex_w length must equal num_weight_batches * num_neuron_batches"

        w_mx = np.zeros((weight_batches_no, len(l1_w))).tolist()
        for ix, w in enumerate(l1_w):
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

                self.bfrt_l0_weights.add_with_get_weights(
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

        assert len(l2_w) == nn[2], 'hex_w2 length must equal number of final neurons'

        num_neuron_batches3 = nn[2] // parallel_neurons_cap3  # 2//2 == 1
        weight_batches_no3  = len(l2_w[0]) // parallel_bit_cap3
        assert len(l2_w[0]) % parallel_bit_cap3 == 0

        # build a matrix so w_mx2[batch][neuron] == that 2-digit chunk
        w_mx2 = np.zeros((weight_batches_no3, len(l2_w)), dtype=object).tolist()
        for ix, w in enumerate(l2_w):
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
                self.bfrt_l1_weights.add_with_get_bin_weights(
                    f"{ix}",           # key “weight_batch”
                    f"{j}",            # key “neuron_batch”
                    f"0b{w0}",         # bit<8>  nr1_w
                    f"0b{w1}",         # bit<8>  nr2_w
                )

        print("→ Done loading all 42-bit weights into l1_weights (two-key table).\n")

    def loead_weights_tb_4(self, l1_w, l2_w, l3_w):
        l1_w = ['{:0128b}'.format(int(l1_w[i], 16)) for i in range(0, len(l1_w))]
        l2_w = ['{:032b}'.format(int(l2_w[i], 16)) for i in range(0, len(l2_w))]
        l1_w = ['{:08b}'.format(int(l3_w[i], 16)) for i in range(0, len(l3_w))]


        print('POPULATE L0 WEIGHTS TABLE')
        parallel_bit_cap = (16//4)
        parallel_neurons_cap = 4

        assert len(l1_w) == nn[1], \
            'weight no. different from neurons no. they must match'

        num_neuron_batches  = nn[1] // parallel_neurons_cap
        weight_batches_no = len(l1_w[0]) // parallel_bit_cap

        assert len(l1_w) == parallel_neurons_cap * num_neuron_batches, \
            "hex_w length must equal num_weight_batches * num_neuron_batches"

        w_mx = np.zeros((weight_batches_no, len(l1_w))).tolist()
        for ix, w in enumerate(l1_w):
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

                self.bfrt_l0_weights.add_with_get_weights(
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
        assert len(l2_w) == nn[2], \
            'l1 weight no. different from neurons no. they must match'

        num_neuron_batches  = nn[2] // parallel_neurons_cap #2
        weight_batches_no = len(l2_w[0]) // parallel_bit_cap #8

        assert len(l2_w) == parallel_neurons_cap * num_neuron_batches, \
            "hex_w2 length must equal num_weight_batches * num_neuron_batches"

        w_mx = np.zeros((weight_batches_no, len(l2_w))).tolist()
        for ix, w in enumerate(l2_w):
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

                self.bfrt_l1_weights.add_with_get_weights(
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

        # must match nn[3] == len(l3_w)
        assert len(l3_w) == nn[3], 'l3_w length must equal number of final neurons'

        num_neuron_batches3 = nn[3] // parallel_neurons_cap3  # 2//2 == 1
        weight_batches_no3  = len(l3_w[0]) // parallel_bit_cap3
        assert len(l3_w[0]) % parallel_bit_cap3 == 0

        # build a matrix so w_mx3[batch][neuron] == that 2-digit chunk
        w_mx3 = np.zeros((weight_batches_no3, len(l3_w)), dtype=object).tolist()
        for ix, w in enumerate(l3_w):
            # split into 2-char chunks: here just one chunk per string
            chunks = [ w[i:i+parallel_bit_cap3] for i in range(0, len(w), parallel_bit_cap3) ]
            for jx, chunk in enumerate(chunks):
                w_mx3[jx][ix] = chunk

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
                self.bfrt_l2_weights.add_with_get_weights(
                    f"{ix}",           # key “weight_batch”
                    f"{j}",            # key “neuron_batch”
                    f"0x{w0}",         # bit<8>  nr1_w
                    f"0x{w1}",         # bit<8>  nr2_w
                    f"0x0",
                    f"0x0"
                )

        print("→ Done loading all 8-bit weights into l2_weights (two-key table).\n")

    def load_bnn_input_reg_7(self, bit_input):
        assert len(bit_input) == 126, "hex_input must be exactly 126 bin digits"

        old_offset = self.bnn_input_offset

        # Make sixteen 4-digit substrings:
        input_chunks = [ f'00{bit_input[i : i + 14]}' for i in range(0, 126, 14) ]
        
        for idx, piece in enumerate(input_chunks):
            print(f"bnn_input_reg.add({self.bnn_input_offset+idx}, 0b{piece})")
            self.bnn_input_reg.add(self.bnn_input_offset+idx, f"0b{piece}")
        
        self.track_inference_input(input=hex(int(bit_input, 2)))
        self.bnn_input_offset += len(input_chunks)

        print("→ Done loading the 126-bit inputs into registers.\n")
        print('→ Next input will be loaded at offset', self.bnn_input_offset)

        return old_offset

    def load_bnn_input_reg_4(self, bit_input):
        assert len(bit_input) == 128, "hex_input must be exactly 128 bin digits"
        old_offset = self.bnn_input_offset
        # Make sixteen 4-digit substrings:
        input_chunks = [ bit_input[i : i + 16] for i in range(0, 128, 16) ]

        for idx, piece in enumerate(input_chunks):
            print(f"bnn_input_reg.add({self.bnn_input_offset+idx}, 0b{piece})")
            self.bnn_input_reg.add(self.bnn_input_offset+idx, f"0b{piece}")
        self.bnn_input_offset += len(input_chunks)

        print("→ Done loading the 128-bit input into register slots 0..7.\n")
        return old_offset