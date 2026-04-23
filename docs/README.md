# P4-based Intrusion Detection System using Decision Tree Classifier

A real-time network intrusion detection system built with P4, enabling in-data-plane machine learning classification for high-speed networks using the CICIDS2017 dataset.

---

### Abstract

Traditional signature-based IDS struggle against modern, dynamic cyber threats. This project addresses the performance limitations of deploying ML-based detection in high-speed networks by offloading classification to a programmable data plane.

A Decision Tree model is trained on the CICIDS2017 dataset, and its logical rules are translated into P4 match-action tables, enabling line-rate classification and mitigation of malicious traffic on a bmv2 software switch.

---

### Technologies

- P4 language (`main.p4`)
- BMv2 (Behavioral Model v2)
- Python (`inject.py`, `trigger.py`)
- Decision Tree model converted into P4 rules
- Precompiled P4 JSON (`main.json`)
- Ruleset generated in JSON (`rules.json`)

---

### Project Structure

```
├── main.p4           # P4 program with flow classification logic
├── main.json         # Compiled version of the P4 program for BMv2
├── rules.json        # Match-action rules generated from Decision Tree
├── inject.py         # Script to send test packets to the switch
├── trigger.py        # Controller or rule injector (likely via P4Runtime or CLI)
└── README.md
```

---

### Getting Started

#### Prerequisites

- Python 3.x
- BMv2 + p4c compiler
- scapy (for `inject.py`)
- CICIDS2017 dataset (used for training, not included here)

#### Run the project

Step 1 — Open VS Code terminal and start the container:
powershell
docker start p4-ids-dev
docker exec -it p4-ids-dev bash

Step 2 — Inside the container, start the switch:
bash
simple_switch main.json -i 0@veth0 -i 1@veth1 &

Step 3 — Wait 2 seconds, load rules:
bash
sleep 2
python3 trigger.py

Step 4 — Open a second terminal (+ in VS Code), monitor output:
powershell
docker exec -it p4-ids-dev tcpdump -i veth1 -n -e
or
tcpdump -i veth1 -n -e

Step 5 — Back in first terminal, inject packets:
bash
python3 inject.py
 
One thing to note — if the container was stopped and restarted, the veth interfaces are lost and need to be recreated first:
bash
ip link add veth0 type veth peer name veth1
ip link set veth0 up
ip link set veth1 up

---

### Project Highlights

- Real-time flow-based feature analysis
- Machine-learned rules deployed directly into the data plane
- Line-rate detection of malicious traffic
- Automatic mitigation based on classification outcome

---

### Conclusion

This work demonstrates that integrating machine learning decision logic directly into a P4-enabled data plane is both feasible and efficient, eliminating the bottlenecks of traditional IDS architectures.
