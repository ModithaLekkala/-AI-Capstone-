## p4src folders structure
- tf_bnn_exec_\<arch\>_\<neurons no.\>nr:    it contains the p4 implementation of BNN executor for architecture *arch* and *neurons no.*  parallel neurons execution for packet processing.
- tf_feature_extr:  it contains the p4 program used to gather the statistics about the flows that are traversing the switch.

## Launch feature_collector and bnn_executor via multi-pipeline p4 program. 
1) After cloning the repository: `cd inet-hynn/p4src` 
2) Change $SDE, $SDE_INSTALL and $REPO_PATH in workflow.sh accordingly to your system.
3) Compile and install the program on tofino SDE with `sudo bash workflow.sh`
4) Launch the tofino model into an external terminal running `bash $SDE/run_tofino_model.sh -p multipipe_inetml -f inet-hynn/p4src/ports.json`
5) Launch switch on external terminal running `bash $SDE/run_switchd.sh -p multipipe_inetml`
6) Launch controller setup on external terminal running `$SDE/run_bfshell.sh -b ``pwd``/p4src/controller.py`
7) Launch client on external terminal running `sudo python p4src/client.py --pcap <pcapfile_path>` 

### Dependencies
Supported Python versions [3.8, 3.10]
run: `sudo python -m pip install --upgrade --no-cache-dir --target $SDE_INSTALL/lib/python<pyversion>/site-packages -r requirement.txt`