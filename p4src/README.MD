- tofino_bnn_executor: it's the folder containing the p4 program, control-plane controller and corresponding python test for the Binarized Neural Network inferece.
- tofino_flows_stats: it contains the p4 program used to gather the statistics about the packet flows that are traversing the switch.
- tofino8nrs: it contains an old version of the bnn_executor computing 8 parallel neurons results. It has a limited amount of layer though.

To compile a p4 program use `bash compile_p4.sh <p4program.p4> tna`.