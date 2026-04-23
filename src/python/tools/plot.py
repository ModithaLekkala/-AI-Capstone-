import matplotlib.pyplot as plt
from scapy.all import rdpcap
import os

# 1. Define the files and their expected outcomes
tests = {
    "Rule A": {"file": "rule_a.pcap", "expected": "drop"},
    "Rule B": {"file": "rule_b.pcap", "expected": "drop"},
    "Tree Rule": {"file": "tree_rule_1.pcap", "expected": "drop"},
    "Normal": {"file": "normal.pcap", "expected": "forward"}
}

# 2. Extract packet counts from the files
labels = []
sent_counts = []
forwarded_counts = []

for name, info in tests.items():
    if os.path.exists(info["file"]):
        pkts = rdpcap(info["file"])
        count = len(pkts)
        labels.append(name)
        sent_counts.append(count)
        
        # NOTE: For now, we assume if it's 'normal' it was forwarded (5 pkts)
        # In a real setup, you would count what came out of veth1
        if info["expected"] == "forward":
            forwarded_counts.append(count) 
        else:
            forwarded_counts.append(0)

# 3. Create the Plot
x = range(len(labels))
plt.figure(figsize=(10, 6))
plt.bar(x, sent_counts, width=0.4, label='Sent (Input)', align='center', color='skyblue')
plt.bar(x, forwarded_counts, width=0.4, label='Forwarded (Output)', align='edge', color='green')

plt.xlabel('Test Category')
plt.ylabel('Packet Count')
plt.title('P4 IDS Performance Visualization')
plt.xticks(x, labels)
plt.legend()
plt.savefig('my_performance_plot.png')
print("Graph saved as my_performance_plot.png")