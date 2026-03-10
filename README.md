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

1. Compile the P4 program (if `main.json` is not available):
   ```bash
   p4c-bm2-ss main.p4 -o main.json
   ```

2. Start the BMv2 switch:
   ```bash
   simple_switch --load-p4 main.json
   ```

3. Inject rules to the switch using:
   ```bash
   python trigger.py
   ```

4. Send packets for testing:
   ```bash
   python inject.py
   ```

---

### Project Highlights

- Real-time flow-based feature analysis
- Machine-learned rules deployed directly into the data plane
- Line-rate detection of malicious traffic
- Automatic mitigation based on classification outcome

---

### Conclusion

This work demonstrates that integrating machine learning decision logic directly into a P4-enabled data plane is both feasible and efficient, eliminating the bottlenecks of traditional IDS architectures.
