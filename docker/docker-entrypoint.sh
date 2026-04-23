#!/bin/bash
# docker-entrypoint.sh
# Sets up virtual ethernet interfaces and optionally starts simple_switch.
# This runs every time the container starts.

set -e

echo "=== P4 IDS Environment Setup ==="

# ---- Create virtual ethernet interfaces ----
# Instead of a veth pair, create two separate interfaces for the switch
if ! ip link show veth0 &>/dev/null; then
    echo "[+] Creating veth interfaces for switch"
    # Create two veth interfaces that will be connected to the switch
    ip link add veth0 type veth peer name switch0
    ip link add veth1 type veth peer name switch1
    # Bring them up
    ip link set veth0 up
    ip link set veth1 up
    ip link set switch0 up
    ip link set switch1 up
    echo "[+] Interfaces created: veth0 <-> switch0, veth1 <-> switch1"
else
    echo "[+] Interfaces already exist"
fi

# ---- Compile P4 if main.json is missing or stale ----
if [ ! -f /workspace/main.json ] || [ /workspace/main.p4 -nt /workspace/main.json ]; then
    echo "[+] Compiling main.p4 → main.json ..."
    cd /workspace
    p4c-bm2-ss --arch v1model -o main.json main.p4
    echo "[+] Compilation successful"
else
    echo "[+] main.json is up to date, skipping compilation"
fi

echo ""
echo "=== Ready! Useful commands ==="
echo ""
echo "  # Start the switch (in background):"
echo "  simple_switch main.json -i 0@switch0 -i 1@switch1 &"
echo ""
echo "  # Load IDS rules:"
echo "  python3 trigger.py"
echo ""
echo "  # Inject test packets:"
echo "  python3 inject.py"
echo ""
echo "  # Watch what arrives on veth1 (forwarded packets):"
echo "  tcpdump -i veth1 -n &"
echo ""

# Execute whatever CMD was passed (default: /bin/bash)
exec "$@"
