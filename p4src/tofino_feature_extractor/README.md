Flow statistics supported by the features pipeline:
- sbytes
- dbytes
- sttl
- dttl
- spkts
- dpkts
- smeansz
- dmeansz
- synack
- ackdat

Work in progress:
- stime
- ltime
- sintpkt
- dintpkt

## Test the feature_extractor
To run and test the feature extractor program for Tofino follow the same instructions for bnn_executor: control plane program `controller.py`, test program `client.py`.
The main p4 program is: `feature_extractor.p4`