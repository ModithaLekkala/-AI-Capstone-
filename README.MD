# BINOCULAR: Dual-Plane Anomaly Detection with In-Switch Inference and Control-Plane Refinement
We propose an hybrid neural network inference architecture that co-designs the mapping of a BNN across the data plane with a full precision MLP on control plane of a programmable network device. Through a teacher-student approach, control plane resident MLP is used to guide the dynamic retraining of the BNN.

This work is in collaboration with:
- Alessio Sacco from Polytechnic of Turin, Italy
- Lorenzo Pappone and Flavio Esposito from Saint Louis University, Missouri, USA

## Dependencies
- Supported Python version: 3.10
- `pip install -r requirements.txt` to install python dependencies.
- `pip install -e .` to install project in editable mode.
- `bash init.sh` to download and prepare datasets.

## Replicate models dynamic retraining and evaluation. 
After dependecies installation.
- `python ds_retraining.py --help` to train BNNs in a distribution shift environment.
- `python ds_ablation_plot --dir results/simple_cross_dataset_eval_<arch>` to plot the corresponding ablation results.
- `python ds_plot -m netbeacon binocular_dense quark` to plot the comparison plots.

## Launch feature_collector and/or bnn_executor via multi-pipeline p4 program.
1) After cloning the repository: `cd binocular/tf_pipelines`
2) Change $SDE, $SDE_INSTALL and $REPO_PATH in tf_pipelines/workflow.sh accordingly to your system.
3) Run `sudo bash $SDE_INSTALL/bin/veth_setup.sh`, then compile and install the program on tofino SDE with `sudo bash workflow.sh`
4) Launch the tofino model into an external terminal running `bash $SDE/run_tofino_model.sh -p multipipe_inetml -f binocular/tf_pipelines/ports.json`
5) Launch switch on external terminal running `bash $SDE/run_switchd.sh -p multipipe_inetml`
6) Launch controller setup on external terminal running ``bash $SDE/run_bfshell.sh -b `pwd`/tf_pipelines/controller_retrain.py``
    - test a. single flow feature extractor + bnn executor: `sudo python tf_pipelines/client.py --pcap <pcapfile_path>`
    - test b. multiple flows bnn executor test:  `sudo python tf_pipelines/client_send_flows.py` 

## File usage
- client_send_flows.py: Simulate the tf_features_extr tofino pipeline by sending 168b long flows statistics. Dataset and selected features chosen by the file parameters.
- client.py: Used to the the feature extractor. It reads packets from a PCAP file, identifies bidirectional TCP flows, and sends them through network interfaces while listening for responses. 

## Docker image
- If **colima** is used: `colima start --arch x86_64 --cpu 4 --memory 8 --disk 100`
- Binocular is based on the **sde** image @ https://git.unistra.fr/maximefriess/p4-lab.git
- Run container with: `sudo docker run --privileged --rm -it -v $(pwd):/binocular binocular`
