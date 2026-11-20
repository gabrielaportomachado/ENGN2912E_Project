#!/bin/bash
# kl.sh: run a KLayout-Python generator in batch mode with the environment the PDK pcells need.
# usage: bash AFE/layout/scripts/kl.sh <script.py> [name=value ...]     each name=value becomes a global variable (a string) of the script; kpdk.py is importable.
# FINDING (LP): the GF180MCU pcell library imports only if USER is set (libs.tech/klayout/tech/pymacros/cells/draw_efuse.py reads os.environ["USER"]); the container has no USER.
export USER="${USER:-designer}"
S="$1"; shift
[ -f "$S" ] || { echo "kl.sh: no script $S" >&2; exit 2; }
D="$(cd "$(dirname "$0")" && pwd)"
export KL_SCRIPT="$(cd "$(dirname "$S")" && pwd)/$(basename "$S")"
export KL_KIT="$D"
KL_ARGS=""; for kv in "$@"; do KL_ARGS="$KL_ARGS$kv"$'\n'; done; export KL_ARGS
exec klayout -b -r "$D/kl_launch.py" < /dev/null
