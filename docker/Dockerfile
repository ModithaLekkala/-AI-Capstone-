# Dockerfile for P4-based IDS (BMv2 + p4c + Python tooling)
# Based on the official P4 tutorial image which has everything pre-installed.
# Build: docker build -t p4-ids .
# Run:   docker run -it --privileged --name p4-ids-dev p4-ids

FROM p4lang/p4app:latest

# ---- System dependencies ----
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    tcpdump \
    iproute2 \
    net-tools \
    iputils-ping \
    nano \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Python dependencies ----
# scapy: packet crafting (inject.py)
# If you add ML scripts later, uncomment sklearn/pandas/numpy
RUN pip3 install scapy==2.4.5

# ---- Working directory ----
WORKDIR /workspace

# Copy repo contents into the image
COPY . /workspace/

# ---- Virtual ethernet pair setup ----
# veth0/veth1 are needed for inject.py and simple_switch.
# These must be created at RUNTIME (not build time) because
# network interfaces don't persist across image layers.
# The entrypoint script handles this.
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/bin/bash"]