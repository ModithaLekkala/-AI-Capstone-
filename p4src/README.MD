## Dependencies
- Download CICIDS2017 and CIC-UNSW-NB15 datasets
- Supported Python versions: 3.8, 3.10
- Tofino SDE needs to be installed.
- Run: `sudo python -m pip install --upgrade --no-cache-dir --target $SDE_INSTALL/lib/python<pyversion>/site-packages -r requirement.txt`

## Launch feature_collector and/or bnn_executor via multi-pipeline p4 program.
1) After cloning the repository: `cd inet-hynn/p4src`
2) Change $SDE, $SDE_INSTALL and $REPO_PATH in tf_pipelines/workflow.sh accordingly to your system.
3) Run `sudo bash $SDE_INSTALL/bin/veth_setup.sh`, then compile and install the program on tofino SDE with `sudo bash workflow.sh`
4) Launch the tofino model into an external terminal running `bash $SDE/run_tofino_model.sh -p multipipe_inetml -f inet-hynn/p4src/tf_pipelines/ports.json`
5) Launch switch on external terminal running `bash $SDE/run_switchd.sh -p multipipe_inetml`
6) Launch controller setup on external terminal ``running $SDE/run_bfshell.sh -b `pwd`/p4src/controller_adv.py``
    - test a. single flow feature extractor + bnn executor: `sudo python p4src/client.py --pcap <pcapfile_path>`
    - test b. multiple flows bnn executor test:  `sudo python p4src/client_send_flows.py` 

## BNN and MLP training and evaluation with SHAP.
Run `python shap_training_test.py --help`

## Launch models dynamic retraining and evaluation. 
Run `python simple_cross_dataset_eval.py`

## File usage
- client_send_flows.py: Simulate the tf_features_extr tofino pipeline by sending 168b long flows statistics. Dataset and selected features chosen by the file parameters.
- client.py: Used to the the feature extractor. It reads packets from a PCAP file, identifies bidirectional TCP flows, and sends them through network interfaces while listening for responses. 
