#!/usr/bin/env bash

# THIS SCRIPT JUST COMPILE A P4 PROGRAM

# Check that at least one argument was provided
if [ $# -lt 1 ]; then
  echo "Missing p4_file to compile."
  exit 1
fi

# If $2 is empty OR equals "tna", pick Tofino/TNA; otherwise use BMv2/v1model
if [ "$2" == "bmv2" ]; then
  echo "Target used: BMv2/v1model."
  compiler="p4c-bmv2"
  target="bmv2"
  arch="v1model"
elif [[ -z "$2" || "$2" == "tna" ]]; then
  echo "Target used: TNA/Tofino."
  compiler="bf-p4c"
  target="tofino"
  arch="tna"
fi

p4_file="$1"

echo "Start compiling of $p4_file with $compiler ($target / $arch)…"
$compiler --target "$target" --arch "$arch" --create-graphs --verbose 3 --std p4-16 -o ./build "$p4_file"
