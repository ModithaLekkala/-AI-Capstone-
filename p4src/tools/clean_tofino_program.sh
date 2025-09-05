#!/usr/bin/env bash
set -euo pipefail

# Deletes installed artifacts for a given P4 program from $SDE_INSTALL and
# optionally removes the CMake build directory. Can also stop running processes.

PROG=""
SDE_INSTALL="${SDE_INSTALL:-}"
BUILD_DIR=""
KILL_PROCS=false
YES=false
TARGET="tofino"   # change if you use tofino2/3 layouts

usage() {
  cat <<EOF
Usage: $(basename "$0") --program <name> [options]

Options:
  -p, --program <name>        Program name (folder under \$SDE_INSTALL/share/p4/targets/<target>/)
  -i, --sde-install <path>    Override \$SDE_INSTALL
  -b, --build-dir <path>      Also delete this build directory
  -t, --target <name>         Target folder (default: tofino)
  -k, --kill                  Kill bf_switchd and tofino-model before cleaning
  -y, --yes                   Do not prompt for confirmation
  -h, --help                  Show this help

Examples:
  $(basename "$0") -p my_prog -k
  $(basename "$0") -p my_prog -b ./build/my_prog -i /opt/bf-sde/install -k -y
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--program) PROG="${2:-}"; shift 2 ;;
    -i|--sde-install) SDE_INSTALL="${2:-}"; shift 2 ;;
    -b|--build-dir) BUILD_DIR="${2:-}"; shift 2 ;;
    -t|--target) TARGET="${2:-}"; shift 2 ;;
    -k|--kill) KILL_PROCS=true; shift ;;
    -y|--yes) YES=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown arg: $1" ;;
  esac
done

[[ -n "$PROG" ]] || { usage; die "Missing --program"; }
[[ -n "$SDE_INSTALL" ]] || die "SDE_INSTALL is not set. Use --sde-install or export SDE_INSTALL."

INSTALL_TARGET_DIR="$SDE_INSTALL/share/p4/targets/$TARGET/$PROG"
INSTALL_TPD_DIR="$SDE_INSTALL/share/tofinopd/$PROG"
INSTALL_LIBPD_DIR="$SDE_INSTALL/lib/tofinopd/$PROG"

echo "About to remove:"
echo "  $INSTALL_TARGET_DIR"
echo "  $INSTALL_TPD_DIR"
echo "  $INSTALL_LIBPD_DIR"
[[ -n "$BUILD_DIR" ]] && echo "  (build dir) $BUILD_DIR"
$KILL_PROCS && echo "  (will kill) bf_switchd, tofino-model"

if ! $YES; then
  read -r -p "Proceed? [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
fi

$KILL_PROCS && {
  pkill -f bf_switchd     2>/dev/null || true
  pkill -f tofino-model   2>/dev/null || true
}

rm -rf "$INSTALL_TARGET_DIR" "$INSTALL_TPD_DIR" "$INSTALL_LIBPD_DIR"
[[ -n "$BUILD_DIR" ]] && rm -rf "$BUILD_DIR"

echo "Done. A fresh build+install will be required."
