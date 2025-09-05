#!/usr/bin/env bash
set -euo pipefail

# Configure, build, install, and (optionally) run bf_switchd for a P4 Studio program.

PROG=""
P4_FILE=""
SDE="${SDE:-}"
SDE_INSTALL="${SDE_INSTALL:-}"
BUILD_DIR=""
P4C=""                  # defaults to $SDE_INSTALL/bin/p4c-tna
TARGET="tofino"         # or tofino2
INIT_MODE="2"           # 0=noinit, 1=warm, 2=cold
JOBS="$(nproc)"
RUN=false
ENABLE_KNET=false
EXTRA_ARGS=()

usage() {
  cat <<EOF
Usage: $(basename "$0") --program <name> --p4 <file> [options] [-- bf_switchd_args...]

Required:
  -p, --program <name>       Program name (e.g., my_prog)
  -P, --p4 <file>            Path to P4 file (e.g., ./p4src/my_prog.p4)

Common:
  -s, --sde <path>           Override \$SDE
  -i, --sde-install <path>   Override \$SDE_INSTALL
  -b, --build-dir <path>     Build dir (default: ./build/<program>)
  -c, --p4c <path>           p4c-tna path (default: \$SDE_INSTALL/bin/p4c-tna)
  -t, --target <name>        Target (default: tofino)
  -m, --init-mode <0|1|2>    bf_switchd init mode (default: 2)
  -j, --jobs <N>             Parallel build jobs (default: $(nproc))
      --enable-knet          Append --enable-knet to bf_switchd (if supported)
      --run                  Launch bf_switchd after install
  -h, --help                 Show this help

Examples:
  $(basename "$0") -p my_prog -P p4src/my_prog.p4 --run
  $(basename "$0") -p my_prog -P p4src/my_prog.p4 -b build/my_prog -i /opt/bf-sde/install -j 8 -- --ucli
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--program) PROG="${2:-}"; shift 2 ;;
    -P|--p4) P4_FILE="${2:-}"; shift 2 ;;
    -s|--sde) SDE="${2:-}"; shift 2 ;;
    -i|--sde-install) SDE_INSTALL="${2:-}"; shift 2 ;;
    -b|--build-dir) BUILD_DIR="${2:-}"; shift 2 ;;
    -c|--p4c) P4C="${2:-}"; shift 2 ;;
    -t|--target) TARGET="${2:-}"; shift 2 ;;
    -m|--init-mode) INIT_MODE="${2:-}"; shift 2 ;;
    -j|--jobs) JOBS="${2:-}"; shift 2 ;;
        --enable-knet) ENABLE_KNET=true; shift ;;
        --run) RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; EXTRA_ARGS+=("$@"); break ;;
    *) die "Unknown arg: $1" ;;
  esac
done

[[ -n "$PROG" && -n "$P4_FILE" ]] || { usage; die "Missing --program and/or --p4."; }
[[ -n "$SDE_INSTALL" ]] || die "SDE_INSTALL is not set. Use --sde-install or export it."
[[ -n "$SDE" ]] || echo "WARN: SDE not set; proceeding (usually fine)."

[[ -f "$P4_FILE" ]] || die "P4 file not found: $P4_FILE"
[[ -d "$SDE_INSTALL" ]] || die "SDE_INSTALL not a directory: $SDE_INSTALL"

P4C="${P4C:-$SDE_INSTALL/bin/p4c-tna}"
[[ -x "$P4C" ]] || die "p4c-tna not executable: $P4C"

BUILD_DIR="${BUILD_DIR:-$(pwd)/build/$PROG}"
mkdir -p "$BUILD_DIR"

echo "== Configure =="
cmake -S "${SDE}/p4studio" -B "$BUILD_DIR" \
  -DCMAKE_INSTALL_PREFIX="$SDE_INSTALL" \
  -DCMAKE_MODULE_PATH="${SDE}/cmake" \
  -DP4_NAME="$PROG" \
  -DP4_PATH="$P4_FILE" \
  -DP4C="$P4C"

echo "== Build =="
cmake --build "$BUILD_DIR" --clean-first --target "$PROG" -j"$JOBS"

echo "== Install =="
cmake --build "$BUILD_DIR" --target install

CONF="$SDE_INSTALL/share/p4/targets/$TARGET/$PROG.conf"
[[ -f "$CONF" ]] || die "switchd.conf not found at expected path: $CONF"

echo "== Installed artifacts =="
find "$SDE_INSTALL/share/tofinopd/$PROG" -maxdepth 2 -type f -name 'tofino*.bin' -o -name 'context.json' -o -name 'bf-rt.json' | sed 's/^/  /'

if $RUN; then
  echo "== Launch bf_switchd =="
  CMD=( sudo -E "$SDE_INSTALL/bin/bf_switchd"
        --install-dir "$SDE_INSTALL"
        --conf-file "$CONF"
        --init-mode "$INIT_MODE" )
  $ENABLE_KNET && CMD+=( --enable-knet )
  if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then CMD+=( "${EXTRA_ARGS[@]}" ); fi

  printf '  %q' "${CMD[@]}"; echo
  exec "${CMD[@]}"
else
  echo "Done. To run switchd:"
  echo "  sudo -E $SDE_INSTALL/bin/bf_switchd --install-dir $SDE_INSTALL --conf-file $CONF --init-mode $INIT_MODE"
  $ENABLE_KNET && echo "  (add --enable-knet if your binary supports it)"
fi
