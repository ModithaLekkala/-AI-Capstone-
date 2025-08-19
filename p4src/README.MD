## p4src structure
- tofino_bnn_executor: it contains the p4 program, control-plane controller and corresponding python test for the Binarized Neural Network inferece.
- tofino_flows_stats: it contains the p4 program used to gather the statistics about the packet flows that are traversing the switch.
- tofino8nrs: it contains an old version of the bnn_executor computing 8 parallel neurons results. It has a limited amount of layer though.

## Compile
To compile a p4 program use `bash compile_p4.sh <p4program.p4> tna`.


## Test the bnn_executor for Tofino ASIC
1) Run `sudo tofino_topo.py <p4program.p4>` to launch the Tofino topology.
2) To run the control plane program use `mx s1` on external terminal and then `$SDE/run_bfshell.sh -b ``pwd``/p4src/tofino_controller.py` where `$SDE` is the open-p4studio installation path
3) To run the test code from a client use `mx h1` on ext term and then `python tofino_mlp_test.py`.

## Test the feature_extractor
To run and test the feature extractor program for Tofino follow the same instructions for bnn_executor skipping the second point. It doesn't need any control plane configuration (not yet).
The main p4 program is: `feature_extractor.p4`

## Launch both feature_collector and bnn_executor via multi-pipeline p4 program. 
Run `sudo tofino_topo.py p4src/main.p4`

## Dependencies (work in progress)
- p4-utils
- open-p4studio
