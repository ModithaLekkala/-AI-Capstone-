# Efficient Neural Network Mapping Co-Design In Programmable Networks

We propose a hybrid neural network inference architecture that co-designs the mapping of a DNN across the data plane and control plane of a programmable network device.

This work is in collaboration with Lorenzo Pappone and Flavio Esposito from Saint Louis University.

### CHANGE LAYER DIMENSION
In order to change the number of neurons for a specific layer here the steps to follow:
- p4src/pycommon: change congruently the number of weights and the neural network description.
- p4src/tofino_mlp_prep.p4: change the preprocessor definition of HEIGTH_IX with (new_num_neurons/8), change L1_WEIGHT_TB_SIZE with the new number of weights for the new layer, add a new suitable WRITE_SIGN() macro directive at line +-180.
- p4src/tofino_mlp_test.py: if the involved layer is the output layer you may want to update the BNN_pkt field bit-width