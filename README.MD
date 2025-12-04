# Deploying Run-Time Adaptive Binarized Neural Network in Programmable Data Planes
We propose an hybrid neural network inference architecture that co-designs the mapping of a BNN across the data plane with a full precision MLP on control plane of a programmable network device. Through a teacher-student approach, control plane resident MLP is used to guide the dynamic retraining of the BNN.

This work is in collaboration with:
- Alessio Sacco from Polytechnic of Turin, Italy
- Lorenzo Pappone and Flavio Esposito from Saint Louis University, Missouri, USA

## Dependencies
- Supported Python versions: 3.8, 3.10
- `pip install -r requirements.txt` to install python dependencies.
- `bash init.sh` in order to download and prepare datasets.

## Replicate models dynamic retraining and evaluation. 
After dependecies installation.
- `python simple_cross_dataset_eval --help` to train BNNs in a distribution shift environment.
- `python plot_cross_dataset_eval --dir results/simple_cross_dataset_eval_<arch>` to plot the corresponding results.

## BNN and MLP training and evaluation with SHAP.
- `python shap_training_test --help` to train BNNs on a fixed dataset.

## Launch feature_collector and/or bnn_executor via multi-pipeline p4 program.
1) After cloning the repository: `cd inet-hynn/p4src`
2) Change $SDE, $SDE_INSTALL and $REPO_PATH in tf_pipelines/workflow.sh accordingly to your system.
3) Run `sudo bash $SDE_INSTALL/bin/veth_setup.sh`, then compile and install the program on tofino SDE with `sudo bash workflow.sh`
4) Launch the tofino model into an external terminal running `bash $SDE/run_tofino_model.sh -p multipipe_inetml -f inet-hynn/p4src/tf_pipelines/ports.json`
5) Launch switch on external terminal running `bash $SDE/run_switchd.sh -p multipipe_inetml`
6) Launch controller setup on external terminal ``running $SDE/run_bfshell.sh -b `pwd`/p4src/controller_adv.py``
    - test a. single flow feature extractor + bnn executor: `sudo python p4src/client.py --pcap <pcapfile_path>`
    - test b. multiple flows bnn executor test:  `sudo python p4src/client_send_flows.py` 

## File usage
- client_send_flows.py: Simulate the tf_features_extr tofino pipeline by sending 168b long flows statistics. Dataset and selected features chosen by the file parameters.
- client.py: Used to the the feature extractor. It reads packets from a PCAP file, identifies bidirectional TCP flows, and sends them through network interfaces while listening for responses. 
