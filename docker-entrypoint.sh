#!/bin/bash
# docker-entrypoint.sh
# Sets up virtual ethernet interfaces and optionally starts simple_switch.
# This runs every time the container starts.

set -e

echo "=== P4 IDS Environment Setup ==="

# ---- Create virtual ethernet pair (veth0 <-> veth1) ----
# veth0: inject.py sends packets INTO the switch here
# veth1: forwarded packets come OUT here (for monitoring)
if ! ip link show veth0 &>/dev/null; then
    echo "[+] Creating veth pair: veth0 <-> veth1"
    ip link add veth0 type veth peer name veth1
    ip link set veth0 up
    ip link set veth1 up
    # Disable IPv6 DAD to avoid delays
    sysctl -w net.ipv6.conf.veth0.disable_ipv6=1 &>/dev/null || true
    sysctl -w net.ipv6.conf.veth1.disable_ipv6=1 &>/dev/null || true
    echo "[+] veth0 and veth1 are up"
else
    echo "[+] veth0 already exists"
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
echo "  simple_switch main.json -i 0@veth0 -i 1@veth1 &"
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
