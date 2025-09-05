## p4src structure
- tofino_bnn_executor: it contains the Binarized Neural Network inference program.
- tofino_flows_stats: it contains the p4 program used to gather the statistics about the packet flows that are traversing the switch.

## Compile
To compile a p4 program for tna/Tofino use `bash compile_p4.sh <p4program.p4> tna`.

## Launch feature_collector and bnn_executor via multi-pipeline p4 program. 
1) Comment `#include "../common/headers.p4"` in both feature_extractor.p4 and tofino_mlp.p4.
2) Comment Switch() declaration on feature_extractor.p4 (line 119) and tofino_mlp.p4 (line 282).
3) Run `sudo bash workflow.sh`
4) Launch the tofino model into an external terminal running `bash $SDE/run_tofino_model.sh -p multipipe_inetml -f /home/sgeraci/slu/inet-hynn/p4src/ports.json --log-dir /home/sgeraci/slu/inet-hynn/log`
5) Launch switch on external terminal running `bash $SDE/run_switchd.sh -p multipipe_inetml`
6) Launch controller setup on external terminal running `$SDE/run_bfshell.sh -b ``pwd``/p4src/controller.py`
7) Launch client on external terminal running `sudo python p4src/client.py --pcap /home/sgeraci/Desktop/datasets/UNSW-NB15/pcap/1.pcap` 

## Dependencies (work in progress)
- p4-utils
- open-p4studio
